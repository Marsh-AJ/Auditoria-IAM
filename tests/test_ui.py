"""
Pruebas unitarias para la interfaz de escritorio PySide6 del Sistema de Auditoría IAM.
Verifica creación de ventana, presencia de las 5 secciones, navegación dinámica,
selector de fuentes y desacoplamiento absoluto del motor y bases de datos.
"""
import os
import sys
from unittest.mock import patch

import pytest

# Asegurar modo offscreen para ejecución sin pantalla física en entornos automatizados
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from src.auditoria_iam.ui import MainWindow
from src.auditoria_iam.ui.pages import (
    AuditPage,
    HistoryPage,
    HomePage,
    ResultsPage,
    SettingsPage,
)


@pytest.fixture(scope="session")
def qapp():
    """Garantiza una única instancia de QApplication para todas las pruebas de UI."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(qapp):
    """Crea y entrega una instancia limpia de MainWindow para cada prueba."""
    window = MainWindow()
    return window


def test_ui_modules_import():
    """1. Verifica la correcta importación de los módulos de interfaz."""
    import src.auditoria_iam.ui as ui_pkg
    import src.auditoria_iam.ui.main_window as mw_mod
    import src.auditoria_iam.ui.pages as pages_pkg
    import src.auditoria_iam.ui.styles as styles_mod

    assert hasattr(ui_pkg, "MainWindow")
    assert hasattr(mw_mod, "MainWindow")
    assert hasattr(pages_pkg, "HomePage")
    assert hasattr(pages_pkg, "AuditPage")
    assert hasattr(pages_pkg, "ResultsPage")
    assert hasattr(pages_pkg, "HistoryPage")
    assert hasattr(pages_pkg, "SettingsPage")
    assert hasattr(styles_mod, "CYBER_SECURITY_STYLE")


def test_main_window_creation(main_window):
    """2. Verifica la inicialización de la ventana principal y sus propiedades base."""
    assert main_window.windowTitle() == "Sistema de Auditoría IAM"
    # Comprobar dimensiones mínimas y actuales
    min_size = main_window.minimumSize()
    assert min_size.width() >= 960
    assert min_size.height() >= 600
    assert main_window.width() >= 960
    assert main_window.height() >= 600


def test_five_sections_exist_in_stack(main_window):
    """3. Verifica la existencia de las 5 páginas requeridas en el contenedor central dinámico."""
    stack = main_window.stacked_widget
    assert stack.count() == 5

    assert isinstance(stack.widget(0), HomePage)
    assert isinstance(stack.widget(1), AuditPage)
    assert isinstance(stack.widget(2), ResultsPage)
    assert isinstance(stack.widget(3), HistoryPage)
    assert isinstance(stack.widget(4), SettingsPage)


def test_navigation_between_screens(main_window):
    """4. Verifica que cada botón del menú lateral cambie realmente la pantalla activa."""
    stack = main_window.stacked_widget

    # Navegar a Inicio (0)
    main_window._on_navigate(0)
    assert stack.currentIndex() == 0
    assert stack.currentWidget() == main_window.home_page
    assert main_window.nav_buttons[0].isChecked()

    # Navegar a Ejecutar auditoría (1)
    main_window._on_navigate(1)
    assert stack.currentIndex() == 1
    assert stack.currentWidget() == main_window.audit_page
    assert main_window.nav_buttons[1].isChecked()

    # Navegar a Resultados (2)
    main_window._on_navigate(2)
    assert stack.currentIndex() == 2
    assert stack.currentWidget() == main_window.results_page
    assert main_window.nav_buttons[2].isChecked()

    # Navegar a Historial (3)
    main_window._on_navigate(3)
    assert stack.currentIndex() == 3
    assert stack.currentWidget() == main_window.history_page
    assert main_window.nav_buttons[3].isChecked()

    # Navegar a Configuración (4)
    main_window._on_navigate(4)
    assert stack.currentIndex() == 4
    assert stack.currentWidget() == main_window.settings_page
    assert main_window.nav_buttons[4].isChecked()


def test_audit_page_source_selector(main_window):
    """5. Verifica la presencia del selector de fuente (Simulador y AWS IAM) en la pantalla de auditoría."""
    audit_page = main_window.audit_page
    combo = audit_page.source_selector

    assert combo is not None
    assert combo.count() == 2

    items = [combo.itemText(i) for i in range(combo.count())]
    assert any("simulador" in item.lower() for item in items)
    assert any("aws" in item.lower() for item in items)


def test_audit_page_execute_button_does_not_invoke_engine(main_window):
    """6. Verifica que el botón de ejecución no invoque todavía el motor ni realice consultas."""
    audit_page = main_window.audit_page
    btn = audit_page.execute_button
    assert btn is not None

    # Simular clic en el botón con patch al AuditEngine para asegurar desacoplamiento
    with patch("src.auditoria_iam.audit.engine.AuditEngine.evaluate_all") as mock_eval:
        btn.click()
        # Verificar que el motor NO fue invocado
        mock_eval.assert_not_called()

    # Verificar que se muestre un mensaje informativo claro en la interfaz
    status_text = audit_page.status_message.text()
    assert "Fase 5 - Entrega 2" in status_text or "habilitada" in status_text
    assert "No se han efectuado consultas" in status_text or "desacoplados" in status_text


def test_results_page_structure(main_window):
    """7. Verifica la estructura visual preparada para resultados con las 5 columnas requeridas."""
    results_page = main_window.results_page
    table = results_page.results_table

    assert table.columnCount() == 5
    headers = [table.horizontalHeaderItem(i).text() for i in range(5)]
    assert "Recurso Auditado" in headers
    assert "Regla Evaluada" in headers
    assert "Control ISO" in headers
    assert "Estado" in headers
    assert "Descripción del Resultado" in headers
    assert table.rowCount() == 0  # Sin resultados precargados falsos


def test_history_page_structure(main_window):
    """8. Verifica que la pantalla de historial muestre el estado de entrega posterior sin conectar BD."""
    history_page = main_window.history_page
    table = history_page.history_table

    assert table.columnCount() == 5
    assert table.rowCount() == 0


def test_settings_page_sections_and_no_credentials(main_window):
    """9. Verifica que la pantalla de configuración presente las secciones visuales sin credenciales."""
    settings_page = main_window.settings_page
    assert settings_page is not None

    # Asegurar que no se exponen contraseñas ni campos de claves secretas
    labels = settings_page.findChildren(object, name="")
    all_text = " ".join([str(getattr(obj, "text", lambda: "")()) for obj in labels])
    assert "password" not in all_text.lower() or "contraseñas" in all_text.lower()
    assert "secret_key" not in all_text.lower()
    assert "aws_session_token" not in all_text.lower()

