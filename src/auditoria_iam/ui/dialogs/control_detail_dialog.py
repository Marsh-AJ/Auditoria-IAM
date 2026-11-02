"""
Diálogo modal para la visualización detallada de un Control ISO/IEC 27001:2022.
Presenta objetivo, alcance técnico auditado en AWS IAM, criterios de evaluación,
interpretación de estados y delimitación formal de certificación.
"""
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.auditoria_iam.ui.controls_catalog import get_control_detail


class IsoControlDetailDialog(QDialog):
    """Diálogo modal interactivo para consultar el detalle de un control ISO 27001."""

    def __init__(self, control_code: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.control_code = control_code
        self.data = get_control_detail(control_code) or {}

        name = self.data.get("name", "Control de Seguridad")
        self.setWindowTitle(f"Detalle Técnico — Control ISO/IEC 27001:2022 {control_code}: {name}")
        self.resize(760, 680)
        self.setMinimumSize(600, 480)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 1. Encabezado con Badges y Título
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        iso_badge = QLabel(f"ISO/IEC 27001:2022 — {self.control_code}")
        iso_badge.setStyleSheet(
            "background-color: #0369a1; color: #f0f9ff; border-radius: 4px; "
            "padding: 4px 10px; font-weight: bold; font-size: 12px;"
        )

        rule_code = self.data.get("rule_code", "N/A")
        rule_badge = QLabel(f"Regla Técnica: {rule_code}")
        rule_badge.setStyleSheet(
            "background-color: #334155; color: #38bdf8; border-radius: 4px; "
            "padding: 4px 10px; font-weight: bold; font-size: 12px; font-family: monospace;"
        )

        header_layout.addWidget(iso_badge)
        header_layout.addWidget(rule_badge)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        title = QLabel(f"Control {self.control_code} — {self.data.get('name', '')}")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(title)

        ref_label = QLabel(self.data.get("reference", ""))
        ref_label.setStyleSheet("font-size: 12px; color: #64748b; font-style: italic;")
        layout.addWidget(ref_label)

        # Separador horizontal
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("color: #334155;")
        layout.addWidget(sep1)

        # 2. Descripción Informativa del Control
        sec_desc = self._create_section(
            "1. Descripción Informativa del Control",
            self.data.get("summary", ""),
            is_card=True,
            border_color="#38bdf8"
        )
        layout.addWidget(sec_desc)

        # 3. Objetivo de Seguridad
        sec_obj = self._create_section(
            "2. Objetivo de Seguridad",
            self.data.get("security_objective", ""),
            is_card=True,
            border_color="#0284c7"
        )
        layout.addWidget(sec_obj)

        # 4. Aspecto Técnico Auditado en AWS IAM
        sec_tech = self._create_section(
            "3. Aspecto Técnico Auditado en AWS IAM",
            self.data.get("technical_aspect", ""),
            is_card=True,
            border_color="#818cf8"
        )
        layout.addWidget(sec_tech)

        # 5. Criterios de Verificación de la Regla IAM
        criteria_box = QFrame()
        criteria_box.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 12px;")
        cb_layout = QVBoxLayout(criteria_box)
        cb_layout.setSpacing(10)

        cb_title = QLabel("4. Criterios y Verificaciones de la Regla IAM")
        cb_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")
        cb_layout.addWidget(cb_title)

        criteria_list = self.data.get("verification_criteria", [])
        for crit_code, crit_desc in criteria_list:
            crit_item = QHBoxLayout()
            crit_item.setSpacing(8)

            badge = QLabel(crit_code)
            badge.setStyleSheet(
                "background-color: #0f172a; color: #38bdf8; border: 1px solid #334155; "
                "border-radius: 4px; padding: 2px 8px; font-weight: bold; font-family: monospace; font-size: 11px;"
            )
            lbl_desc = QLabel(crit_desc)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("color: #e2e8f0; font-size: 12px; line-height: 1.4;")

            crit_item.addWidget(badge, alignment=Qt.AlignTop)
            crit_item.addWidget(lbl_desc, stretch=1)
            cb_layout.addLayout(crit_item)

        layout.addWidget(criteria_box)

        # 6. Significado de los Estados de Auditoría
        status_box = QFrame()
        status_box.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 12px;")
        sb_layout = QVBoxLayout(status_box)
        sb_layout.setSpacing(10)

        sb_title = QLabel("5. Significado de los Estados de Evaluación")
        sb_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")
        sb_layout.addWidget(sb_title)

        meanings = self.data.get("status_meanings", {})
        status_styles = {
            "Conforme": ("#22c55e", "#14532d"),
            "Hallazgo": ("#ef4444", "#7f1d1d"),
            "No evaluable": ("#f59e0b", "#78350f"),
        }

        for st_name, st_text in meanings.items():
            fg_col, bg_col = status_styles.get(st_name, ("#94a3b8", "#1e293b"))
            st_layout = QHBoxLayout()
            st_layout.setSpacing(8)

            st_badge = QLabel(f" {st_name} ")
            st_badge.setStyleSheet(
                f"background-color: {bg_col}; color: {fg_col}; border: 1px solid {fg_col}; "
                "border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 11px;"
            )
            st_desc = QLabel(st_text)
            st_desc.setWordWrap(True)
            st_desc.setStyleSheet("color: #cbd5e1; font-size: 12px; line-height: 1.3;")

            st_layout.addWidget(st_badge, alignment=Qt.AlignTop)
            st_layout.addWidget(st_desc, stretch=1)
            sb_layout.addLayout(st_layout)

        layout.addWidget(status_box)

        # 7. Información sobre el Alcance y Limitaciones
        scope_box = QFrame()
        scope_box.setStyleSheet(
            "background-color: #0f172a; border-left: 4px solid #f59e0b; "
            "border: 1px solid #334155; border-left-width: 4px; border-left-color: #f59e0b; "
            "border-radius: 6px; padding: 14px;"
        )
        scope_layout = QVBoxLayout(scope_box)
        scope_layout.setSpacing(6)

        scope_title = QLabel("⚠️ Alcance Técnico y Limitaciones de la Evaluación")
        scope_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #f59e0b;")
        scope_layout.addWidget(scope_title)

        scope_text = QLabel(
            self.data.get("scope_notice", "")
            + "\n\nNota formal: Los resultados generados por este prototipo de investigación no representan una "
            "certificación ISO/IEC 27001 ni sustituyen una auditoría integral de cumplimiento organizacional."
        )
        scope_text.setWordWrap(True)
        scope_text.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.4;")
        scope_layout.addWidget(scope_text)

        layout.addWidget(scope_box)
        layout.addStretch()

        scroll_area.setWidget(content)
        main_layout.addWidget(scroll_area)

        # Barra inferior de cierre
        btn_close = QPushButton("Cerrar")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(
            "background-color: #1e293b; color: #f8fafc; border: 1px solid #475569; "
            "border-radius: 6px; padding: 8px 24px; font-weight: 500; font-size: 13px;"
        )
        btn_close.clicked.connect(self.accept)

        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        actions_layout.addWidget(btn_close)
        main_layout.addLayout(actions_layout)

    def _create_section(
        self, title_text: str, content_text: str, is_card: bool = False, border_color: str = "#334155"
    ) -> QWidget:
        box = QFrame()
        if is_card:
            box.setStyleSheet(
                f"background-color: #1e293b; border-left: 3px solid {border_color}; "
                "border-top: 1px solid #334155; border-right: 1px solid #334155; border-bottom: 1px solid #334155; "
                "border-radius: 6px; padding: 12px;"
            )
        b_layout = QVBoxLayout(box)
        b_layout.setContentsMargins(12, 10, 12, 10)
        b_layout.setSpacing(6)

        t_lbl = QLabel(title_text)
        t_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc;")
        b_layout.addWidget(t_lbl)

        c_lbl = QLabel(content_text)
        c_lbl.setWordWrap(True)
        c_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px; line-height: 1.4;")
        b_layout.addWidget(c_lbl)

        return box

