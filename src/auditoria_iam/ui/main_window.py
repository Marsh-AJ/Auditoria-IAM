"""
Ventana Principal de la Aplicación de Escritorio del Sistema de Auditoría IAM.
Implementa navegación lateral serena estilo consola ejecutiva, barra superior de
contexto (breadcrumbs) y área central dinámica (QStackedWidget).
"""
from typing import Dict

from PySide6.QtCore import QSize, Qt
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

from src.auditoria_iam.application.audit_service import AuditService
from src.auditoria_iam.ui.icons import create_icon_badge, render_svg_icon
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

    SECTION_BREADCRUMBS: Dict[int, str] = {
        0: "Resumen de Seguridad",
        1: "Ejecutar Auditoría",
        2: "Resultados de Evaluación",
        3: "Historial de Ejecuciones",
        4: "Configuración del Sistema",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sistema de Auditoría IAM")
        self.resize(1280, 800)
        self.setMinimumSize(960, 600)
        self.setStyleSheet(CYBER_SECURITY_STYLE)

        self._init_ui()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Menú lateral (Calm Sidebar)
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # 2. Columna derecha: Barra superior de contexto + Área central dinámica
        workspace_col = QWidget(self)
        workspace_layout = QVBoxLayout(workspace_col)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        top_bar = self._create_top_bar()
        workspace_layout.addWidget(top_bar)

        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setObjectName("central_stack")

        # Servicio compartido de orquestación y auditoría
        self.audit_service = AuditService()

        # Instanciar las vistas
        self.home_page = HomePage(self, audit_service=self.audit_service)
        self.audit_page = AuditPage(self, audit_service=self.audit_service)
        self.results_page = ResultsPage(self, audit_service=self.audit_service)
        self.history_page = HistoryPage(self, audit_service=self.audit_service)
        self.settings_page = SettingsPage(self)

        self.stacked_widget.addWidget(self.home_page)      # Índice 0
        self.stacked_widget.addWidget(self.audit_page)     # Índice 1
        self.stacked_widget.addWidget(self.results_page)   # Índice 2
        self.stacked_widget.addWidget(self.history_page)   # Índice 3
        self.stacked_widget.addWidget(self.settings_page)  # Índice 4

        # Conectar señales de integración entre páginas
        self.home_page.run_selected.connect(self._on_historical_run_selected)
        self.home_page.navigate_requested.connect(self._on_navigate)
        self.audit_page.audit_completed.connect(self._on_audit_completed)
        self.audit_page.navigate_requested.connect(self._on_navigate)
        self.history_page.run_selected.connect(self._on_historical_run_selected)

        workspace_layout.addWidget(self.stacked_widget, stretch=1)
        main_layout.addWidget(workspace_col, stretch=1)

        # Seleccionar página inicial (Inicio)
        self.nav_buttons[0].setChecked(True)
        self.stacked_widget.setCurrentIndex(0)

    def _create_top_bar(self) -> QFrame:
        """Construye la barra superior minimalista con ruta de navegación (breadcrumb) e indicadores."""
        bar = QFrame(self)
        bar.setObjectName("top_header_bar")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(8)

        lbl_root = QLabel("Auditoría IAM")
        lbl_root.setStyleSheet("color: #94A3B8; font-size: 12.5px; font-weight: 500;")

        lbl_sep = QLabel("/")
        lbl_sep.setStyleSheet("color: #CBD5E1; font-size: 12.5px;")

        self.lbl_breadcrumb_active = QLabel(self.SECTION_BREADCRUMBS[0])
        self.lbl_breadcrumb_active.setStyleSheet("color: #0F172A; font-size: 12.5px; font-weight: 600;")

        layout.addWidget(lbl_root)
        layout.addWidget(lbl_sep)
        layout.addWidget(self.lbl_breadcrumb_active)
        layout.addStretch()

        # Insignias discretas de contexto normativo y modo operativo
        iso_chip = QLabel("ISO/IEC 27001:2022")
        iso_chip.setStyleSheet(
            "background-color: #F8FAFC; color: #475569; border: 1px solid #E2E8F0; "
            "border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: 600;"
        )

        ro_chip = QLabel("●  Modo solo lectura")
        ro_chip.setStyleSheet(
            "background-color: #ECFDF5; color: #16845B; border: 1px solid #BBF7D0; "
            "border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: 600;"
        )

        layout.addWidget(iso_chip)
        layout.addWidget(ro_chip)
        return bar

    def _create_sidebar(self) -> QFrame:
        """Construye el panel lateral sereno con logotipo, módulos principales y pie institucional."""
        sidebar = QFrame(self)
        sidebar.setObjectName("sidebar")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 20, 14, 18)
        layout.setSpacing(6)

        # 1. Identidad institucional superior
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(4, 0, 4, 0)
        brand_row.setSpacing(11)

        brand_icon = create_icon_badge(
            "brand_shield",
            fg_color="#60A5FA",
            bg_color="#1A2C47",
            border_color="#2A4365",
            box_size=36,
            icon_size=18,
            radius=9,
            parent=sidebar,
        )

        brand_text_col = QVBoxLayout()
        brand_text_col.setSpacing(1)

        title_label = QLabel("Auditoría IAM")
        title_label.setObjectName("brand_title")

        subtitle_label = QLabel("UPHARVEN · CLOUD SEC")
        subtitle_label.setObjectName("brand_subtitle")

        brand_text_col.addWidget(title_label)
        brand_text_col.addWidget(subtitle_label)

        brand_row.addWidget(brand_icon)
        brand_row.addLayout(brand_text_col, stretch=1)
        layout.addLayout(brand_row)

        layout.addSpacing(10)
        divider_top = QFrame(sidebar)
        divider_top.setFixedHeight(1)
        divider_top.setStyleSheet("background-color: #1D2E46; border: none;")
        layout.addWidget(divider_top)
        layout.addSpacing(6)

        # 2. Etiqueta de sección
        sec_label = QLabel("MENÚ PRINCIPAL")
        sec_label.setObjectName("sidebar_section_label")
        layout.addWidget(sec_label)

        # 3. Grupo de navegación (Configuración oculto visualmente para esta entrega pero disponible funcionalmente)
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.nav_buttons: Dict[int, QPushButton] = {}

        nav_items = [
            (0, "Dashboard", "dashboard", True),
            (1, "Ejecutar auditoría", "play_bolt", True),
            (2, "Resultados", "clipboard", True),
            (3, "Historial", "history", True),
            (4, "Configuración", "settings", False),
        ]

        for index, label_text, icon_name, is_visible in nav_items:
            btn = QPushButton(f"  {label_text}")
            btn.setProperty("class", "nav_button")
            btn.setIcon(
                render_svg_icon(
                    icon_name,
                    color="#94A3B8",
                    active_color="#60A5FA",
                    size=17,
                )
            )
            btn.setIconSize(QSize(17, 17))
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setVisible(is_visible)
            btn.clicked.connect(lambda checked, idx=index: self._on_navigate(idx))

            self.button_group.addButton(btn, index)
            self.nav_buttons[index] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # 4. Pie institucional estilo tarjeta de organización
        divider_bottom = QFrame(sidebar)
        divider_bottom.setFixedHeight(1)
        divider_bottom.setStyleSheet("background-color: #1D2E46; border: none;")
        layout.addWidget(divider_bottom)
        layout.addSpacing(8)

        org_row = QHBoxLayout()
        org_row.setContentsMargins(4, 2, 4, 2)
        org_row.setSpacing(10)

        avatar = QLabel("UP")
        avatar.setFixedSize(QSize(32, 32))
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            "background-color: #1C314E; color: #7CC4FA; border: 1px solid #2A4365; "
            "border-radius: 8px; font-size: 11px; font-weight: 700;"
        )

        org_text_col = QVBoxLayout()
        org_text_col.setSpacing(1)

        org_name = QLabel("UPHARVEN C.A.")
        org_name.setStyleSheet("color: #E2E8F0; font-size: 12px; font-weight: 600;")

        org_ver = QLabel("Prototipo v1.0 · ISO 27001")
        org_ver.setStyleSheet("color: #64748B; font-size: 10.5px; font-weight: 500;")

        org_text_col.addWidget(org_name)
        org_text_col.addWidget(org_ver)

        org_row.addWidget(avatar)
        org_row.addLayout(org_text_col, stretch=1)
        layout.addLayout(org_row)

        return sidebar

    def _on_navigate(self, index: int) -> None:
        """Cambia activamente la pantalla central visible según el índice seleccionado."""
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
            if index in self.nav_buttons and not self.nav_buttons[index].isChecked():
                self.nav_buttons[index].setChecked(True)
            if index in self.SECTION_BREADCRUMBS:
                self.lbl_breadcrumb_active.setText(self.SECTION_BREADCRUMBS[index])
            # Si se navega a Inicio/Dashboard, refrescar métricas
            if index == 0:
                self.home_page.refresh_dashboard()
            # Si se navega a Historial, refrescar la lista de auditorías guardadas
            elif index == 3:
                self.history_page.refresh_history()

    def _on_audit_completed(self, results, resources, summary) -> None:
        """Transfiere los resultados reales de la auditoría a la vista de resultados y refresca dashboard."""
        self.results_page.load_results(results=results, resources=resources, summary=summary)
        self.home_page.refresh_dashboard()

    def _on_historical_run_selected(self, run_id: int) -> None:
        """Recupera los resultados de una auditoría guardada en MySQL y los muestra en ResultsPage."""
        try:
            results, resources, summary = self.audit_service.get_historical_run_results(run_id)
            self.results_page.load_results(results=results, resources=resources, summary=summary, run_id=run_id)
            self._on_navigate(2)
        except Exception as exc:
            error_msg = (
                f"No fue posible recuperar los resultados de la auditoría #{run_id} desde MySQL "
                f"({type(exc).__name__}). Verifique la conexión con la base de datos."
            )
            self.last_historical_error = error_msg
            self.history_page.show_error_message(error_msg)
