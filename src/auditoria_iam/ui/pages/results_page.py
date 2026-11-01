"""
Página de Resultados para el Sistema de Auditoría IAM.
Presenta el resumen cuantitativo de la última auditoría y la visualización tabular
detallada de los resultados reales generados por el motor de auditoría.
"""
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.auditoria_iam.audit.models import AuditResult


class ResultsPage(QWidget):
    """Pantalla para la visualización de resultados técnicos de auditoría."""

    # Mapeo de reglas a controles ISO/IEC 27001:2022
    RULE_TO_ISO = {
        "IAM-001": "5.15",
        "IAM-002": "5.16",
        "IAM-003": "5.18",
        "IAM-004": "8.5",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("results_page")
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # 1. Encabezado de la página
        title = QLabel("Resultados de Auditoría")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")

        subtitle = QLabel(
            "Visualización detallada de la evaluación de controles ISO/IEC 27001:2022 y hallazgos técnicos."
        )
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # 2. Tarjetas de Resumen Cuantitativo
        self.summary_container = QFrame()
        self.summary_container.setStyleSheet(
            "background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 14px;"
        )
        summary_grid = QGridLayout(self.summary_container)
        summary_grid.setSpacing(12)

        # Crear widgets de resumen
        self.lbl_total = self._create_summary_card(summary_grid, 0, "Total Evaluaciones", "0", "#38bdf8")
        self.lbl_conforme = self._create_summary_card(summary_grid, 1, "Conforme", "0", "#22c55e")
        self.lbl_hallazgo = self._create_summary_card(summary_grid, 2, "Hallazgo", "0", "#ef4444")
        self.lbl_no_evaluable = self._create_summary_card(summary_grid, 3, "No evaluable", "0", "#94a3b8")

        layout.addWidget(self.summary_container)

        # 3. Banner informativo de estado
        self.info_banner = QFrame()
        self.info_banner.setStyleSheet(
            "background-color: #0f172a; border-left: 4px solid #f59e0b; border-radius: 6px; padding: 12px;"
        )
        banner_layout = QVBoxLayout(self.info_banner)
        banner_layout.setContentsMargins(12, 8, 12, 8)

        self.banner_text = QLabel(
            "ℹ Todavía no se ha ejecutado ninguna auditoría en esta sesión.\n"
            "Seleccione 'Ejecutar auditoría' en el menú lateral para iniciar una evaluación técnica con el simulador de datos."
        )
        self.banner_text.setWordWrap(True)
        self.banner_text.setStyleSheet("color: #e2e8f0; font-size: 13px; line-height: 1.4;")
        banner_layout.addWidget(self.banner_text)
        layout.addWidget(self.info_banner)

        # 4. Estructura de tabla con las columnas requeridas
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

        self.results_table.setRowCount(0)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setStyleSheet(
            "background-color: #0f172a; alternate-background-color: #131d31; "
            "border: 1px solid #334155; border-radius: 6px; gridline-color: #1e293b; color: #f8fafc;"
        )

        layout.addWidget(self.results_table)

    def _create_summary_card(
        self, grid: QGridLayout, col: int, label_text: str, default_val: str, color_hex: str
    ) -> QLabel:
        """Crea un indicador métrico con etiqueta y valor grande."""
        card_widget = QWidget()
        card_layout = QVBoxLayout(card_widget)
        card_layout.setContentsMargins(8, 4, 8, 4)
        card_layout.setSpacing(2)

        title = QLabel(label_text)
        title.setStyleSheet("font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase;")

        val_label = QLabel(default_val)
        val_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color_hex};")

        card_layout.addWidget(title)
        card_layout.addWidget(val_label)
        grid.addWidget(card_widget, 0, col)
        return val_label

    def load_results(
        self,
        results: List[AuditResult],
        resources: List[Dict[str, Any]],
        summary: Dict[str, int],
    ) -> None:
        """
        Carga y visualiza los resultados reales de auditoría en la tabla y contadores de resumen.

        Args:
            results: Lista de instancias AuditResult generadas por AuditEngine.
            resources: Lista de recursos evaluados para enriquecer metadatos de visualización.
            summary: Diccionario con total, conforme, hallazgo y no_evaluable.
        """
        # 1. Actualizar indicadores numéricos de resumen
        self.lbl_total.setText(str(summary.get("total", len(results))))
        self.lbl_conforme.setText(str(summary.get("conforme", 0)))
        self.lbl_hallazgo.setText(str(summary.get("hallazgo", 0)))
        self.lbl_no_evaluable.setText(str(summary.get("no_evaluable", 0)))

        # 2. Actualizar banner de estado
        self.info_banner.setStyleSheet(
            "background-color: #0f172a; border-left: 4px solid #22c55e; border-radius: 6px; padding: 12px;"
        )
        self.banner_text.setText(
            f"✓ Mostrando resultados reales de la última ejecución. "
            f"Se evaluaron {len(resources)} recursos IAM frente a las 4 reglas técnicas "
            f"con un total de {len(results)} evaluaciones registradas."
        )

        # 3. Construir índice de recursos por ID
        resource_index: Dict[Any, Dict[str, Any]] = {
            r.get("id"): r for r in resources if "id" in r
        }

        # 4. Poblar la tabla de resultados
        self.results_table.setRowCount(len(results))

        for row_idx, res in enumerate(results):
            # Obtener datos del recurso evaluado
            res_meta = resource_index.get(res.resource_id, {})
            resource_name = res_meta.get("resource_key") or res_meta.get("display_name") or f"ID {res.resource_id}"
            resource_type = res_meta.get("resource_type", "IAM_RESOURCE")
            iso_control = self.RULE_TO_ISO.get(res.rule_code, "N/A")

            # Crear ítems de tabla
            item_resource = QTableWidgetItem(str(resource_name))
            item_type = QTableWidgetItem(str(resource_type))
            item_rule = QTableWidgetItem(str(res.rule_code))
            item_iso = QTableWidgetItem(f"ISO {iso_control}")
            item_status = QTableWidgetItem(str(res.result_status))
            item_justification = QTableWidgetItem(str(res.justification))

            # Estilo condicional según estado del resultado
            status_font = QFont()
            status_font.setBold(True)
            item_status.setFont(status_font)

            if res.result_status == "Conforme":
                item_status.setForeground(QColor("#22c55e"))
            elif res.result_status == "Hallazgo":
                item_status.setForeground(QColor("#ef4444"))
            else:  # No evaluable
                item_status.setForeground(QColor("#94a3b8"))

            # Deshabilitar edición en todas las celdas
            for item in (item_resource, item_type, item_rule, item_iso, item_status, item_justification):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            self.results_table.setItem(row_idx, 0, item_resource)
            self.results_table.setItem(row_idx, 1, item_type)
            self.results_table.setItem(row_idx, 2, item_rule)
            self.results_table.setItem(row_idx, 3, item_iso)
            self.results_table.setItem(row_idx, 4, item_status)
            self.results_table.setItem(row_idx, 5, item_justification)
