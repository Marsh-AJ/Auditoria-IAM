"""
Página Principal / Dashboard de Auditoría IAM para la aplicación de escritorio.
Integra métricas ejecutivas estilo consola SaaS moderna, distribución gráfica de
resultados, barras de cumplimiento por regla técnica, resumen de última ejecución y
catálogo interactivo de controles ISO/IEC 27001:2022.
"""
from typing import Any, Dict, Optional

from PySide6.QtCharts import QChart, QChartView, QPieSeries
from PySide6.QtCore import QMargins, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.auditoria_iam.application.audit_service import AuditService
from src.auditoria_iam.ui.controls_catalog import EXTERNAL_ISO_URL
from src.auditoria_iam.ui.dialogs.control_detail_dialog import IsoControlDetailDialog
from src.auditoria_iam.ui.icons import create_icon_badge, render_svg_icon


class HomePage(QWidget):
    """Vista principal / Dashboard interactivo del sistema de auditoría IAM."""

    # Señal emitida para solicitar ver los resultados de una ejecución específica (run_id)
    run_selected = Signal(int)
    # Señal emitida para solicitar navegación hacia otra pestaña por índice (ej. Historial = 3)
    navigate_requested = Signal(int)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("home_page")
        self._audit_service = audit_service or AuditService()
        self.current_run_id: Optional[int] = None
        self.last_error: Optional[str] = None

        self._init_ui()
        self.refresh_dashboard()

    def _init_ui(self) -> None:
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        content_widget.setObjectName("home_canvas")
        content_widget.setStyleSheet("QWidget#home_canvas { background-color: #F5F7FA; }")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(28, 24, 28, 32)
        layout.setSpacing(18)

        # =====================================================================
        # 1. ENCABEZADO EJECUTIVO Y ACCIONES RÁPIDAS
        # =====================================================================
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)

        title = QLabel("Resumen de Seguridad IAM")
        title.setProperty("class", "page_title")

        subtitle = QLabel(
            "Estado de cumplimiento técnico, distribución de hallazgos y controles ISO/IEC 27001:2022 · UPHARVEN C.A."
        )
        subtitle.setProperty("class", "page_subtitle")
        subtitle.setWordWrap(True)

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_layout.addLayout(title_col, stretch=1)

        buttons_header_layout = QHBoxLayout()
        buttons_header_layout.setSpacing(10)

        self.btn_refresh = QPushButton("  Actualizar")
        self.btn_refresh.setProperty("class", "secondary_button")
        self.btn_refresh.setIcon(render_svg_icon("refresh", color="#334155", size=15))
        self.btn_refresh.setIconSize(QSize(15, 15))
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_dashboard)
        buttons_header_layout.addWidget(self.btn_refresh)

        self.btn_new_audit = QPushButton("  Nueva auditoría")
        self.btn_new_audit.setProperty("class", "primary_button")
        self.btn_new_audit.setIcon(render_svg_icon("plus", color="#FFFFFF", size=15, stroke_width=2.2))
        self.btn_new_audit.setIconSize(QSize(15, 15))
        self.btn_new_audit.setCursor(Qt.PointingHandCursor)
        self.btn_new_audit.clicked.connect(lambda: self.navigate_requested.emit(1))
        buttons_header_layout.addWidget(self.btn_new_audit)

        header_layout.addLayout(buttons_header_layout)
        layout.addLayout(header_layout)

        # Franja discreta de estado operativo
        self.banner = QFrame()
        self.banner.setObjectName("home_status_banner")
        self._set_banner_style("#294F78")
        banner_layout = QHBoxLayout(self.banner)
        banner_layout.setContentsMargins(16, 10, 16, 10)

        self.banner_text = QLabel(
            "Consultando estado del sistema y registros de auditoría en MySQL..."
        )
        self.banner_text.setWordWrap(True)
        self.banner_text.setStyleSheet("color: #334155; font-size: 12.5px; font-weight: 500;")
        banner_layout.addWidget(self.banner_text)
        layout.addWidget(self.banner)

        # =====================================================================
        # 2. TARJETAS EJECUTIVAS DE INDICADORES (KPI CARDS)
        # =====================================================================
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        (
            self.card_total,
            self.lbl_kpi_total,
            self.pill_kpi_total,
        ) = self._create_kpi_card(
            title="TOTAL EVALUACIONES",
            value="—",
            pill_text="Base 100%",
            pill_fg="#294F78",
            pill_bg="#EEF4FF",
            pill_border="#DBEAFE",
            icon_name="layers",
            icon_fg="#294F78",
            icon_bg="#EEF4FF",
            icon_border="#DBEAFE",
            footer_text="Criterios técnicos inspeccionados",
            tooltip="Total de verificaciones ejecutadas en la última auditoría",
        )

        (
            self.card_conforme,
            self.lbl_kpi_conforme,
            self.pill_kpi_conforme,
        ) = self._create_kpi_card(
            title="CONFORMES",
            value="—",
            pill_text="✓ 0.0%",
            pill_fg="#16845B",
            pill_bg="#ECFDF5",
            pill_border="#A7F3D0",
            icon_name="shield_check",
            icon_fg="#16845B",
            icon_bg="#ECFDF5",
            icon_border="#D1FAE5",
            footer_text="Cumplen parámetros ISO 27001",
            tooltip="Evaluaciones que satisfacen los criterios de seguridad",
        )

        (
            self.card_hallazgo,
            self.lbl_kpi_hallazgo,
            self.pill_kpi_hallazgo,
        ) = self._create_kpi_card(
            title="HALLAZGOS DETECTADOS",
            value="—",
            pill_text="! 0.0%",
            pill_fg="#D64545",
            pill_bg="#FEF2F2",
            pill_border="#FECACA",
            icon_name="alert_triangle",
            icon_fg="#D64545",
            icon_bg="#FEF2F2",
            icon_border="#FEE2E2",
            footer_text="Desviaciones técnicas activas",
            tooltip="Anomalías o riesgos detectados que requieren revisión",
        )

        (
            self.card_no_evaluable,
            self.lbl_kpi_no_evaluable,
            self.pill_kpi_no_eval,
        ) = self._create_kpi_card(
            title="NO EVALUABLES",
            value="—",
            pill_text="• 0.0%",
            pill_fg="#B45309",
            pill_bg="#FFFBEB",
            pill_border="#FDE68A",
            icon_name="info_circle",
            icon_fg="#B45309",
            icon_bg="#FFFBEB",
            icon_border="#FEF3C7",
            footer_text="Metadatos no aplicables o ausentes",
            tooltip="Recursos sin atributos suficientes para el criterio específico",
        )

        kpi_layout.addWidget(self.card_total, stretch=1)
        kpi_layout.addWidget(self.card_conforme, stretch=1)
        kpi_layout.addWidget(self.card_hallazgo, stretch=1)
        kpi_layout.addWidget(self.card_no_evaluable, stretch=1)
        layout.addLayout(kpi_layout)

        # =====================================================================
        # 3. FILA ANALÍTICA: DISTRIBUCIÓN GRÁFICA + CUMPLIMIENTO POR REGLA
        # =====================================================================
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        # --- Panel izquierdo: Distribución de Resultados (Donut) ---
        chart_card = QFrame()
        chart_card.setProperty("class", "card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(20, 18, 20, 18)
        chart_layout.setSpacing(12)

        chart_top_row = QHBoxLayout()
        chart_header = QLabel("Distribución de Resultados")
        chart_header.setProperty("class", "card_header_title")
        chart_top_row.addWidget(chart_header)
        chart_top_row.addStretch()

        # Leyenda minimalista en cabecera (estilo Meridian ERP)
        for dot_col, dot_lbl in (
            ("#16845B", "Conforme"),
            ("#D64545", "Hallazgo"),
            ("#D49A32", "No eval."),
        ):
            leg = QLabel(f'<span style="color:{dot_col}; font-size:13px;">●</span> {dot_lbl}')
            leg.setStyleSheet("color: #64748B; font-size: 11.5px; font-weight: 500; margin-left: 6px;")
            chart_top_row.addWidget(leg)

        chart_layout.addLayout(chart_top_row)
        chart_layout.addWidget(self._create_hairline())

        self.lbl_chart_empty = QLabel(
            "Sin registros de auditoría disponibles.\nInicie una evaluación para visualizar la distribución."
        )
        self.lbl_chart_empty.setAlignment(Qt.AlignCenter)
        self.lbl_chart_empty.setStyleSheet("color: #94A3B8; font-size: 12.5px; padding: 48px 16px;")
        chart_layout.addWidget(self.lbl_chart_empty, stretch=1)

        self.chart = QChart()
        self.chart.setBackgroundVisible(False)
        self.chart.layout().setContentsMargins(0, 0, 0, 0)
        self.chart.setMargins(QMargins(0, 0, 0, 0))
        self.chart.legend().setVisible(False)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing, True)
        self.chart_view.setMinimumHeight(215)
        self.chart_view.setMaximumHeight(235)
        self.chart_view.setStyleSheet("background: transparent; border: none;")
        self.chart_view.setVisible(False)
        chart_layout.addWidget(self.chart_view, stretch=1)

        self.dist_breakdown_layout = QHBoxLayout()
        self.dist_breakdown_layout.setSpacing(8)

        self.badge_dist_conforme = self._create_distribution_badge("Conforme", "—", "#16845B")
        self.badge_dist_hallazgo = self._create_distribution_badge("Hallazgo", "—", "#D64545")
        self.badge_dist_no_eval = self._create_distribution_badge("No evaluable", "—", "#D49A32")

        self.dist_breakdown_layout.addWidget(self.badge_dist_conforme)
        self.dist_breakdown_layout.addWidget(self.badge_dist_hallazgo)
        self.dist_breakdown_layout.addWidget(self.badge_dist_no_eval)
        chart_layout.addLayout(self.dist_breakdown_layout)

        charts_row.addWidget(chart_card, stretch=11)

        # --- Panel derecho: Cumplimiento por Regla IAM (Barras estilo Meridian Utilization) ---
        rules_card = QFrame()
        rules_card.setProperty("class", "card")
        rules_layout = QVBoxLayout(rules_card)
        rules_layout.setContentsMargins(20, 18, 20, 18)
        rules_layout.setSpacing(12)

        rules_top_row = QHBoxLayout()
        rules_header = QLabel("Cumplimiento por Regla IAM")
        rules_header.setProperty("class", "card_header_title")
        rules_top_row.addWidget(rules_header)
        rules_top_row.addStretch()

        rules_tag = QLabel("4 controles activos")
        rules_tag.setStyleSheet("color: #94A3B8; font-size: 11.5px; font-weight: 600;")
        rules_top_row.addWidget(rules_tag)
        rules_layout.addLayout(rules_top_row)
        rules_layout.addWidget(self._create_hairline())

        self.rule_widgets: Dict[str, Dict[str, Any]] = {}
        rules_meta = [
            ("IAM-001", "Control 5.15 — Control de acceso"),
            ("IAM-002", "Control 5.16 — Gestión de identidades"),
            ("IAM-003", "Control 5.18 — Derechos de acceso"),
            ("IAM-004", "Control 8.5 — Autenticación segura"),
        ]

        for idx_r, (r_code, r_title) in enumerate(rules_meta):
            r_container = QWidget()
            rb_col = QVBoxLayout(r_container)
            rb_col.setContentsMargins(2, 2, 2, 2)
            rb_col.setSpacing(6)

            # Línea superior: Nombre de la regla + píldoras + porcentaje
            top_line = QHBoxLayout()
            top_line.setSpacing(6)

            lbl_code_name = QLabel(f'<b style="color:#0F172A;">{r_code}</b>  <span style="color:#64748B;">·  {r_title}</span>')
            lbl_code_name.setStyleSheet("font-size: 12.5px;")
            top_line.addWidget(lbl_code_name, stretch=1)

            lbl_c = QLabel("Conf: 0")
            lbl_c.setStyleSheet(
                "background-color: #ECFDF5; color: #16845B; border: 1px solid #D1FAE5; "
                "border-radius: 5px; padding: 2px 7px; font-weight: 700; font-size: 10.5px;"
            )
            lbl_h = QLabel("Hall: 0")
            lbl_h.setStyleSheet(
                "background-color: #FEF2F2; color: #D64545; border: 1px solid #FEE2E2; "
                "border-radius: 5px; padding: 2px 7px; font-weight: 700; font-size: 10.5px;"
            )
            lbl_ne = QLabel("NoEv: 0")
            lbl_ne.setStyleSheet(
                "background-color: #FFFBEB; color: #B45309; border: 1px solid #FEF3C7; "
                "border-radius: 5px; padding: 2px 7px; font-weight: 700; font-size: 10.5px;"
            )
            lbl_pct = QLabel("0%")
            lbl_pct.setFixedWidth(38)
            lbl_pct.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl_pct.setStyleSheet("color: #475569; font-size: 12px; font-weight: 700;")

            top_line.addWidget(lbl_c)
            top_line.addWidget(lbl_h)
            top_line.addWidget(lbl_ne)
            top_line.addWidget(lbl_pct)
            rb_col.addLayout(top_line)

            # Barra de progreso sutil estilo utilización
            prog = QProgressBar()
            prog.setRange(0, 100)
            prog.setValue(0)
            prog.setTextVisible(False)
            prog.setFixedHeight(6)
            rb_col.addWidget(prog)

            self.rule_widgets[r_code] = {
                "conforme": lbl_c,
                "hallazgo": lbl_h,
                "no_evaluable": lbl_ne,
                "pct_label": lbl_pct,
                "progress": prog,
            }
            rules_layout.addWidget(r_container)
            if idx_r < len(rules_meta) - 1:
                rules_layout.addSpacing(2)

        rules_layout.addStretch()
        charts_row.addWidget(rules_card, stretch=13)
        layout.addLayout(charts_row)

        # =====================================================================
        # 4. RESUMEN DE LA ÚLTIMA AUDITORÍA (ESTILO TABLA EJECUTIVA COMPACTA)
        # =====================================================================
        self.last_run_card = QFrame()
        self.last_run_card.setProperty("class", "card")
        last_run_layout = QVBoxLayout(self.last_run_card)
        last_run_layout.setContentsMargins(0, 16, 0, 16)
        last_run_layout.setSpacing(12)

        lr_header_layout = QHBoxLayout()
        lr_header_layout.setContentsMargins(20, 0, 20, 0)
        lr_header_layout.setSpacing(10)

        lr_title = QLabel("Última Auditoría Registrada")
        lr_title.setProperty("class", "card_header_title")
        lr_header_layout.addWidget(lr_title)
        lr_header_layout.addStretch()

        self.btn_view_history = QPushButton("Ver historial")
        self.btn_view_history.setProperty("class", "secondary_button")
        self.btn_view_history.setCursor(Qt.PointingHandCursor)
        self.btn_view_history.clicked.connect(self._on_view_history_clicked)
        lr_header_layout.addWidget(self.btn_view_history)

        self.btn_view_results = QPushButton("Ver resultados detallados  →")
        self.btn_view_results.setProperty("class", "primary_button")
        self.btn_view_results.setEnabled(False)
        self.btn_view_results.setCursor(Qt.PointingHandCursor)
        self.btn_view_results.clicked.connect(self._on_view_results_clicked)
        lr_header_layout.addWidget(self.btn_view_results)

        last_run_layout.addLayout(lr_header_layout)

        # Franja de encabezados tipo fila de tabla SaaS
        col_header_strip = QFrame()
        col_header_strip.setObjectName("lr_header_strip")
        col_header_strip.setStyleSheet(
            "QFrame#lr_header_strip { background-color: #F8FAFC; border-top: 1px solid #EDF2F7; border-bottom: 1px solid #EDF2F7; }"
        )
        ch_grid = QGridLayout(col_header_strip)
        ch_grid.setContentsMargins(20, 8, 20, 8)
        ch_grid.setHorizontalSpacing(24)

        headers_meta = [
            "EJECUCIÓN",
            "FECHA Y HORA",
            "FUENTE DE DATOS",
            "ESTADO",
            "HALLAZGOS DETECTADOS",
        ]
        for col_i, h_txt in enumerate(headers_meta):
            h_lbl = QLabel(h_txt)
            h_lbl.setStyleSheet(
                "color: #64748B; font-size: 10.5px; font-weight: 700; letter-spacing: 0.6px;"
            )
            ch_grid.addWidget(h_lbl, 0, col_i)
            ch_grid.setColumnStretch(col_i, 1)

        last_run_layout.addWidget(col_header_strip)

        # Fila de valores de la última auditoría
        vals_row_widget = QWidget()
        lr_grid = QGridLayout(vals_row_widget)
        lr_grid.setContentsMargins(20, 4, 20, 2)
        lr_grid.setHorizontalSpacing(24)

        self.lbl_run_id = QLabel("—")
        self.lbl_run_id.setStyleSheet("color: #0F172A; font-weight: 700; font-size: 13.5px; font-family: 'Consolas', monospace;")

        self.lbl_run_date = QLabel("—")
        self.lbl_run_date.setStyleSheet("color: #334155; font-size: 13px; font-weight: 500;")

        self.lbl_run_source = QLabel("—")
        self.lbl_run_source.setStyleSheet("color: #0F172A; font-size: 13px; font-weight: 600;")

        self.lbl_run_status = QLabel("—")
        self.lbl_run_status.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")

        self.lbl_run_findings = QLabel("—")
        self.lbl_run_findings.setStyleSheet("color: #0F172A; font-weight: 700; font-size: 13.5px;")

        lr_grid.addWidget(self.lbl_run_id, 0, 0)
        lr_grid.addWidget(self.lbl_run_date, 0, 1)
        lr_grid.addWidget(self.lbl_run_source, 0, 2)
        lr_grid.addWidget(self.lbl_run_status, 0, 3, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        lr_grid.addWidget(self.lbl_run_findings, 0, 4)
        for col_i in range(5):
            lr_grid.setColumnStretch(col_i, 1)

        last_run_layout.addWidget(vals_row_widget)
        layout.addWidget(self.last_run_card)

        # =====================================================================
        # 5. CATÁLOGO INTERACTIVO DE CONTROLES ISO/IEC 27001:2022
        # =====================================================================
        controls_header_row = QHBoxLayout()
        controls_header_row.setSpacing(16)

        controls_text_col = QVBoxLayout()
        controls_text_col.setSpacing(2)

        controls_title = QLabel("Catálogo de Controles ISO/IEC 27001:2022")
        controls_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")

        controls_subtitle = QLabel(
            "Explore el objetivo de seguridad, criterios algorítmicos y delimitaciones técnicas de los cuatro controles evaluados."
        )
        controls_subtitle.setStyleSheet("font-size: 12.5px; color: #64748B;")

        controls_text_col.addWidget(controls_title)
        controls_text_col.addWidget(controls_subtitle)
        controls_header_row.addLayout(controls_text_col, stretch=1)

        self.btn_open_iso_doc = QPushButton("  Norma ISO/IEC 27001:2022  ↗")
        self.btn_open_iso_doc.setProperty("class", "secondary_button")
        self.btn_open_iso_doc.setIcon(render_svg_icon("external_link", color="#334155", size=14))
        self.btn_open_iso_doc.setIconSize(QSize(14, 14))
        self.btn_open_iso_doc.setCursor(Qt.PointingHandCursor)
        self.btn_open_iso_doc.setToolTip(
            "Abrir documento de referencia externo en Internet Archive en el navegador predeterminado"
        )
        self.btn_open_iso_doc.clicked.connect(self._open_iso_external_doc)
        controls_header_row.addWidget(self.btn_open_iso_doc, alignment=Qt.AlignVCenter)

        layout.addLayout(controls_header_row)

        controls_grid = QGridLayout()
        controls_grid.setSpacing(16)

        controls_data = [
            (
                "5.15",
                "Control de acceso",
                "IAM-001",
                "users_lock",
                "Evalúa la correspondencia entre los grupos asignados a usuarios y los perfiles esperados, así como las relaciones de confianza de roles.",
            ),
            (
                "5.16",
                "Gestión de identidades",
                "IAM-002",
                "user_check",
                "Evalúa la vigencia, el estado de las identidades y su actividad reciente frente al umbral técnico de 90 días.",
            ),
            (
                "5.18",
                "Derechos de acceso",
                "IAM-003",
                "file_json",
                "Analiza sintácticamente las políticas JSON para detectar privilegios administrativos irrestrictos o comodines excesivos.",
            ),
            (
                "8.5",
                "Autenticación segura",
                "IAM-004",
                "key_round",
                "Verifica la exigencia y activación efectiva de autenticación multifactor (MFA) en identidades de usuario con acceso activo.",
            ),
        ]

        self.control_cards: Dict[str, QFrame] = {}

        for idx, (iso_code, name, rule_code, icon_name, desc) in enumerate(controls_data):
            card = self._create_iso_control_card(iso_code, name, rule_code, icon_name, desc)
            self.control_cards[iso_code] = card
            controls_grid.addWidget(card, idx // 2, idx % 2)

        layout.addLayout(controls_grid)

        # =====================================================================
        # 6. FUENTES DE DATOS DISPONIBLES
        # =====================================================================
        sources_title = QLabel("Fuentes de Información Soportadas")
        sources_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        layout.addWidget(sources_title)

        sources_layout = QHBoxLayout()
        sources_layout.setSpacing(16)

        sources_data = [
            (
                "Simulador Local de Datos",
                "Entorno Determinista",
                "database",
                "#294F78",
                "#EEF4FF",
                "#DBEAFE",
                "Conjunto controlado de recursos IAM diseñado para validación académica reproducible frente a las cuatro reglas de auditoría.",
            ),
            (
                "Adaptador AWS IAM (Boto3)",
                "Nube · Solo Lectura",
                "cloud",
                "#16845B",
                "#ECFDF5",
                "#D1FAE5",
                "Extracción en tiempo real de usuarios, grupos, roles y políticas en AWS mediante llamadas estrictamente de lectura.",
            ),
        ]

        for s_title, s_tag, s_icon, s_fg, s_bg, s_bdr, s_desc in sources_data:
            s_card = QFrame()
            s_card.setProperty("class", "card")
            sc_row = QHBoxLayout(s_card)
            sc_row.setContentsMargins(20, 18, 20, 18)
            sc_row.setSpacing(14)

            icon_box = create_icon_badge(
                s_icon,
                fg_color=s_fg,
                bg_color=s_bg,
                border_color=s_bdr,
                box_size=40,
                icon_size=19,
                radius=10,
            )
            sc_row.addWidget(icon_box, alignment=Qt.AlignTop)

            sc_text = QVBoxLayout()
            sc_text.setSpacing(5)

            top_s = QHBoxLayout()
            st = QLabel(s_title)
            st.setStyleSheet("font-size: 14px; font-weight: 700; color: #0F172A;")
            tag_lbl = QLabel(s_tag)
            tag_lbl.setStyleSheet(
                f"background-color: {s_bg}; color: {s_fg}; border: 1px solid {s_bdr}; "
                "border-radius: 5px; padding: 2px 8px; font-size: 10.5px; font-weight: 700;"
            )
            top_s.addWidget(st)
            top_s.addStretch()
            top_s.addWidget(tag_lbl)

            sd = QLabel(s_desc)
            sd.setWordWrap(True)
            sd.setStyleSheet("font-size: 12.5px; color: #64748B; line-height: 1.4;")

            sc_text.addLayout(top_s)
            sc_text.addWidget(sd)
            sc_row.addLayout(sc_text, stretch=1)
            sources_layout.addWidget(s_card, stretch=1)

        layout.addLayout(sources_layout)
        layout.addStretch()

        scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

    # =========================================================================
    # LÓGICA DE ACTUALIZACIÓN DEL DASHBOARD (SOLO LECTURA)
    # =========================================================================

    def _set_banner_style(self, accent_hex: str) -> None:
        self.banner.setStyleSheet(
            f"QFrame#home_status_banner {{ background-color: #FFFFFF; border: 1px solid #E5E9F0; "
            f"border-left: 3px solid {accent_hex}; border-radius: 10px; }}"
        )

    def refresh_dashboard(self) -> None:
        """
        Consulta de forma estrictamente de solo lectura los datos más recientes
        almacenados en MySQL y actualiza todos los componentes visuales del dashboard.
        """
        try:
            data = self._audit_service.get_dashboard_data()
            self.last_error = None

            if not data.get("has_data"):
                self.current_run_id = None
                self.btn_view_results.setEnabled(False)

                self._set_banner_style("#D49A32")
                self.banner_text.setText(
                    "ℹ  No hay ejecuciones registradas en la base de datos. Pulse 'Nueva auditoría' para iniciar una evaluación."
                )

                self.lbl_run_id.setText("—")
                self.lbl_run_date.setText("—")
                self.lbl_run_source.setText("—")
                self.lbl_run_status.setText("—")
                self.lbl_run_status.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 500;")
                self.lbl_run_findings.setText("—")

                self.lbl_kpi_total.setText("0")
                self.lbl_kpi_conforme.setText("0")
                self.lbl_kpi_hallazgo.setText("0")
                self.lbl_kpi_no_evaluable.setText("0")

                self.pill_kpi_conforme.setText("✓ 0.0%")
                self.pill_kpi_hallazgo.setText("! 0.0%")
                self.pill_kpi_no_eval.setText("• 0.0%")

                self.chart_view.setVisible(False)
                self.lbl_chart_empty.setVisible(True)
                self.badge_dist_conforme.setText("Conforme: 0 (0.0%)")
                self.badge_dist_hallazgo.setText("Hallazgo: 0 (0.0%)")
                self.badge_dist_no_eval.setText("No evaluable: 0 (0.0%)")

                for _, widgets in self.rule_widgets.items():
                    widgets["conforme"].setText("Conf: 0")
                    widgets["hallazgo"].setText("Hall: 0")
                    widgets["no_evaluable"].setText("NoEv: 0")
                    widgets["pct_label"].setText("0%")
                    widgets["progress"].setValue(0)
                return

            latest = data.get("latest_run") or {}
            self.current_run_id = latest.get("id")
            self.btn_view_results.setEnabled(self.current_run_id is not None)

            run_id_str = f"#{self.current_run_id}" if self.current_run_id else ""
            date_str = str(latest.get("execution_date", ""))
            self._set_banner_style("#16845B")
            self.banner_text.setText(
                f"✓  Sincronizado con la última auditoría registrada ({run_id_str} · {date_str}). "
                "Seleccione 'Ver resultados detallados' para inspeccionar cada hallazgo."
            )

            self.lbl_run_id.setText(f"#{self.current_run_id}")
            self.lbl_run_date.setText(date_str)
            self.lbl_run_source.setText(str(latest.get("source_type", "simulacion")).capitalize())

            status_raw = str(latest.get("status", "completada")).capitalize()
            self.lbl_run_status.setText(status_raw)
            self.lbl_run_status.setStyleSheet(
                "background-color: #EEF4FF; color: #1E40AF; border: 1px solid #DBEAFE; "
                "border-radius: 10px; padding: 3px 10px; font-size: 11.5px; font-weight: 700;"
            )

            findings_count = latest.get("total_findings", 0)
            self.lbl_run_findings.setText(str(findings_count))
            self.lbl_run_findings.setStyleSheet(
                f"color: {'#D64545' if findings_count else '#16845B'}; font-weight: 700; font-size: 13.5px;"
            )

            summary = data.get("summary", {})
            self.lbl_kpi_total.setText(str(summary.get("total", 0)))
            self.lbl_kpi_conforme.setText(str(summary.get("conforme", 0)))
            self.lbl_kpi_hallazgo.setText(str(summary.get("hallazgo", 0)))
            self.lbl_kpi_no_evaluable.setText(str(summary.get("no_evaluable", 0)))

            dist = data.get("distribution", {})
            conf_cnt = dist.get("conforme", {}).get("count", 0)
            conf_pct = dist.get("conforme", {}).get("percentage", 0.0)
            hall_cnt = dist.get("hallazgo", {}).get("count", 0)
            hall_pct = dist.get("hallazgo", {}).get("percentage", 0.0)
            noev_cnt = dist.get("no_evaluable", {}).get("count", 0)
            noev_pct = dist.get("no_evaluable", {}).get("percentage", 0.0)

            self.pill_kpi_conforme.setText(f"✓ {conf_pct}%")
            self.pill_kpi_hallazgo.setText(f"! {hall_pct}%")
            self.pill_kpi_no_eval.setText(f"• {noev_pct}%")

            self._update_chart(conf_cnt, conf_pct, hall_cnt, hall_pct, noev_cnt, noev_pct)

            rules_sum = data.get("rules_summary", {})
            for r_code, widgets in self.rule_widgets.items():
                r_info = rules_sum.get(r_code, {})
                c_val = int(r_info.get("conforme", 0))
                h_val = int(r_info.get("hallazgo", 0))
                ne_val = int(r_info.get("no_evaluable", 0))
                widgets["conforme"].setText(f"Conf: {c_val}")
                widgets["hallazgo"].setText(f"Hall: {h_val}")
                widgets["no_evaluable"].setText(f"NoEv: {ne_val}")

                eval_base = c_val + h_val
                pct_rule = round((c_val / eval_base) * 100) if eval_base > 0 else 0
                widgets["pct_label"].setText(f"{pct_rule}%")
                widgets["progress"].setValue(pct_rule)

                bar_col = "#16845B" if pct_rule >= 75 else ("#294F78" if pct_rule >= 45 else "#D64545")
                widgets["progress"].setStyleSheet(
                    f"QProgressBar {{ background-color: #EDF2F7; border: none; border-radius: 3px; max-height: 6px; min-height: 6px; }} "
                    f"QProgressBar::chunk {{ background-color: {bar_col}; border-radius: 3px; }}"
                )

        except Exception as exc:
            self.last_error = str(exc)
            self.current_run_id = None
            self.btn_view_results.setEnabled(False)

            self._set_banner_style("#D64545")
            self.banner_text.setText(
                f"⚠️ No se pudo conectar a la base de datos MySQL para consultar los datos del dashboard ({type(exc).__name__}). "
                "Verifique que el servidor MySQL se encuentre en ejecución y configurado correctamente."
            )

            self.chart_view.setVisible(False)
            self.lbl_chart_empty.setVisible(True)
            self.lbl_kpi_total.setText("—")
            self.lbl_kpi_conforme.setText("—")
            self.lbl_kpi_hallazgo.setText("—")
            self.lbl_kpi_no_evaluable.setText("—")
            self.pill_kpi_conforme.setText("—")
            self.pill_kpi_hallazgo.setText("—")
            self.pill_kpi_no_eval.setText("—")
            self.lbl_run_id.setText("—")
            self.lbl_run_date.setText("—")
            self.lbl_run_source.setText("—")
            self.lbl_run_status.setText("—")
            self.lbl_run_findings.setText("—")

    def _update_chart(
        self,
        conf_cnt: int,
        conf_pct: float,
        hall_cnt: int,
        hall_pct: float,
        noev_cnt: int,
        noev_pct: float,
    ) -> None:
        """Actualiza la serie del gráfico circular de distribución y las etiquetas de desglose."""
        self.badge_dist_conforme.setText(f"Conforme: {conf_cnt} ({conf_pct}%)")
        self.badge_dist_hallazgo.setText(f"Hallazgo: {hall_cnt} ({hall_pct}%)")
        self.badge_dist_no_eval.setText(f"No evaluable: {noev_cnt} ({noev_pct}%)")

        total = conf_cnt + hall_cnt + noev_cnt
        if total <= 0:
            self.chart_view.setVisible(False)
            self.lbl_chart_empty.setVisible(True)
            return

        self.lbl_chart_empty.setVisible(False)
        self.chart_view.setVisible(True)

        self.chart.removeAllSeries()
        series = QPieSeries()
        series.setHoleSize(0.54)

        for label_txt, cnt_val, hex_col in (
            (f"Conforme ({conf_pct}%)", conf_cnt, "#16845B"),
            (f"Hallazgo ({hall_pct}%)", hall_cnt, "#D64545"),
            (f"No evaluable ({noev_pct}%)", noev_cnt, "#D49A32"),
        ):
            if cnt_val > 0:
                slc = series.append(label_txt, cnt_val)
                slc.setColor(QColor(hex_col))
                slc.setBorderColor(QColor("#FFFFFF"))
                slc.setBorderWidth(2)

        self.chart.addSeries(series)

    # =========================================================================
    # NAVEGACIÓN Y VISTAS DE DETALLE
    # =========================================================================

    def _open_control_detail(self, control_code: str) -> None:
        """Abre la ventana modal con el detalle exhaustivo del control ISO seleccionado."""
        dialog = IsoControlDetailDialog(control_code=control_code, parent=self)
        dialog.exec()

    def _open_iso_external_doc(self) -> None:
        """Abre el documento de la norma alojado en Internet Archive en el navegador predeterminado."""
        QDesktopServices.openUrl(QUrl(EXTERNAL_ISO_URL))

    def _on_view_results_clicked(self) -> None:
        """Emite la señal para transferir la visualización de resultados a ResultsPage."""
        if self.current_run_id is not None:
            self.run_selected.emit(self.current_run_id)

    def _on_view_history_clicked(self) -> None:
        """Emite la señal para navegar hacia la sección de Historial."""
        self.navigate_requested.emit(3)

    # =========================================================================
    # CONSTRUCTORES DE COMPONENTES (ESTILO MERIDIAN / INDIGOSAFE)
    # =========================================================================

    @staticmethod
    def _create_hairline() -> QFrame:
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #F1F5F9; border: none;")
        return line

    def _create_kpi_card(
        self,
        title: str,
        value: str,
        pill_text: str,
        pill_fg: str,
        pill_bg: str,
        pill_border: str,
        icon_name: str,
        icon_fg: str,
        icon_bg: str,
        icon_border: str,
        footer_text: str,
        tooltip: str,
    ) -> tuple[QFrame, QLabel, QLabel]:
        """Crea una tarjeta KPI limpia con insignia de ícono superior, cifra destacada, píldora y pie."""
        card = QFrame()
        card.setProperty("class", "card")
        card.setToolTip(tooltip)

        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        # Cuerpo superior de la tarjeta
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(18, 16, 18, 14)
        body_layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(
            "color: #64748B; font-size: 11px; font-weight: 700; letter-spacing: 0.6px;"
        )
        icon_badge = create_icon_badge(
            icon_name,
            fg_color=icon_fg,
            bg_color=icon_bg,
            border_color=icon_border,
            box_size=34,
            icon_size=17,
            radius=9,
        )

        top_row.addWidget(t_lbl, stretch=1)
        top_row.addWidget(icon_badge)
        body_layout.addLayout(top_row)

        mid_row = QHBoxLayout()
        mid_row.setSpacing(10)

        v_lbl = QLabel(value)
        v_lbl.setStyleSheet("color: #0F172A; font-size: 30px; font-weight: 800;")

        p_lbl = QLabel(pill_text)
        p_lbl.setStyleSheet(
            f"background-color: {pill_bg}; color: {pill_fg}; border: 1px solid {pill_border}; "
            "border-radius: 10px; padding: 3px 9px; font-size: 11px; font-weight: 700;"
        )

        mid_row.addWidget(v_lbl)
        mid_row.addStretch()
        mid_row.addWidget(p_lbl, alignment=Qt.AlignVCenter)
        body_layout.addLayout(mid_row)

        c_layout.addWidget(body)
        c_layout.addWidget(self._create_hairline())

        # Pie sutil estilo IndigoSafe
        footer = QWidget()
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(18, 9, 18, 10)
        f_lbl = QLabel(footer_text)
        f_lbl.setStyleSheet("color: #64748B; font-size: 11.5px; font-weight: 500;")
        f_layout.addWidget(f_lbl)
        c_layout.addWidget(footer)

        return card, v_lbl, p_lbl

    def _create_iso_control_card(
        self,
        iso_code: str,
        name: str,
        rule_code: str,
        icon_name: str,
        desc: str,
    ) -> QFrame:
        """Crea una tarjeta de control ISO con insignia vectorial y franja inferior interactiva."""
        card = QFrame()
        card.setProperty("class", "card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        body = QWidget()
        b_layout = QVBoxLayout(body)
        b_layout.setContentsMargins(20, 18, 20, 14)
        b_layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        iso_badge = QLabel(f"ISO {iso_code}")
        iso_badge.setStyleSheet(
            "background-color: #EEF4FF; color: #1E40AF; border: 1px solid #DBEAFE; "
            "border-radius: 6px; padding: 3px 9px; font-weight: 700; font-size: 11px;"
        )
        rule_badge = QLabel(rule_code)
        rule_badge.setStyleSheet(
            "background-color: #F8FAFC; color: #475569; border: 1px solid #E2E8F0; "
            "border-radius: 6px; padding: 3px 9px; font-size: 11px; font-family: 'Consolas', monospace; font-weight: 700;"
        )
        icon_badge = create_icon_badge(
            icon_name,
            fg_color="#172B46",
            bg_color="#F8FAFC",
            border_color="#E2E8F0",
            box_size=34,
            icon_size=17,
            radius=9,
        )

        top_row.addWidget(iso_badge)
        top_row.addWidget(rule_badge)
        top_row.addStretch()
        top_row.addWidget(icon_badge)

        ctrl_name = QLabel(name)
        ctrl_name.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")

        ctrl_desc = QLabel(desc)
        ctrl_desc.setWordWrap(True)
        ctrl_desc.setStyleSheet("font-size: 12.5px; color: #64748B; line-height: 1.4;")

        b_layout.addLayout(top_row)
        b_layout.addWidget(ctrl_name)
        b_layout.addWidget(ctrl_desc)
        b_layout.addStretch()

        card_layout.addWidget(body, stretch=1)
        card_layout.addWidget(self._create_hairline())

        # Pie de acción interactivo estilo IndigoSafe ("Analyze threats  →")
        btn_detail = QPushButton()
        btn_detail.setFixedHeight(38)
        btn_detail.setCursor(Qt.PointingHandCursor)
        btn_detail.setToolTip(f"Consultar criterios técnicos y alcance del Control ISO {iso_code}")
        btn_detail.setStyleSheet(
            "QPushButton { background-color: transparent; border: none; "
            "border-bottom-left-radius: 11px; border-bottom-right-radius: 11px; } "
            "QPushButton:hover { background-color: #F8FAFC; }"
        )
        btn_row = QHBoxLayout(btn_detail)
        btn_row.setContentsMargins(20, 0, 20, 0)

        lbl_action = QLabel("Consultar criterios técnicos y alcance")
        lbl_action.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        lbl_action.setStyleSheet("color: #334155; font-size: 12px; font-weight: 600;")

        lbl_arrow = QLabel("→")
        lbl_arrow.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        lbl_arrow.setStyleSheet("color: #0F172A; font-size: 14px; font-weight: 700;")

        btn_row.addWidget(lbl_action)
        btn_row.addStretch()
        btn_row.addWidget(lbl_arrow)

        btn_detail.clicked.connect(lambda checked, c=iso_code: self._open_control_detail(c))
        card_layout.addWidget(btn_detail)

        return card

    @staticmethod
    def _create_distribution_badge(name: str, text: str, color: str) -> QLabel:
        lbl = QLabel(f"{name}: {text}")
        lbl.setAlignment(Qt.AlignCenter)
        bg_col = "#F8FAFC"
        border_col = "#E2E8F0"
        fg_col = color
        if color in ("#16845B", "#23845B"):
            bg_col = "#ECFDF5"
            border_col = "#D1FAE5"
            fg_col = "#16845B"
        elif color in ("#D64545", "#C24141"):
            bg_col = "#FEF2F2"
            border_col = "#FEE2E2"
            fg_col = "#D64545"
        elif color in ("#D49A32", "#B7791F"):
            bg_col = "#FFFBEB"
            border_col = "#FEF3C7"
            fg_col = "#B45309"

        lbl.setStyleSheet(
            f"background-color: {bg_col}; color: {fg_col}; border: 1px solid {border_col}; "
            "border-radius: 8px; padding: 6px 10px; font-size: 11.5px; font-weight: 700;"
        )
        return lbl
