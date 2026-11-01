"""
Página de Historial de Auditorías para el Sistema de Auditoría IAM.
Estructurada para consultar y filtrar ejecuciones previas y registros de auditoría.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHeaderView,
    QLabel,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)


class HistoryPage(QWidget):
    """Pantalla para la consulta del histórico de ejecuciones y trazabilidad."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("history_page")
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # 1. Encabezado de la página
        title = QLabel("Historial de Auditorías")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")

        subtitle = QLabel(
            "Registro cronológico de evaluaciones técnicas ejecutadas y evolución del cumplimiento."
        )
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # 2. Banner de estado de la consulta histórica
        banner = QFrame()
        banner.setStyleSheet(
            "background-color: #1e293b; border-left: 4px solid #38bdf8; border-radius: 6px; padding: 14px;"
        )
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(12, 10, 12, 10)

        banner_text = QLabel(
            "ℹ La consulta histórica se habilitará en una entrega posterior tras la integración con el esquema relacional de persistencia.\n"
            "En esta entrega estructural no se realizan conexiones ni lecturas activas contra la base de datos MySQL."
        )
        banner_text.setWordWrap(True)
        banner_text.setStyleSheet("color: #e2e8f0; font-size: 13px; line-height: 1.4;")
        banner_layout.addWidget(banner_text)
        layout.addWidget(banner)

        # 3. Estructura de tabla preparada para el histórico
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "ID Ejecución",
            "Fecha y Hora",
            "Fuente Utilizada",
            "Total Evaluaciones",
            "Hallazgos Detectados"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.history_table.setRowCount(0)
        self.history_table.setStyleSheet(
            "background-color: #0f172a; border: 1px solid #334155; border-radius: 6px; gridline-color: #1e293b; color: #f8fafc;"
        )

        layout.addWidget(self.history_table)

