"""
Ventana Principal de la Aplicación de Escritorio del Sistema de Auditoría IAM.
Implementa navegación lateral persistente, área central dinámica (QStackedWidget)
y diseño ergonómico de ciberseguridad.
"""
from typing import Dict

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.auditoria_iam.ui.pages import (
    AuditPage,
    HistoryPage,
    HomePage,
    ResultsPage,
    SettingsPage,
)
from src.auditoria_iam.ui.styles import CYBER_SECURITY_STYLE


class MainWindow(QMainWindow):
    """Ventana principal del sistema con menú de navegación lateral y vistas desacopladas."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sistema de Auditoría IAM")
        self.resize(1200, 750)
        self.setMinimumSize(960, 600)
        self.setStyleSheet(CYBER_SECURITY_STYLE)

        self._init_ui()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Menú lateral (Sidebar)
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # 2. Área central dinámica (QStackedWidget)
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setObjectName("central_stack")

        # Instanciar las 5 páginas
        self.home_page = HomePage(self)
        self.audit_page = AuditPage(self)
        self.results_page = ResultsPage(self)
        self.history_page = HistoryPage(self)
        self.settings_page = SettingsPage(self)

        # Añadir al stack
        self.stacked_widget.addWidget(self.home_page)      # Índice 0
        self.stacked_widget.addWidget(self.audit_page)     # Índice 1
        self.stacked_widget.addWidget(self.results_page)   # Índice 2
        self.stacked_widget.addWidget(self.history_page)   # Índice 3
        self.stacked_widget.addWidget(self.settings_page)  # Índice 4

        # Conectar señales de integración entre páginas
        self.audit_page.audit_completed.connect(self._on_audit_completed)
        self.audit_page.navigate_requested.connect(self._on_navigate)

        main_layout.addWidget(self.stacked_widget, stretch=1)

        # Seleccionar página inicial (Inicio)
        self.nav_buttons[0].setChecked(True)
        self.stacked_widget.setCurrentIndex(0)

    def _create_sidebar(self) -> QFrame:
        """Construye el panel lateral de navegación con branding y botones activos."""
        sidebar = QFrame(self)
        sidebar.setObjectName("sidebar")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(8)

        # Encabezado institucional del menú
        brand_container = QVBoxLayout()
        brand_container.setSpacing(2)

        title_label = QLabel("AUDITORÍA IAM")
        title_label.setObjectName("brand_title")

        subtitle_label = QLabel("UPHARVEN C.A. • ISO 27001")
        subtitle_label.setObjectName("brand_subtitle")

        brand_container.addWidget(title_label)
        brand_container.addWidget(subtitle_label)
        layout.addLayout(brand_container)
        layout.addSpacing(16)

        # Grupo exclusivo de botones de navegación
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.nav_buttons: Dict[int, QPushButton] = {}

        nav_items = [
            (0, "Inicio"),
            (1, "Ejecutar auditoría"),
            (2, "Resultados"),
            (3, "Historial"),
            (4, "Configuración"),
        ]

        for index, label_text in nav_items:
            btn = QPushButton(f"  {label_text}")
            btn.setProperty("class", "nav_button")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=index: self._on_navigate(idx))

            self.button_group.addButton(btn, index)
            self.nav_buttons[index] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Pie del menú lateral
        footer_label = QLabel("v1.0.0 • Prototipo Académico")
        footer_label.setStyleSheet("color: #475569; font-size: 11px;")
        layout.addWidget(footer_label)

        return sidebar

    def _on_navigate(self, index: int) -> None:
        """Cambia activamente la pantalla central visible según el índice seleccionado."""
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
            if index in self.nav_buttons and not self.nav_buttons[index].isChecked():
                self.nav_buttons[index].setChecked(True)

    def _on_audit_completed(self, results, resources, summary) -> None:
        """Transfiere los resultados reales de la auditoría a la vista de resultados."""
        self.results_page.load_results(results=results, resources=resources, summary=summary)


