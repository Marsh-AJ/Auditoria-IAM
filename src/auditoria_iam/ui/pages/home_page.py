"""
Página Principal / Dashboard de Auditoría IAM para la aplicación de escritorio.
Integra métricas ejecutivas, distribución gráfica de resultados, resumen por regla técnica,
catálogo interactivo de controles ISO/IEC 27001:2022 con vistas detalladas y acceso
al documento externo de la norma en Internet Archive.
"""
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.auditoria_iam.application.audit_service import AuditService
from src.auditoria_iam.ui.controls_catalog import EXTERNAL_ISO_URL, ISO_CONTROLS_DETAILS
from src.auditoria_iam.ui.dialogs.control_detail_dialog import IsoControlDetailDialog


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
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(24)

        # =====================================================================
        # 1. ENCABEZADO Y BARRA DE ACCIÓN SUPERIOR
        # =====================================================================
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title = QLabel("Dashboard de Auditoría IAM")
        title.setProperty("class", "page_title")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #38bdf8;")

        subtitle = QLabel(
            "Métricas ejecutivas de seguridad, distribución de resultados y catálogo de controles ISO/IEC 27001:2022."
        )
        subtitle.setProperty("class", "page_subtitle")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout, stretch=1)

        # Botón de actualización del dashboard
        self.btn_refresh = QPushButton("Actualizar dashboard 🔄")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setStyleSheet(
            "background-color: #1e293b; color: #f8fafc; border: 1px solid #334155; "
            "border-radius: 6px; padding: 8px 16px; font-weight: 500; font-size: 12px;"
        )
        self.btn_refresh.clicked.connect(self.refresh_dashboard)
        header_layout.addWidget(self.btn_refresh, alignment=Qt.AlignRight | Qt.AlignVCenter)

        layout.addLayout(header_layout)

        # Banner de estado informativo / advertencias
        self.banner = QFrame()
        self.banner.setStyleSheet(
            "background-color: #1e293b; border-left: 4px solid #38bdf8; border-radius: 6px; padding: 12px;"
        )
        banner_layout = QHBoxLayout(self.banner)
        banner_layout.setContentsMargins(12, 8, 12, 8)

        self.banner_text = QLabel(
            "ℹ Consultando estado del sistema y registros de auditoría en MySQL..."
        )
        self.banner_text.setWordWrap(True)
        self.banner_text.setStyleSheet("color: #e2e8f0; font-size: 13px; font-weight: 500;")
        banner_layout.addWidget(self.banner_text)
        layout.addWidget(self.banner)

        # =====================================================================
        # 2. TARJETA DE INFORMACIÓN DE LA ÚLTIMA AUDITORÍA
        # =====================================================================
        self.last_run_card = QFrame()
        self.last_run_card.setProperty("class", "card")
        self.last_run_card.setStyleSheet(
            "background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 16px;"
        )
        last_run_layout = QVBoxLayout(self.last_run_card)
        last_run_layout.setSpacing(12)

        lr_header_layout = QHBoxLayout()
        lr_title = QLabel("Información de la Última Auditoría")
        lr_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #f8fafc;")
        lr_header_layout.addWidget(lr_title)
        lr_header_layout.addStretch()

        self.btn_view_results = QPushButton("Ver resultados detallados →")
        self.btn_view_results.setEnabled(False)
        self.btn_view_results.setCursor(Qt.PointingHandCursor)
        self.btn_view_results.setStyleSheet(
            "background-color: #0284c7; color: #ffffff; border: none; border-radius: 6px; "
            "padding: 6px 14px; font-weight: bold; font-size: 12px;"
        )
        self.btn_view_results.clicked.connect(self._on_view_results_clicked)
        lr_header_layout.addWidget(self.btn_view_results)

        self.btn_view_history = QPushButton("Ver historial completo")
        self.btn_view_history.setCursor(Qt.PointingHandCursor)
        self.btn_view_history.setStyleSheet(
            "background-color: #334155; color: #f8fafc; border: none; border-radius: 6px; "
            "padding: 6px 12px; font-size: 12px;"
        )
        self.btn_view_history.clicked.connect(self._on_view_history_clicked)
        lr_header_layout.addWidget(self.btn_view_history)

        last_run_layout.addLayout(lr_header_layout)

        # Campos de detalle de la auditoría en cuadrícula
        lr_grid = QGridLayout()
        lr_grid.setHorizontalSpacing(24)
        lr_grid.setVerticalSpacing(6)

        lbl_id_title = QLabel("ID Ejecución:")
        lbl_id_title.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.lbl_run_id = QLabel("—")
        self.lbl_run_id.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 13px;")

        lbl_date_title = QLabel("Fecha y Hora:")
        lbl_date_title.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.lbl_run_date = QLabel("—")
        self.lbl_run_date.setStyleSheet("color: #f8fafc; font-size: 13px;")

        lbl_src_title = QLabel("Fuente de Datos:")
        lbl_src_title.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.lbl_run_source = QLabel("—")
        self.lbl_run_source.setStyleSheet("color: #f8fafc; font-size: 13px;")

        lbl_status_title = QLabel("Estado:")
        lbl_status_title.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.lbl_run_status = QLabel("—")
        self.lbl_run_status.setStyleSheet("color: #f8fafc; font-size: 13px;")

        lbl_find_title = QLabel("Hallazgos Detectados:")
        lbl_find_title.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.lbl_run_findings = QLabel("—")
        self.lbl_run_findings.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 13px;")

        lr_grid.addWidget(lbl_id_title, 0, 0)
        lr_grid.addWidget(self.lbl_run_id, 0, 1)
        lr_grid.addWidget(lbl_date_title, 0, 2)
        lr_grid.addWidget(self.lbl_run_date, 0, 3)
        lr_grid.addWidget(lbl_src_title, 1, 0)
        lr_grid.addWidget(self.lbl_run_source, 1, 1)
        lr_grid.addWidget(lbl_status_title, 1, 2)
        lr_grid.addWidget(self.lbl_run_status, 1, 3)
        lr_grid.addWidget(lbl_find_title, 1, 4)
        lr_grid.addWidget(self.lbl_run_findings, 1, 5)

        last_run_layout.addLayout(lr_grid)
        layout.addWidget(self.last_run_card)

        # =====================================================================
        # 3. CUATRO TARJETAS DE INDICADORES PRINCIPALES (KPI)
        # =====================================================================
        kpi_title = QLabel("Indicadores Principales de Evaluación")
        kpi_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(kpi_title)

        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        # 1. Total
        self.card_total, self.lbl_kpi_total = self._create_kpi_card(
            "Total Evaluaciones", "—", "#38bdf8", "Total de criterios evaluados en la auditoría"
        )
        # 2. Conforme
        self.card_conforme, self.lbl_kpi_conforme = self._create_kpi_card(
            "Conforme", "—", "#22c55e", "Criterios que cumplen las condiciones técnicas"
        )
        # 3. Hallazgo
        self.card_hallazgo, self.lbl_kpi_hallazgo = self._create_kpi_card(
            "Hallazgo", "—", "#ef4444", "Anomalías o desviaciones técnicas detectadas"
        )
        # 4. No evaluable
        self.card_no_evaluable, self.lbl_kpi_no_evaluable = self._create_kpi_card(
            "No evaluable", "—", "#f59e0b", "Identidades con metadatos ausentes o incompletos"
        )

        kpi_layout.addWidget(self.card_total)
        kpi_layout.addWidget(self.card_conforme)
        kpi_layout.addWidget(self.card_hallazgo)
        kpi_layout.addWidget(self.card_no_evaluable)
        layout.addLayout(kpi_layout)

        # =====================================================================
        # 4. GRÁFICO DE DISTRIBUCIÓN Y RESUMEN POR REGLA
        # =====================================================================
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        # Panel izquierdo: Gráfico circular de distribución
        chart_card = QFrame()
        chart_card.setProperty("class", "card")
        chart_card.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 14px;")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setSpacing(10)

        chart_header = QLabel("Distribución de Resultados")
        chart_header.setStyleSheet("font-size: 15px; font-weight: bold; color: #f8fafc;")
        chart_layout.addWidget(chart_header)

        # Mensaje de placeholder cuando no hay datos
        self.lbl_chart_empty = QLabel("ℹ No hay información disponible.\nAún no se han registrado auditorías en el sistema.")
        self.lbl_chart_empty.setAlignment(Qt.AlignCenter)
        self.lbl_chart_empty.setStyleSheet("color: #94a3b8; font-size: 13px; padding: 30px;")
        chart_layout.addWidget(self.lbl_chart_empty)

        # QChart y QChartView de PySide6
        self.chart = QChart()
        self.chart.setBackgroundVisible(False)
        self.chart.layout().setContentsMargins(0, 0, 0, 0)
        self.chart.legend().setVisible(False)  # Usamos desglose explícito en badges

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(self.chart_view.renderHints())
        self.chart_view.setMinimumHeight(200)
        self.chart_view.setMaximumHeight(220)
        self.chart_view.setStyleSheet("background: transparent;")
        self.chart_view.setVisible(False)
        chart_layout.addWidget(self.chart_view)

        # Desglose numérico y porcentual debajo del gráfico
        self.dist_breakdown_layout = QHBoxLayout()
        self.dist_breakdown_layout.setSpacing(8)

        self.badge_dist_conforme = self._create_distribution_badge("Conforme", "—", "#22c55e")
        self.badge_dist_hallazgo = self._create_distribution_badge("Hallazgo", "—", "#ef4444")
        self.badge_dist_no_eval = self._create_distribution_badge("No evaluable", "—", "#f59e0b")

        self.dist_breakdown_layout.addWidget(self.badge_dist_conforme)
        self.dist_breakdown_layout.addWidget(self.badge_dist_hallazgo)
        self.dist_breakdown_layout.addWidget(self.badge_dist_no_eval)
        chart_layout.addLayout(self.dist_breakdown_layout)

        charts_row.addWidget(chart_card, stretch=1)

        # Panel derecho: Resumen por regla IAM
        rules_card = QFrame()
        rules_card.setProperty("class", "card")
        rules_card.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 14px;")
        rules_layout = QVBoxLayout(rules_card)
        rules_layout.setSpacing(10)

        rules_header = QLabel("Resumen por Regla de Auditoría")
        rules_header.setStyleSheet("font-size: 15px; font-weight: bold; color: #f8fafc;")
        rules_layout.addWidget(rules_header)

        # Contenedor para las 4 reglas
        self.rule_widgets: Dict[str, Dict[str, QLabel]] = {}
        rules_meta = [
            ("IAM-001", "Control 5.15 — Control de acceso"),
            ("IAM-002", "Control 5.16 — Gestión de identidades"),
            ("IAM-003", "Control 5.18 — Derechos de acceso"),
            ("IAM-004", "Control 8.5 — Autenticación segura"),
        ]

        for r_code, r_title in rules_meta:
            r_box = QFrame()
            r_box.setStyleSheet("background-color: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 8px 12px;")
            rb_layout = QHBoxLayout(r_box)
            rb_layout.setContentsMargins(8, 4, 8, 4)
            rb_layout.setSpacing(10)

            # Nombre de la regla
            r_name_layout = QVBoxLayout()
            r_name_layout.setSpacing(1)
            lbl_code = QLabel(r_code)
            lbl_code.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px; font-family: monospace;")
            lbl_name = QLabel(r_title)
            lbl_name.setStyleSheet("color: #94a3b8; font-size: 11px;")
            r_name_layout.addWidget(lbl_code)
            r_name_layout.addWidget(lbl_name)
            rb_layout.addLayout(r_name_layout, stretch=1)

            # Contadores por regla
            lbl_c = QLabel("Conf: 0")
            lbl_c.setStyleSheet("color: #22c55e; font-weight: bold; font-size: 11px;")
            lbl_h = QLabel("Hall: 0")
            lbl_h.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 11px;")
            lbl_ne = QLabel("NoEv: 0")
            lbl_ne.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 11px;")

            rb_layout.addWidget(lbl_c)
            rb_layout.addWidget(lbl_h)
            rb_layout.addWidget(lbl_ne)

            self.rule_widgets[r_code] = {
                "conforme": lbl_c,
                "hallazgo": lbl_h,
                "no_evaluable": lbl_ne,
            }
            rules_layout.addWidget(r_box)

        charts_row.addWidget(rules_card, stretch=1)
        layout.addLayout(charts_row)

        # =====================================================================
        # 5. CATÁLOGO INTERACTIVO DE CONTROLES ISO/IEC 27001:2022
        # =====================================================================
        controls_section_layout = QVBoxLayout()
        controls_section_layout.setSpacing(6)

        controls_title = QLabel("Catálogo Interactivo de Controles ISO/IEC 27001:2022")
        controls_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")

        controls_subtitle = QLabel(
            "Seleccione cualquiera de los cuatro controles técnicos evaluados por el sistema para consultar "
            "su alcance, criterios algorítmicos y delimitaciones de certificación."
        )
        controls_subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")

        controls_section_layout.addWidget(controls_title)
        controls_section_layout.addWidget(controls_subtitle)
        layout.addLayout(controls_section_layout)

        # Barra de acceso externo a la norma
        doc_bar = QFrame()
        doc_bar.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 10px 14px;")
        db_layout = QHBoxLayout(doc_bar)
        db_layout.setContentsMargins(8, 6, 8, 6)

        doc_info = QLabel("Norma de referencia:")
        doc_info.setStyleSheet("color: #94a3b8; font-size: 12px;")
        db_layout.addWidget(doc_info)

        self.btn_open_iso_doc = QPushButton("Consultar documento ISO/IEC 27001:2022 ↗")
        self.btn_open_iso_doc.setCursor(Qt.PointingHandCursor)
        self.btn_open_iso_doc.setStyleSheet(
            "background-color: #0369a1; color: #ffffff; border: none; border-radius: 4px; "
            "padding: 6px 14px; font-weight: bold; font-size: 12px;"
        )
        self.btn_open_iso_doc.clicked.connect(self._open_iso_external_doc)
        db_layout.addWidget(self.btn_open_iso_doc)

        doc_disclaimer = QLabel(
            "Recurso externo independiente alojado en Internet Archive (tercera edición). Se abrirá en el navegador predeterminado."
        )
        doc_disclaimer.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
        db_layout.addWidget(doc_disclaimer)
        db_layout.addStretch()

        layout.addWidget(doc_bar)

        # Cuadrícula 2x2 interactiva de controles
        controls_grid = QGridLayout()
        controls_grid.setSpacing(16)

        controls_data = [
            ("5.15", "Control de acceso", "IAM-001", "Verificación de correspondencia de grupos asignados y relaciones de confianza en roles."),
            ("5.16", "Gestión de identidades", "IAM-002", "Identificación de identidades con actividad inactiva superior al umbral configurable de 90 días, mediante los metadatos disponibles."),
            ("5.18", "Derechos de acceso", "IAM-003", "Análisis sintáctico estricto de políticas JSON para prevenir patrones de permisos excesivamente amplios."),
            ("8.5", "Autenticación segura", "IAM-004", "Exigencia de autenticación multifactor (MFA) obligatoria en usuarios activos de la plataforma.")
        ]

        self.control_cards: Dict[str, QFrame] = {}

        for idx, (iso_code, name, rule_code, desc) in enumerate(controls_data):
            card = QFrame()
            card.setProperty("class", "card")
            card.setStyleSheet(
                "background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 14px;"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(8)

            badge_layout = QHBoxLayout()
            iso_badge = QLabel(f"ISO {iso_code}")
            iso_badge.setStyleSheet(
                "background-color: #0369a1; color: #e0f2fe; border-radius: 4px; padding: 3px 8px; font-weight: bold; font-size: 11px;"
            )
            rule_badge = QLabel(rule_code)
            rule_badge.setStyleSheet(
                "background-color: #334155; color: #94a3b8; border-radius: 4px; padding: 3px 8px; font-size: 11px; font-family: monospace;"
            )
            badge_layout.addWidget(iso_badge)
            badge_layout.addWidget(rule_badge)
            badge_layout.addStretch()

            ctrl_name = QLabel(name)
            ctrl_name.setStyleSheet("font-size: 14px; font-weight: 600; color: #f8fafc;")

            ctrl_desc = QLabel(desc)
            ctrl_desc.setWordWrap(True)
            ctrl_desc.setStyleSheet("font-size: 12px; color: #94a3b8; line-height: 1.3;")

            # Botón interactivo para ver detalles del control
            btn_detail = QPushButton("Consultar detalle técnico →")
            btn_detail.setCursor(Qt.PointingHandCursor)
            btn_detail.setStyleSheet(
                "background-color: #0f172a; color: #38bdf8; border: 1px solid #334155; "
                "border-radius: 4px; padding: 6px 10px; font-size: 11px; font-weight: 500;"
            )
            btn_detail.clicked.connect(lambda checked, c=iso_code: self._open_control_detail(c))

            card_layout.addLayout(badge_layout)
            card_layout.addWidget(ctrl_name)
            card_layout.addWidget(ctrl_desc)
            card_layout.addStretch()
            card_layout.addWidget(btn_detail, alignment=Qt.AlignRight)

            self.control_cards[iso_code] = card

            row = idx // 2
            col = idx % 2
            controls_grid.addWidget(card, row, col)

        layout.addLayout(controls_grid)

        # =====================================================================
        # 6. SECCIÓN: FUENTES DE INFORMACIÓN DISPONIBLES
        # =====================================================================
        sources_title = QLabel("Fuentes de Datos Disponibles")
        sources_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(sources_title)

        sources_layout = QHBoxLayout()
        sources_layout.setSpacing(16)

        sources_data = [
            ("Simulador Local de Datos", "Dataset determinista diseñado para pruebas y validación académica frente a los 8 criterios de auditoría."),
            ("Adaptador AWS IAM (Boto3)", "Consulta en vivo de identidades, grupos, roles y políticas de AWS en modo estrictamente de solo lectura mediante el adaptador; su ejecución desde la interfaz se habilitará en la siguiente entrega.")
        ]

        for s_title, s_desc in sources_data:
            s_card = QFrame()
            s_card.setProperty("class", "card")
            s_card.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 14px;")
            sc_layout = QVBoxLayout(s_card)
            sc_layout.setSpacing(6)

            st = QLabel(s_title)
            st.setStyleSheet("font-size: 14px; font-weight: 600; color: #38bdf8;")
            sd = QLabel(s_desc)
            sd.setWordWrap(True)
            sd.setStyleSheet("font-size: 12px; color: #94a3b8;")

            sc_layout.addWidget(st)
            sc_layout.addWidget(sd)
            sc_layout.addStretch()
            sources_layout.addWidget(s_card)

        layout.addLayout(sources_layout)
        layout.addStretch()

        scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

    # =========================================================================
    # LÓGICA DE ACTUALIZACIÓN DEL DASHBOARD (SOLO LECTURA)
    # =========================================================================

    def refresh_dashboard(self) -> None:
        """
        Consulta de forma estrictamente de solo lectura los datos más recientes
        almacenados en MySQL y actualiza todos los componentes visuales del dashboard.
        """
        try:
            data = self._audit_service.get_dashboard_data()
            self.last_error = None

            if not data.get("has_data"):
                # No existen auditorías registradas en MySQL
                self.current_run_id = None
                self.btn_view_results.setEnabled(False)

                self.banner.setStyleSheet(
                    "background-color: #0f172a; border-left: 4px solid #f59e0b; border-radius: 6px; padding: 12px;"
                )
                self.banner_text.setText(
                    "ℹ No hay ejecuciones registradas. Ejecute una auditoría desde el menú lateral para visualizar métricas en este dashboard."
                )

                # Resetear información de última auditoría
                self.lbl_run_id.setText("—")
                self.lbl_run_date.setText("—")
                self.lbl_run_source.setText("—")
                self.lbl_run_status.setText("—")
                self.lbl_run_findings.setText("—")

                # Resetear KPIs
                self.lbl_kpi_total.setText("0")
                self.lbl_kpi_conforme.setText("0")
                self.lbl_kpi_hallazgo.setText("0")
                self.lbl_kpi_no_evaluable.setText("0")

                # Ocultar gráfico y mostrar placeholder
                self.chart_view.setVisible(False)
                self.lbl_chart_empty.setVisible(True)
                self.badge_dist_conforme.setText("Conforme: 0 (0.0%)")
                self.badge_dist_hallazgo.setText("Hallazgo: 0 (0.0%)")
                self.badge_dist_no_eval.setText("No evaluable: 0 (0.0%)")

                # Resetear resumen por regla
                for r_code, widgets in self.rule_widgets.items():
                    widgets["conforme"].setText("Conf: 0")
                    widgets["hallazgo"].setText("Hall: 0")
                    widgets["no_evaluable"].setText("NoEv: 0")
                return

            # Auditoría válida recuperada
            latest = data.get("latest_run") or {}
            self.current_run_id = latest.get("id")
            self.btn_view_results.setEnabled(self.current_run_id is not None)

            # Banner de estado exitoso
            run_id_str = f"#{self.current_run_id}" if self.current_run_id else ""
            date_str = str(latest.get("execution_date", ""))
            self.banner.setStyleSheet(
                "background-color: #0f172a; border-left: 4px solid #22c55e; border-radius: 6px; padding: 12px;"
            )
            self.banner_text.setText(
                f"✓ Mostrando métricas de la última auditoría registrada ({run_id_str} — {date_str}). "
                "Pulse 'Ver resultados detallados' para explorar la evaluación granular."
            )

            # Actualizar tarjeta de última auditoría
            self.lbl_run_id.setText(f"#{self.current_run_id}")
            self.lbl_run_date.setText(date_str)
            self.lbl_run_source.setText(str(latest.get("source_type", "simulacion")).capitalize())
            self.lbl_run_status.setText(str(latest.get("status", "completada")).capitalize())
            self.lbl_run_findings.setText(str(latest.get("total_findings", 0)))

            # Actualizar KPIs
            summary = data.get("summary", {})
            self.lbl_kpi_total.setText(str(summary.get("total", 0)))
            self.lbl_kpi_conforme.setText(str(summary.get("conforme", 0)))
            self.lbl_kpi_hallazgo.setText(str(summary.get("hallazgo", 0)))
            self.lbl_kpi_no_evaluable.setText(str(summary.get("no_evaluable", 0)))

            # Actualizar gráfico de distribución
            dist = data.get("distribution", {})
            conf_cnt = dist.get("conforme", {}).get("count", 0)
            conf_pct = dist.get("conforme", {}).get("percentage", 0.0)
            hall_cnt = dist.get("hallazgo", {}).get("count", 0)
            hall_pct = dist.get("hallazgo", {}).get("percentage", 0.0)
            noev_cnt = dist.get("no_evaluable", {}).get("count", 0)
            noev_pct = dist.get("no_evaluable", {}).get("percentage", 0.0)

            self._update_chart(conf_cnt, conf_pct, hall_cnt, hall_pct, noev_cnt, noev_pct)

            # Actualizar resumen por regla
            rules_sum = data.get("rules_summary", {})
            for r_code, widgets in self.rule_widgets.items():
                r_info = rules_sum.get(r_code, {})
                c_val = r_info.get("conforme", 0)
                h_val = r_info.get("hallazgo", 0)
                ne_val = r_info.get("no_evaluable", 0)
                widgets["conforme"].setText(f"Conf: {c_val}")
                widgets["hallazgo"].setText(f"Hall: {h_val}")
                widgets["no_evaluable"].setText(f"NoEv: {ne_val}")

        except Exception as exc:
            self.last_error = str(exc)
            self.current_run_id = None
            self.btn_view_results.setEnabled(False)

            self.banner.setStyleSheet(
                "background-color: #0f172a; border-left: 4px solid #ef4444; border-radius: 6px; padding: 12px;"
            )
            self.banner_text.setText(
                f"⚠️ No se pudo conectar a la base de datos MySQL para consultar los datos del dashboard ({type(exc).__name__}). "
                "Verifique que el servidor MySQL se encuentre en ejecución y configurado correctamente."
            )

            # Ocultar gráfico y resetear campos para evitar presentar datos antiguos o ficticios
            self.chart_view.setVisible(False)
            self.lbl_chart_empty.setVisible(True)
            self.lbl_kpi_total.setText("—")
            self.lbl_kpi_conforme.setText("—")
            self.lbl_kpi_hallazgo.setText("—")
            self.lbl_kpi_no_evaluable.setText("—")
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
        series.setHoleSize(0.35)  # Aspecto elegante de dona

        if conf_cnt > 0:
            s_c = series.append(f"Conforme ({conf_pct}%)", conf_cnt)
            s_c.setColor(QColor("#22c55e"))
            s_c.setBorderColor(QColor("#14532d"))

        if hall_cnt > 0:
            s_h = series.append(f"Hallazgo ({hall_pct}%)", hall_cnt)
            s_h.setColor(QColor("#ef4444"))
            s_h.setBorderColor(QColor("#7f1d1d"))

        if noev_cnt > 0:
            s_ne = series.append(f"No evaluable ({noev_pct}%)", noev_cnt)
            s_ne.setColor(QColor("#f59e0b"))
            s_ne.setBorderColor(QColor("#78350f"))

        self.chart.addSeries(series)

    # =========================================================================
    # NAVEGACIÓN Y VISTAS DE DETALLE
    # =========================================================================

    def _open_control_detail(self, control_code: str) -> None:
        """Abre la ventana modal con el detalle exhaustivo del control ISO seleccionado."""
        dialog = IsoControlDetailDialog(control_code=control_code, parent=self)
        dialog.exec()

    def _open_iso_external_doc(self) -> None:
        """Abre de forma segura el documento PDF de la norma alojado en Internet Archive en el navegador predeterminado."""
        QDesktopServices.openUrl(QUrl(EXTERNAL_ISO_URL))

    def _on_view_results_clicked(self) -> None:
        """Emite la señal para transferir la visualización de resultados a ResultsPage."""
        if self.current_run_id is not None:
            self.run_selected.emit(self.current_run_id)

    def _on_view_history_clicked(self) -> None:
        """Emite la señal para navegar hacia la sección de Historial."""
        self.navigate_requested.emit(3)

    # =========================================================================
    # HELPERS VISUALES
    # =========================================================================

    def _create_kpi_card(
        self, title: str, value: str, accent_color: str, tooltip: str
    ) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setProperty("class", "card")
        card.setStyleSheet(
            f"background-color: #1e293b; border: 1px solid #334155; border-top: 3px solid {accent_color}; "
            "border-radius: 8px; padding: 14px;"
        )
        card.setToolTip(tooltip)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(12, 10, 12, 10)
        c_layout.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")

        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(f"color: {accent_color}; font-size: 26px; font-weight: bold;")

        c_layout.addWidget(t_lbl)
        c_layout.addWidget(v_lbl)
        c_layout.addStretch()

        return card, v_lbl

    def _create_distribution_badge(self, name: str, text: str, color: str) -> QLabel:
        lbl = QLabel(f"{name}: {text}")
        lbl.setStyleSheet(
            f"background-color: #0f172a; color: {color}; border: 1px solid #334155; "
            "border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: 500;"
        )
        return lbl
