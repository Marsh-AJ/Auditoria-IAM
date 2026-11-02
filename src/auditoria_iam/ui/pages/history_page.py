"""
Página de Historial de Auditorías para el Sistema de Auditoría IAM.
Permite consultar cronológicamente las ejecuciones previas persistidas en MySQL Server,
visualizar sus métricas y cargar los resultados históricos en la interfaz.
"""
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
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


class HistoryPage(QWidget):
    """Pantalla para la consulta del histórico de ejecuciones y trazabilidad."""

    # Señal emitida al solicitar visualizar los resultados de una ejecución histórica (run_id)
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # 1. Encabezado de la página
        title = QLabel("Historial de Auditorías")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")

        subtitle = QLabel(
            "Registro cronológico de evaluaciones técnicas guardadas en MySQL Server y trazabilidad histórica."
        )
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # 2. Barra de acciones (Actualizar / Ver Resultados)
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        self.btn_refresh = QPushButton("Actualizar historial 🔄")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setStyleSheet(
            "background-color: #1e293b; color: #f8fafc; border: 1px solid #334155; "
            "border-radius: 6px; padding: 8px 16px; font-weight: 500; font-size: 12px;"
        )
        self.btn_refresh.clicked.connect(self.refresh_history)

        self.btn_view_results = QPushButton("Ver resultados de la ejecución seleccionada →")
        self.btn_view_results.setEnabled(False)
        self.btn_view_results.setCursor(Qt.PointingHandCursor)
        self.btn_view_results.setStyleSheet(
            "background-color: #0284c7; color: #ffffff; border: none; "
            "border-radius: 6px; padding: 8px 18px; font-weight: bold; font-size: 12px;"
        )
        self.btn_view_results.clicked.connect(self._on_view_results_clicked)

        actions_layout.addWidget(self.btn_refresh)
        actions_layout.addWidget(self.btn_view_results)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        # 3. Banner de estado de la consulta histórica
        self.banner = QFrame()
        self.banner.setStyleSheet(
            "background-color: #1e293b; border-left: 4px solid #38bdf8; border-radius: 6px; padding: 12px;"
        )
        banner_layout = QVBoxLayout(self.banner)
        banner_layout.setContentsMargins(12, 8, 12, 8)

        self.banner_text = QLabel(
            "ℹ No se han consultado las ejecuciones en esta sesión. "
            "Haga clic en 'Actualizar historial 🔄' para consultar los registros persistidos en MySQL."
        )
        self.banner_text.setWordWrap(True)
        self.banner_text.setStyleSheet("color: #e2e8f0; font-size: 13px; line-height: 1.4;")
        banner_layout.addWidget(self.banner_text)
        layout.addWidget(self.banner)

        # 4. Tabla de histórico
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

        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setRowCount(0)
        self.history_table.setStyleSheet(
            "background-color: #0f172a; alternate-background-color: #131d31; "
            "border: 1px solid #334155; border-radius: 6px; gridline-color: #1e293b; color: #f8fafc;"
        )

        self.history_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.history_table.cellDoubleClicked.connect(lambda r, c: self._on_view_results_clicked())

        layout.addWidget(self.history_table)

    def refresh_history(self) -> None:
        """Consulta y actualiza la lista de ejecuciones guardadas en MySQL."""
        self.btn_view_results.setEnabled(False)

        try:
            runs = self._audit_service.get_audit_history()

            if not runs:
                self.history_table.setRowCount(0)
                self.banner.setStyleSheet(
                    "background-color: #0f172a; border-left: 4px solid #f59e0b; border-radius: 6px; padding: 12px;"
                )
                self.banner_text.setText(
                    "ℹ No se han registrado auditorías previas en la base de datos MySQL."
                )
                return

            self.banner.setStyleSheet(
                "background-color: #0f172a; border-left: 4px solid #22c55e; border-radius: 6px; padding: 12px;"
            )
            self.banner_text.setText(
                f"✓ Se encontraron {len(runs)} ejecuciones de auditoría guardadas en MySQL. "
                "Seleccione una fila y pulse 'Ver resultados' para consultar su detalle."
            )

            self.history_table.setRowCount(len(runs))

            for row_idx, r in enumerate(runs):
                item_id = QTableWidgetItem(f"#{r.get('id', '')}")
                item_date = QTableWidgetItem(str(r.get("execution_date", "")))
                item_source = QTableWidgetItem(str(r.get("source_type", "")))
                item_status = QTableWidgetItem(str(r.get("status", "")))
                item_findings = QTableWidgetItem(str(r.get("total_findings", 0)))
                item_summary = QTableWidgetItem(str(r.get("summary", "")))

                # Formato no editable
                for itm in (item_id, item_date, item_source, item_status, item_findings, item_summary):
                    itm.setFlags(itm.flags() & ~Qt.ItemIsEditable)

                self.history_table.setItem(row_idx, 0, item_id)
                self.history_table.setItem(row_idx, 1, item_date)
                self.history_table.setItem(row_idx, 2, item_source)
                self.history_table.setItem(row_idx, 3, item_status)
                self.history_table.setItem(row_idx, 4, item_findings)
                self.history_table.setItem(row_idx, 5, item_summary)

        except Exception as exc:
            self.history_table.setRowCount(0)
            self.banner.setStyleSheet(
                "background-color: #0f172a; border-left: 4px solid #ef4444; border-radius: 6px; padding: 12px;"
            )
            self.banner_text.setText(
                f"⚠️ No se pudo conectar a la base de datos MySQL para consultar el historial ({type(exc).__name__}). "
                "Verifique que el servidor MySQL se encuentre en ejecución y configurado correctamente."
            )

    def _on_selection_changed(self) -> None:
        """Habilita o deshabilita el botón de ver resultados según la selección activa."""
        has_selection = len(self.history_table.selectedItems()) > 0
        self.btn_view_results.setEnabled(has_selection)

    def _on_view_results_clicked(self) -> None:
        """Emite la señal de ejecución seleccionada para transferir los resultados a ResultsPage."""
        selected_rows = self.history_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        item = self.history_table.item(row, 0)
        if item is not None:
            # Remover '#' del prefijo si existe
            raw_id = item.text().replace("#", "").strip()
            try:
                run_id = int(raw_id)
                self.run_selected.emit(run_id)
            except ValueError:
                pass

    def show_error_message(self, message: str) -> None:
        """Muestra un mensaje de error visible y controlado en el banner de la página de historial."""
        self.banner.setStyleSheet(
            "background-color: #0f172a; border-left: 4px solid #ef4444; border-radius: 6px; padding: 12px;"
        )
        self.banner_text.setText(f"⚠️ {message}")
