"""
Página de Resultados para el Sistema de Auditoría IAM.
Estructurada para presentar el detalle de evaluaciones por recurso, control ISO y estado.
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


class ResultsPage(QWidget):
    """Pantalla para la visualización de resultados técnicos de auditoría."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("results_page")
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # 1. Encabezado de la página
        title = QLabel("Resultados de Auditoría")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")

        subtitle = QLabel(
            "Visualización detallada de la evaluación de controles ISO/IEC 27001:2022 y hallazgos técnicos."
        )
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # 2. Banner informativo de resultados no cargados
        info_banner = QFrame()
        info_banner.setStyleSheet(
            "background-color: #1e293b; border-left: 4px solid #f59e0b; border-radius: 6px; padding: 14px;"
        )
        banner_layout = QVBoxLayout(info_banner)
        banner_layout.setContentsMargins(12, 10, 12, 10)

        banner_text = QLabel(
            "ℹ Todavía no existen resultados cargados en esta pantalla.\n"
            "Los resultados de evaluación se poblarán automáticamente una vez ejecutada una auditoría "
            "tras la integración funcional programada en la siguiente entrega."
        )
        banner_text.setWordWrap(True)
        banner_text.setStyleSheet("color: #e2e8f0; font-size: 13px; line-height: 1.4;")
        banner_layout.addWidget(banner_text)
        layout.addWidget(info_banner)

        # 3. Estructura de tabla preparada con las columnas requeridas
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Recurso Auditado",
            "Regla Evaluada",
            "Control ISO",
            "Estado",
            "Descripción del Resultado"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.results_table.setRowCount(0)
        self.results_table.setStyleSheet(
            "background-color: #0f172a; border: 1px solid #334155; border-radius: 6px; gridline-color: #1e293b; color: #f8fafc;"
        )

        layout.addWidget(self.results_table)

