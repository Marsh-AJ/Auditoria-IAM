"""
Página de Historial de Auditorías para el Sistema de Auditoría IAM.
Permite consultar cronológicamente las ejecuciones previas persistidas en MySQL Server,
transferir los resultados a la vista de detalle y exportar informes históricos
en formatos PDF, Excel (XLSX) y CSV dentro de una tarjeta empresarial limpia.
"""
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
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
from src.auditoria_iam.ui.icons import render_svg_icon


class HistoryPage(QWidget):
    """Pantalla para la consulta del histórico de ejecuciones, trazabilidad y exportación."""

    run_selected = Signal(int)

    def __init__(
        self,
        parent: QWidget | None = None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("history_page")
        self._audit_service = audit_service or AuditService()
        self._init_ui()

    def _init_ui(self) -> None:
        self.setStyleSheet("QWidget#history_page { background-color: #F5F7FA; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(16)

        # 1. Encabezado de la página con botón de actualización a la derecha
        header_row = QHBoxLayout()
        header_row.setSpacing(16)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)

        title = QLabel("Historial de Auditorías")
        title.setProperty("class", "page_title")

        subtitle = QLabel(
            "Registro cronológico de evaluaciones técnicas almacenadas en MySQL Server, trazabilidad y exportación."
        )
        subtitle.setProperty("class", "page_subtitle")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col, stretch=1)

        self.btn_refresh = QPushButton("  Actualizar historial")
        self.btn_refresh.setProperty("class", "secondary_button")
        self.btn_refresh.setIcon(render_svg_icon("refresh", color="#334155", size=15))
        self.btn_refresh.setIconSize(QSize(15, 15))
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_history)
        header_row.addWidget(self.btn_refresh, alignment=Qt.AlignVCenter)

        layout.addLayout(header_row)

        # 2. Franja discreta de estado de la consulta histórica
        self.banner = QFrame()
        self.banner.setObjectName("history_status_banner")
        self._set_banner_style("#294F78")
        banner_layout = QVBoxLayout(self.banner)
        banner_layout.setContentsMargins(16, 10, 16, 10)

        self.banner_text = QLabel(
            "ℹ  Haga clic en 'Actualizar historial' para consultar las ejecuciones persistidas en MySQL."
        )
        self.banner_text.setWordWrap(True)
        self.banner_text.setStyleSheet("color: #334155; font-size: 12.5px; font-weight: 500;")
        banner_layout.addWidget(self.banner_text)
        layout.addWidget(self.banner)

        # 3. Tarjeta de tabla estilo Meridian ERP con barra de acciones integrada
        table_card = QFrame()
        table_card.setProperty("class", "card")
        tc_layout = QVBoxLayout(table_card)
        tc_layout.setContentsMargins(0, 14, 0, 6)
        tc_layout.setSpacing(10)

        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(20, 0, 20, 4)
        toolbar_row.setSpacing(8)

        lbl_card_title = QLabel("Ejecuciones Registradas")
        lbl_card_title.setProperty("class", "card_header_title")
        toolbar_row.addWidget(lbl_card_title)
        toolbar_row.addStretch()

        lbl_export = QLabel("Exportar seleccionada:")
        lbl_export.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600; margin-right: 4px;")
        toolbar_row.addWidget(lbl_export)

        self.btn_export_pdf = QPushButton("  PDF")
        self.btn_export_pdf.setProperty("class", "secondary_button")
        self.btn_export_pdf.setIcon(render_svg_icon("file_export", color="#172B46", disabled_color="#94A3B8", size=14))
        self.btn_export_pdf.setIconSize(QSize(14, 14))
        self.btn_export_pdf.setEnabled(False)
        self.btn_export_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_export_pdf.clicked.connect(lambda: self._export_selected_run("pdf"))
        toolbar_row.addWidget(self.btn_export_pdf)

        self.btn_export_excel = QPushButton("  Excel")
        self.btn_export_excel.setProperty("class", "secondary_button")
        self.btn_export_excel.setIcon(render_svg_icon("file_export", color="#16845B", disabled_color="#94A3B8", size=14))
        self.btn_export_excel.setIconSize(QSize(14, 14))
        self.btn_export_excel.setEnabled(False)
        self.btn_export_excel.setCursor(Qt.PointingHandCursor)
        self.btn_export_excel.clicked.connect(lambda: self._export_selected_run("xlsx"))
        toolbar_row.addWidget(self.btn_export_excel)

        self.btn_export_csv = QPushButton("  CSV")
        self.btn_export_csv.setProperty("class", "secondary_button")
        self.btn_export_csv.setIcon(render_svg_icon("file_export", color="#294F78", disabled_color="#94A3B8", size=14))
        self.btn_export_csv.setIconSize(QSize(14, 14))
        self.btn_export_csv.setEnabled(False)
        self.btn_export_csv.setCursor(Qt.PointingHandCursor)
        self.btn_export_csv.clicked.connect(lambda: self._export_selected_run("csv"))
        toolbar_row.addWidget(self.btn_export_csv)

        self.btn_view_results = QPushButton("Ver resultados  →")
        self.btn_view_results.setProperty("class", "primary_button")
        self.btn_view_results.setEnabled(False)
        self.btn_view_results.setCursor(Qt.PointingHandCursor)
        self.btn_view_results.clicked.connect(self._on_view_results_clicked)
        toolbar_row.addWidget(self.btn_view_results)

        tc_layout.addLayout(toolbar_row)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "ID Ejecución",
            "Fecha y Hora",
            "Fuente Utilizada",
            "Estado",
            "Hallazgos Detectados",
            "Resumen de Ejecución",
        ])
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setRowCount(0)

        self.history_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.history_table.cellDoubleClicked.connect(lambda r, c: self._on_view_results_clicked())

        tc_layout.addWidget(self.history_table, stretch=1)
        layout.addWidget(table_card, stretch=1)

    def _set_banner_style(self, accent_hex: str) -> None:
        self.banner.setStyleSheet(
            f"QFrame#history_status_banner {{ background-color: #FFFFFF; border: 1px solid #E5E9F0; "
            f"border-left: 3px solid {accent_hex}; border-radius: 10px; }}"
        )

    def refresh_history(self) -> None:
        """Consulta y actualiza la lista de ejecuciones guardadas en MySQL."""
        self._set_selection_actions_enabled(False)

        try:
            runs = self._audit_service.get_audit_history()

            if not runs:
                self.history_table.setRowCount(0)
                self._set_banner_style("#D49A32")
                self.banner_text.setText(
                    "ℹ  No se han registrado auditorías previas en la base de datos MySQL."
                )
                return

            self._set_banner_style("#16845B")
            self.banner_text.setText(
                f"✓  Se encontraron {len(runs)} ejecuciones almacenadas en MySQL. "
                "Seleccione una fila para consultar su detalle o exportar el informe."
            )

            self.history_table.setRowCount(len(runs))

            for row_idx, r in enumerate(runs):
                item_id = QTableWidgetItem(f"#{r.get('id', '')}")
                item_id.setTextAlignment(Qt.AlignCenter)
                id_font = QFont()
                id_font.setBold(True)
                item_id.setFont(id_font)
                item_id.setForeground(QColor("#0F172A"))

                item_date = QTableWidgetItem(str(r.get("execution_date", "")))
                item_date.setTextAlignment(Qt.AlignCenter)

                item_source = QTableWidgetItem(str(r.get("source_type", "")))
                item_source.setTextAlignment(Qt.AlignCenter)

                status_val = str(r.get("status", ""))
                item_status = QTableWidgetItem(status_val)
                item_status.setTextAlignment(Qt.AlignCenter)
                st_font = QFont()
                st_font.setBold(True)
                item_status.setFont(st_font)
                if status_val.lower() in ("completada", "exitosa", "completed"):
                    item_status.setForeground(QColor("#16845B"))
                    item_status.setBackground(QColor("#ECFDF5"))

                findings_cnt = int(r.get("total_findings", 0) or 0)
                item_findings = QTableWidgetItem(str(findings_cnt))
                item_findings.setTextAlignment(Qt.AlignCenter)
                item_findings.setFont(st_font)
                item_findings.setForeground(QColor("#D64545" if findings_cnt > 0 else "#16845B"))

                item_summary = QTableWidgetItem(str(r.get("summary", "")))
                item_summary.setToolTip(str(r.get("summary", "")))

                for itm in (item_id, item_date, item_source, item_status, item_findings, item_summary):
                    itm.setFlags(itm.flags() & ~Qt.ItemIsEditable)

                self.history_table.setItem(row_idx, 0, item_id)
                self.history_table.setItem(row_idx, 1, item_date)
                self.history_table.setItem(row_idx, 2, item_source)
                self.history_table.setItem(row_idx, 3, item_status)
                self.history_table.setItem(row_idx, 4, item_findings)
                self.history_table.setItem(row_idx, 5, item_summary)

            self.history_table.resizeRowsToContents()

        except Exception as exc:
            self.history_table.setRowCount(0)
            self._set_banner_style("#D64545")
            self.banner_text.setText(
                f"⚠  No se pudo conectar a la base de datos MySQL para consultar el historial ({type(exc).__name__}). "
                "Verifique que el servidor MySQL se encuentre en ejecución."
            )

    def _set_selection_actions_enabled(self, enabled: bool) -> None:
        self.btn_view_results.setEnabled(enabled)
        self.btn_export_pdf.setEnabled(enabled)
        self.btn_export_excel.setEnabled(enabled)
        self.btn_export_csv.setEnabled(enabled)

    def _on_selection_changed(self) -> None:
        has_selection = len(self.history_table.selectedItems()) > 0
        self._set_selection_actions_enabled(has_selection)

    def _get_selected_run_id(self) -> Optional[int]:
        selected_rows = self.history_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        item = self.history_table.item(row, 0)
        if item is None:
            return None
        raw_id = item.text().replace("#", "").strip()
        try:
            return int(raw_id)
        except ValueError:
            return None

    def _on_view_results_clicked(self) -> None:
        run_id = self._get_selected_run_id()
        if run_id is not None:
            self.run_selected.emit(run_id)

    def _export_selected_run(self, format_type: str) -> None:
        run_id = self._get_selected_run_id()
        if run_id is None:
            self.show_error_message("Seleccione una ejecución de auditoría de la tabla antes de exportar.")
            return

        fmt = format_type.strip().lower()
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = "xlsx" if fmt in ("xlsx", "excel") else fmt
        default_name = f"auditoria_iam_run_{run_id}_{now_str}.{ext}"

        if fmt == "pdf":
            file_filter = "Documento PDF (*.pdf);;Todos los archivos (*.*)"
        elif fmt in ("xlsx", "excel"):
            file_filter = "Libro de Microsoft Excel (*.xlsx);;Todos los archivos (*.*)"
        elif fmt == "csv":
            file_filter = "Archivo de valores separados por comas (*.csv);;Todos los archivos (*.*)"
        else:
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            f"Exportar Informe Histórico #{run_id} ({fmt.upper()})",
            default_name,
            file_filter,
        )

        if not filepath:
            return

        try:
            saved_path = self._audit_service.export_audit_report(
                filepath=filepath,
                format_type=fmt,
                run_id=run_id,
            )
            self._set_banner_style("#16845B")
            self.banner_text.setText(
                f"✓  Informe {fmt.upper()} de la ejecución #{run_id} exportado exitosamente · Ruta: {saved_path}"
            )
        except Exception as exc:
            self.show_error_message(f"Error al exportar el informe {fmt.upper()} ({type(exc).__name__}): {exc}")

    def show_error_message(self, message: str) -> None:
        self._set_banner_style("#D64545")
        self.banner_text.setText(f"⚠  {message}")
