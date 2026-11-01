"""
Paquete de páginas y vistas para la interfaz de usuario PySide6.
"""
from src.auditoria_iam.ui.pages.audit_page import AuditPage
from src.auditoria_iam.ui.pages.history_page import HistoryPage
from src.auditoria_iam.ui.pages.home_page import HomePage
from src.auditoria_iam.ui.pages.results_page import ResultsPage
from src.auditoria_iam.ui.pages.settings_page import SettingsPage

__all__ = [
    "HomePage",
    "AuditPage",
    "ResultsPage",
    "HistoryPage",
    "SettingsPage",
]

