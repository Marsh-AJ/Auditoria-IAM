"""Configuración global de pruebas y gestión del ciclo de vida de PySide6 / Qt."""

from typing import Generator
import pytest
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp() -> Generator[QApplication, None, None]:
    """Garantiza una única instancia de QApplication para toda la sesión de pruebas."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Limpieza final de la sesión para evitar colisiones nativas durante el desmontaje
    for widget in app.topLevelWidgets():
        try:
            widget.close()
            widget.deleteLater()
        except Exception:
            pass
    try:
        app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def clean_qt_widgets(qapp: QApplication) -> Generator[None, None, None]:
    """Fixture de limpieza automática por prueba.

    Registra los widgets de nivel superior existentes antes del test,
    y al finalizar cierra y programa deleteLater() únicamente para
    los widgets nuevos creados durante la prueba.
    """
    existing_widgets = set(qapp.topLevelWidgets())
    yield
    current_widgets = qapp.topLevelWidgets()
    new_widgets = [w for w in current_widgets if w not in existing_widgets]
    for widget in new_widgets:
        try:
            widget.close()
            widget.deleteLater()
        except Exception:
            pass
    try:
        qapp.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()
    except Exception:
        pass

