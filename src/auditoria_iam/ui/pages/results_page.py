"""
Página de Resultados para el Sistema de Auditoría IAM.
Presenta indicadores ejecutivos tipo consola SaaS, visualización tabular limpia
integrada en tarjeta corporativa y exportación en formatos PDF, Excel (XLSX) y CSV.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.auditoria_iam.application.audit_service import AuditService
from src.auditoria_iam.audit.models import AuditResult
from src.auditoria_iam.ui.icons import create_icon_badge, render_svg_icon


class ResultsPage(QWidget):
    """Pantalla para la visualización de resultados técnicos de auditoría y exportación."""

    RULE_TO_ISO = {
        "IAM-001": "5.15",
        "IAM-002": "5.16",
        "IAM-003": "5.18",
        "IAM-004": "8.5",
    }

    def __init__(
        self,
        parent: QWidget | None = None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("results_page")
        self._audit_service = audit_service or AuditService()
        self._current_results: List[AuditResult] = []
        self._current_resources: List[Dict[str, Any]] = []
        self._current_summary: Dict[str, int] = {}
        self._current_run_id: Optional[int] = None
        self._init_ui()

    def _init_ui(self) -> None:
        self.setStyleSheet("QWidget#results_page { background-color: #F5F7FA; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(16)

        # 1. Encabezado de la página
        title_col = QVBoxLayout()
        title_col.setSpacing(3)

        title = QLabel("Resultados de Auditoría")
        title.setProperty("class", "page_title")

        subtitle = QLabel(
            "Inspección granular de verificaciones técnicas ISO/IEC 27001:2022 y generación de informes ejecutivos."
        )
        subtitle.setProperty("class", "page_subtitle")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        layout.addLayout(title_col)

        # 2. Fila de 4 tarjetas KPI independientes (consistentes con Dashboard)
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(16)

        c_tot, self.lbl_total, self.pill_total = self._create_kpi_card(
            "TOTAL EVALUACIONES",
            "0",
            "Base 100%",
            "#294F78",
            "#EEF4FF",
            "#DBEAFE",
            "layers",
            "Criterios procesados",
        )
        c_conf, self.lbl_conforme, self.pill_conforme = self._create_kpi_card(
            "CONFORMES",
            "0",
            "✓ 0%",
            "#16845B",
            "#ECFDF5",
            "#A7F3D0",
            "shield_check",
            "Cumplen parámetros ISO",
        )
        c_hall, self.lbl_hallazgo, self.pill_hallazgo = self._create_kpi_card(
            "HALLAZGOS",
            "0",
            "! 0%",
            "#D64545",
            "#FEF2F2",
            "#FECACA",
            "alert_triangle",
            "Desviaciones detectadas",
        )
        c_noev, self.lbl_no_evaluable, self.pill_no_eval = self._create_kpi_card(
            "NO EVALUABLES",
            "0",
            "• 0%",
            "#B45309",
            "#FFFBEB",
            "#FDE68A",
            "info_circle",
            "Metadatos no aplicables",
        )

        kpi_row.addWidget(c_tot, stretch=1)
        kpi_row.addWidget(c_conf, stretch=1)
        kpi_row.addWidget(c_hall, stretch=1)
        kpi_row.addWidget(c_noev, stretch=1)
        layout.addLayout(kpi_row)

        # 3. Franja discreta de estado informativo
        self.info_banner = QFrame()
        self.info_banner.setObjectName("results_info_banner")
        self._set_banner_style("#D49A32")
        banner_layout = QVBoxLayout(self.info_banner)
        banner_layout.setContentsMargins(16, 10, 16, 10)

        self.banner_text = QLabel(
            "ℹ  Aún no se ha cargado ninguna auditoría en esta sesión. "
            "Inicie una evaluación desde 'Ejecutar auditoría' o seleccione un registro en 'Historial'."
        )
        self.banner_text.setWordWrap(True)
        self.banner_text.setStyleSheet("color: #334155; font-size: 12.5px; font-weight: 500;")
        banner_layout.addWidget(self.banner_text)
        layout.addWidget(self.info_banner)

        # 4. Tarjeta de tabla estilo consola empresarial (con cabecera y barra de exportación integrada)
        table_card = QFrame()
        table_card.setProperty("class", "card")
        tc_layout = QVBoxLayout(table_card)
        tc_layout.setContentsMargins(0, 14, 0, 6)
        tc_layout.setSpacing(10)

        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(20, 0, 20, 4)
        toolbar_row.setSpacing(8)

        lbl_table_title = QLabel("Detalle de Evaluaciones Técnicas")
        lbl_table_title.setProperty("class", "card_header_title")
        toolbar_row.addWidget(lbl_table_title)
        toolbar_row.addStretch()

        lbl_export = QLabel("Exportar:")
        lbl_export.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600; margin-right: 4px;")
        toolbar_row.addWidget(lbl_export)

        self.btn_export_pdf = QPushButton("  PDF")
        self.btn_export_pdf.setProperty("class", "primary_button")
        self.btn_export_pdf.setIcon(render_svg_icon("file_export", color="#FFFFFF", disabled_color="#94A3B8", size=14))
        self.btn_export_pdf.setIconSize(QSize(14, 14))
        self.btn_export_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_export_pdf.setEnabled(False)
        self.btn_export_pdf.clicked.connect(lambda: self.export_results("pdf"))
        toolbar_row.addWidget(self.btn_export_pdf)

        self.btn_export_excel = QPushButton("  Excel")
        self.btn_export_excel.setProperty("class", "secondary_button")
        self.btn_export_excel.setIcon(render_svg_icon("file_export", color="#16845B", disabled_color="#94A3B8", size=14))
        self.btn_export_excel.setIconSize(QSize(14, 14))
        self.btn_export_excel.setCursor(Qt.PointingHandCursor)
        self.btn_export_excel.setEnabled(False)
        self.btn_export_excel.clicked.connect(lambda: self.export_results("xlsx"))
        toolbar_row.addWidget(self.btn_export_excel)

        self.btn_export_csv = QPushButton("  CSV")
        self.btn_export_csv.setProperty("class", "secondary_button")
        self.btn_export_csv.setIcon(render_svg_icon("file_export", color="#294F78", disabled_color="#94A3B8", size=14))
        self.btn_export_csv.setIconSize(QSize(14, 14))
        self.btn_export_csv.setCursor(Qt.PointingHandCursor)
        self.btn_export_csv.setEnabled(False)
        self.btn_export_csv.clicked.connect(lambda: self.export_results("csv"))
        toolbar_row.addWidget(self.btn_export_csv)

        tc_layout.addLayout(toolbar_row)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Recurso Auditado",
            "Tipo de Recurso",
            "Regla Evaluada",
            "Control ISO",
            "Estado",
            "Descripción del Resultado",
        ])
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setRowCount(0)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setWordWrap(True)

        tc_layout.addWidget(self.results_table, stretch=1)
        layout.addWidget(table_card, stretch=1)

    def _set_banner_style(self, accent_hex: str) -> None:
        self.info_banner.setStyleSheet(
            f"QFrame#results_info_banner {{ background-color: #FFFFFF; border: 1px solid #E5E9F0; "
            f"border-left: 3px solid {accent_hex}; border-radius: 10px; }}"
        )

    @staticmethod
    def _create_kpi_card(
        label_text: str,
        default_val: str,
        pill_text: str,
        fg_hex: str,
        bg_hex: str,
        border_hex: str,
        icon_name: str,
        footer_caption: str,
    ) -> tuple[QFrame, QLabel, QLabel]:
        card = QFrame()
        card.setProperty("class", "card")

        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        body = QWidget()
        b_layout = QVBoxLayout(body)
        b_layout.setContentsMargins(18, 14, 18, 12)
        b_layout.setSpacing(8)

        top_row = QHBoxLayout()
        title = QLabel(label_text)
        title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.6px;")
        icon_box = create_icon_badge(
            icon_name,
            fg_color=fg_hex,
            bg_color=bg_hex,
            border_color=border_hex,
            box_size=32,
            icon_size=16,
            radius=8,
        )
        top_row.addWidget(title, stretch=1)
        top_row.addWidget(icon_box)
        b_layout.addLayout(top_row)

        mid_row = QHBoxLayout()
        val_label = QLabel(default_val)
        val_label.setStyleSheet("font-size: 26px; font-weight: 800; color: #0F172A;")

        pill_lbl = QLabel(pill_text)
        pill_lbl.setStyleSheet(
            f"background-color: {bg_hex}; color: {fg_hex}; border: 1px solid {border_hex}; "
            "border-radius: 10px; padding: 2px 8px; font-size: 10.5px; font-weight: 700;"
        )
        mid_row.addWidget(val_label)
        mid_row.addStretch()
        mid_row.addWidget(pill_lbl, alignment=Qt.AlignVCenter)
        b_layout.addLayout(mid_row)

        c_layout.addWidget(body)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #F1F5F9; border: none;")
        c_layout.addWidget(line)

        footer = QWidget()
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(18, 7, 18, 8)
        f_lbl = QLabel(footer_caption)
        f_lbl.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 500;")
        f_layout.addWidget(f_lbl)
        c_layout.addWidget(footer)

        return card, val_label, pill_lbl

    def load_results(
        self,
        results: List[AuditResult],
        resources: List[Dict[str, Any]],
        summary: Dict[str, int],
        run_id: Optional[int] = None,
    ) -> None:
        """
        Carga y visualiza los resultados reales de auditoría en la tabla y contadores de resumen.
        Habilita los botones de exportación cuando hay datos disponibles.
        """
        self._current_results = results
        self._current_resources = resources
        self._current_summary = summary
        self._current_run_id = run_id

        has_data = len(results) > 0
        self.btn_export_pdf.setEnabled(has_data)
        self.btn_export_excel.setEnabled(has_data)
        self.btn_export_csv.setEnabled(has_data)

        total_n = int(summary.get("total", len(results)))
        conf_n = int(summary.get("conforme", 0))
        hall_n = int(summary.get("hallazgo", 0))
        noev_n = int(summary.get("no_evaluable", 0))

        self.lbl_total.setText(str(total_n))
        self.lbl_conforme.setText(str(conf_n))
        self.lbl_hallazgo.setText(str(hall_n))
        self.lbl_no_evaluable.setText(str(noev_n))

        if total_n > 0:
            self.pill_conforme.setText(f"✓ {round((conf_n / total_n) * 100, 1)}%")
            self.pill_hallazgo.setText(f"! {round((hall_n / total_n) * 100, 1)}%")
            self.pill_no_eval.setText(f"• {round((noev_n / total_n) * 100, 1)}%")
        else:
            self.pill_conforme.setText("✓ 0%")
            self.pill_hallazgo.setText("! 0%")
            self.pill_no_eval.setText("• 0%")

        self._set_banner_style("#16845B")
        if run_id is not None:
            self.banner_text.setText(
                f"✓  Mostrando resultados históricos de la ejecución #{run_id} recuperados desde MySQL "
                f"({len(resources)} recursos IAM · {len(results)} evaluaciones registradas)."
            )
        else:
            self.banner_text.setText(
                f"✓  Mostrando resultados de la última ejecución completada "
                f"({len(resources)} recursos IAM · {len(results)} evaluaciones registradas)."
            )

        resource_index: Dict[Any, Dict[str, Any]] = {
            r.get("id"): r for r in resources if "id" in r
        }

        self.results_table.setRowCount(len(results))

        for row_idx, res in enumerate(results):
            res_meta = resource_index.get(res.resource_id, {})
            resource_name = res_meta.get("resource_key") or res_meta.get("display_name") or f"ID {res.resource_id}"
            resource_type = res_meta.get("resource_type", "IAM_RESOURCE")
            iso_control = self.RULE_TO_ISO.get(res.rule_code, "N/A")

            item_resource = QTableWidgetItem(str(resource_name))
            item_resource.setToolTip(f"{resource_name} ({resource_type})")
            res_font = QFont()
            res_font.setBold(True)
            item_resource.setFont(res_font)

            item_type = QTableWidgetItem(str(resource_type))
            item_type.setForeground(QColor("#64748B"))

            item_rule = QTableWidgetItem(str(res.rule_code))
            item_rule.setTextAlignment(Qt.AlignCenter)

            item_iso = QTableWidgetItem(f"ISO {iso_control}")
            item_iso.setTextAlignment(Qt.AlignCenter)

            item_status = QTableWidgetItem(str(res.result_status))
            item_justification = QTableWidgetItem(str(res.justification))
            item_justification.setToolTip(str(res.justification))

            status_font = QFont()
            status_font.setBold(True)
            item_status.setFont(status_font)
            item_status.setTextAlignment(Qt.AlignCenter)

            if res.result_status == "Conforme":
                item_status.setForeground(QColor("#16845B"))
                item_status.setBackground(QColor("#ECFDF5"))
            elif res.result_status == "Hallazgo":
                item_status.setForeground(QColor("#D64545"))
                item_status.setBackground(QColor("#FEF2F2"))
            else:
                item_status.setForeground(QColor("#B45309"))
                item_status.setBackground(QColor("#FFFBEB"))

            for item in (item_resource, item_type, item_rule, item_iso, item_status, item_justification):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            self.results_table.setItem(row_idx, 0, item_resource)
            self.results_table.setItem(row_idx, 1, item_type)
            self.results_table.setItem(row_idx, 2, item_rule)
            self.results_table.setItem(row_idx, 3, item_iso)
            self.results_table.setItem(row_idx, 4, item_status)
            self.results_table.setItem(row_idx, 5, item_justification)

        self.results_table.resizeRowsToContents()

    def export_results(self, format_type: str) -> None:
        """
        Abre un diálogo estándar para seleccionar ubicación y genera el archivo
        de reporte de auditoría en el formato indicado.
        """
        if not self._current_results:
            self._set_banner_style("#D49A32")
            self.banner_text.setText("⚠  No hay resultados disponibles para exportar en esta sesión.")
            return

        fmt = format_type.strip().lower()
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"auditoria_iam_run_{self._current_run_id}" if self._current_run_id is not None else "auditoria_iam_actual"

        if fmt == "pdf":
            default_name = f"{prefix}_{now_str}.pdf"
            file_filter = "Documento PDF (*.pdf);;Todos los archivos (*.*)"
        elif fmt in ("xlsx", "excel"):
            default_name = f"{prefix}_{now_str}.xlsx"
            file_filter = "Libro de Microsoft Excel (*.xlsx);;Todos los archivos (*.*)"
        elif fmt == "csv":
            default_name = f"{prefix}_{now_str}.csv"
            file_filter = "Archivo de valores separados por comas (*.csv);;Todos los archivos (*.*)"
        else:
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            f"Exportar Informe de Auditoría IAM ({fmt.upper()})",
            default_name,
            file_filter,
        )

        if not filepath:
            return

        try:
            saved_path = self._audit_service.export_audit_report(
                filepath=filepath,
                format_type=fmt,
                run_id=self._current_run_id,
                results=self._current_results,
                resources=self._current_resources,
                summary=self._current_summary,
            )
            self._set_banner_style("#16845B")
            self.banner_text.setText(
                f"✓  Informe {fmt.upper()} exportado exitosamente · Ruta: {saved_path}"
            )
        except Exception as exc:
            self._set_banner_style("#D64545")
            self.banner_text.setText(
                f"⚠  Error al exportar el informe {fmt.upper()} ({type(exc).__name__}): {exc}"
            )
