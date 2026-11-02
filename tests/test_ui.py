"""
Pruebas unitarias para la interfaz de escritorio PySide6 del Sistema de Auditoría IAM.
Verifica creación de ventana, presencia de las 5 secciones, navegación dinámica,
selector de fuentes, ejecución real del motor con datos simulados, presentación de resultados
en tabla y contadores, manejo defensivo de errores y ausencia total de llamadas a AWS y MySQL.
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Asegurar modo offscreen para ejecución sin pantalla física en entornos automatizados
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from src.auditoria_iam.application.audit_service import AuditService
from src.auditoria_iam.ui import MainWindow
from src.auditoria_iam.ui.pages import (
    AuditPage,
    HistoryPage,
    HomePage,
    ResultsPage,
    SettingsPage,
)


@pytest.fixture
def main_window(qapp):
    """Crea y entrega una instancia limpia de MainWindow para cada prueba con teardown explícito."""
    window = MainWindow()
    yield window
    try:
        window.close()
        window.deleteLater()
    except Exception:
        pass


def test_ui_modules_import():
    """1. Verifica la correcta importación de los módulos de interfaz y aplicación."""
    import src.auditoria_iam.application.audit_service as service_mod
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
    assert hasattr(service_mod, "AuditService")


def test_main_window_creation(main_window):
    """2. Verifica la inicialización de la ventana principal y sus dimensiones mínimas."""
    assert main_window.windowTitle() == "Sistema de Auditoría IAM"
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
    """5. Verifica la presencia del selector de fuentes (Simulador y AWS IAM)."""
    audit_page = main_window.audit_page
    combo = audit_page.source_selector

    assert combo is not None
    assert combo.count() == 2

    items = [combo.itemText(i) for i in range(combo.count())]
    assert any("simulador" in item.lower() for item in items)
    assert any("aws" in item.lower() for item in items)


def test_audit_page_aws_allows_execution(main_window):
    """6. Verifica que AWS IAM permita seleccionar y ejecutar auditorías en esta entrega."""
    audit_page = main_window.audit_page
    combo = audit_page.source_selector

    # Seleccionar AWS IAM
    for i in range(combo.count()):
        if combo.itemData(i) == "aws":
            combo.setCurrentIndex(i)
            break

    # El botón debe estar habilitado para AWS IAM
    assert audit_page.execute_button.isEnabled()
    assert "boto3" in audit_page.status_message.text().lower() or "aws" in audit_page.status_message.text().lower()

    # Asegurar que al hacer clic se ejecuta el flujo de AWS
    with patch.object(audit_page._audit_service, "run_aws_audit") as mock_aws_audit:
        mock_aws_audit.return_value = (
            [],
            [],
            {"total": 0, "conforme": 0, "hallazgo": 0, "no_evaluable": 0},
            {"persisted": False, "run_id": None, "message": ""},
        )
        audit_page._on_execute_clicked()
        mock_aws_audit.assert_called_once()


def test_results_page_structure(main_window):
    """7. Verifica la estructura visual preparada para resultados con las columnas y contadores."""
    results_page = main_window.results_page
    table = results_page.results_table

    assert table.columnCount() == 6
    headers = [table.horizontalHeaderItem(i).text() for i in range(6)]
    assert "Recurso Auditado" in headers
    assert "Tipo de Recurso" in headers
    assert "Regla Evaluada" in headers
    assert "Control ISO" in headers
    assert "Estado" in headers
    assert "Descripción del Resultado" in headers
    assert table.rowCount() == 0  # Inicialmente vacío


def test_history_page_structure(main_window):
    """8. Verifica que la pantalla de historial muestre la estructura de columnas requerida."""
    history_page = main_window.history_page
    table = history_page.history_table

    assert table.columnCount() == 6
    headers = [table.horizontalHeaderItem(i).text() for i in range(6)]
    assert "ID Ejecución" in headers
    assert "Fecha y Hora" in headers
    assert "Fuente Utilizada" in headers
    assert "Estado" in headers
    assert "Hallazgos Detectados" in headers
    assert "Resumen de Ejecución" in headers
    assert table.rowCount() == 0


def test_settings_page_sections_and_no_credentials(main_window):
    """9. Verifica que la pantalla de configuración presente las secciones visuales sin exponer credenciales."""
    settings_page = main_window.settings_page
    assert settings_page is not None

    labels = settings_page.findChildren(object, name="")
    all_text = " ".join([str(getattr(obj, "text", lambda: "")()) for obj in labels])
    assert "password" not in all_text.lower() or "contraseñas" in all_text.lower()
    assert "secret_key" not in all_text.lower()
    assert "aws_session_token" not in all_text.lower()


def test_audit_execution_invokes_engine_and_processes_all_four_rules(main_window):
    """10. Verifica que el botón de ejecución invoque el motor real y evalúe las cuatro reglas IAM."""
    audit_page = main_window.audit_page
    results_page = main_window.results_page

    # Seleccionar simulador
    audit_page.source_selector.setCurrentIndex(0)
    assert audit_page.source_selector.currentData() == "simulador"
    assert audit_page.execute_button.isEnabled()

    # Ejecutar auditoría real
    audit_page.execute_button.click()

    # Verificar que el mensaje informa terminación correcta
    status_text = audit_page.status_message.text()
    assert "Auditoría finalizada correctamente" in status_text
    assert "Total de evaluaciones: 67" in status_text

    # Verificar que la tabla de resultados se pobló con los 67 resultados
    table = results_page.results_table
    assert table.rowCount() == 67

    # Verificar que las 4 reglas (IAM-001, IAM-002, IAM-003, IAM-004) fueron procesadas
    rules_in_table = set()
    for row in range(table.rowCount()):
        rules_in_table.add(table.item(row, 2).text())

    assert "IAM-001" in rules_in_table
    assert "IAM-002" in rules_in_table
    assert "IAM-003" in rules_in_table
    assert "IAM-004" in rules_in_table


def test_results_page_counters_and_statuses_match_engine_output(main_window):
    """11. Verifica que los contadores numéricos y los 3 estados (Conforme, Hallazgo, No evaluable) coincidan."""
    audit_page = main_window.audit_page
    results_page = main_window.results_page

    audit_page.source_selector.setCurrentIndex(0)
    audit_page.execute_button.click()

    # Verificar contadores métricos de resumen
    assert results_page.lbl_total.text() == "67"
    assert results_page.lbl_conforme.text() == "36"
    assert results_page.lbl_hallazgo.text() == "6"
    assert results_page.lbl_no_evaluable.text() == "25"

    # Verificar que los tres estados figuran en la tabla
    table = results_page.results_table
    statuses_in_table = set()
    for row in range(table.rowCount()):
        statuses_in_table.add(table.item(row, 4).text())

    assert "Conforme" in statuses_in_table
    assert "Hallazgo" in statuses_in_table
    assert "No evaluable" in statuses_in_table


def test_error_handling_does_not_crash_application(main_window):
    """12. Verifica que los errores imprevistos se capturen y muestren sin cerrar la aplicación."""
    audit_page = main_window.audit_page

    # Mockear el servicio para simular un fallo inesperado
    with patch.object(audit_page._audit_service, "run_simulated_audit", side_effect=RuntimeError("Fallo simulado")):
        audit_page.execute_button.click()

        # Comprobar que se presentó un mensaje de error legible
        assert "❌ Error durante la ejecución de la auditoría" in audit_page.status_message.text()
        assert "RuntimeError" in audit_page.status_message.text()

        # Comprobar que el botón se volvió a habilitar
        assert audit_page.execute_button.isEnabled()


def test_multiple_audits_execution_updates_cleanly(main_window):
    """13. Verifica que sea posible ejecutar una segunda auditoría actualizando los datos limpiamente."""
    audit_page = main_window.audit_page
    results_page = main_window.results_page

    # Primera ejecución
    audit_page.execute_button.click()
    assert results_page.results_table.rowCount() == 67

    # Segunda ejecución consecutiva
    audit_page.execute_button.click()
    # No deben duplicarse las filas (debe permanecer en 67)
    assert results_page.results_table.rowCount() == 67
    assert results_page.lbl_total.text() == "67"


def test_audit_execution_saves_to_mysql_and_updates_ui(main_window):
    """14. Verifica que la ejecución de auditoría invoque la persistencia y reporte el ID guardado."""
    audit_page = main_window.audit_page

    with patch("src.auditoria_iam.application.audit_service.save_audit_run", return_value=42) as mock_save:
        audit_page.execute_button.click()
        mock_save.assert_called_once()
        status_text = audit_page.status_message.text()
        assert "Ejecución ID #42" in status_text or "ID #42" in status_text


def test_persistence_failure_retains_results_in_memory_and_warns(main_window):
    """15. Verifica que si MySQL falla, la auditoría conserve los resultados en memoria y emita un aviso."""
    audit_page = main_window.audit_page
    results_page = main_window.results_page

    with patch("src.auditoria_iam.application.audit_service.save_audit_run", side_effect=RuntimeError("DB caída")):
        audit_page.execute_button.click()

        # Comprobar que los resultados en memoria se conservan en la interfaz
        assert results_page.results_table.rowCount() == 67
        # Comprobar que se presentó el mensaje de advertencia sobre MySQL
        status_text = audit_page.status_message.text()
        assert "Aviso de persistencia" in status_text
        assert "memoria" in status_text


def test_history_page_loads_and_displays_runs_from_mysql(main_window):
    """16. Verifica que la pantalla de historial cargue y muestre ejecuciones recuperadas de MySQL."""
    history_page = main_window.history_page

    mock_runs = [
        {
            "id": 1,
            "execution_date": "2026-11-01 10:00:00",
            "source_type": "simulacion",
            "status": "completada",
            "total_findings": 6,
            "summary": "Total: 67 | Conforme: 36 | Hallazgo: 6 | No evaluable: 25",
        },
        {
            "id": 2,
            "execution_date": "2026-11-01 11:30:00",
            "source_type": "simulacion",
            "status": "completada",
            "total_findings": 3,
            "summary": "Total: 67 | Conforme: 40 | Hallazgo: 3 | No evaluable: 24",
        },
    ]

    with patch.object(history_page._audit_service, "get_audit_history", return_value=mock_runs):
        history_page.refresh_history()

        table = history_page.history_table
        assert table.rowCount() == 2
        assert table.item(0, 0).text() == "#1"
        assert table.item(1, 0).text() == "#2"
        assert "Se encontraron 2 ejecuciones" in history_page.banner_text.text()


def test_history_page_select_run_loads_historical_results_in_results_page(main_window):
    """17. Verifica que al seleccionar una auditoría del historial, se consulten sus resultados en ResultsPage."""
    history_page = main_window.history_page
    results_page = main_window.results_page

    mock_runs = [
        {"id": 99, "execution_date": "2026-11-01 12:00:00", "source_type": "simulacion", "status": "completada", "total_findings": 1, "summary": "Test run"},
    ]

    from src.auditoria_iam.audit.models import AuditResult
    mock_results = [
        AuditResult("IAM-001", "C15-01", 1, "Conforme", "Histórico Conforme 1"),
        AuditResult("IAM-003", "C18-01", 2, "Hallazgo", "Histórico Hallazgo 1"),
    ]
    mock_resources = [{"id": 1, "resource_key": "user.test1"}, {"id": 2, "resource_key": "user.test2"}]
    mock_summary = {"total": 2, "conforme": 1, "hallazgo": 1, "no_evaluable": 0}

    with patch.object(history_page._audit_service, "get_audit_history", return_value=mock_runs), \
         patch.object(main_window.audit_page._audit_service, "get_historical_run_results", return_value=(mock_results, mock_resources, mock_summary)):

        history_page.refresh_history()
        history_page.history_table.selectRow(0)
        assert history_page.btn_view_results.isEnabled()

        # Pulsar ver resultados
        history_page.btn_view_results.click()

        # Debe haber navegado a ResultsPage (índice 2)
        assert main_window.stacked_widget.currentIndex() == 2
        assert results_page.results_table.rowCount() == 2
        assert results_page.lbl_total.text() == "2"
        assert results_page.lbl_hallazgo.text() == "1"
        assert "ejecución #99" in results_page.banner_text.text()


def test_history_page_error_retrieving_historical_run_communicated_through_ui(main_window):
    """18. Verifica que si falla la consulta de resultados históricos, se comunique en la UI sin cerrar la aplicación."""
    history_page = main_window.history_page

    mock_runs = [
        {"id": 404, "execution_date": "2026-11-01 12:00:00", "source_type": "simulacion", "status": "completada", "total_findings": 1, "summary": "Test run"},
    ]

    with patch.object(history_page._audit_service, "get_audit_history", return_value=mock_runs), \
         patch.object(main_window.audit_page._audit_service, "get_historical_run_results", side_effect=RuntimeError("Error de lectura en MySQL")):

        history_page.refresh_history()
        history_page.history_table.selectRow(0)
        assert history_page.btn_view_results.isEnabled()

        # Pulsar ver resultados (producirá error controlado)
        history_page.btn_view_results.click()

        # Comprobar que no se produjo crash y que el error quedó registrado
        assert hasattr(main_window, "last_historical_error")
        assert "No fue posible recuperar los resultados de la auditoría #404" in main_window.last_historical_error
        assert "RuntimeError" in main_window.last_historical_error

        # Comprobar que el banner de HistoryPage muestra el mensaje visible
        assert "No fue posible recuperar los resultados de la auditoría #404" in history_page.banner_text.text()


