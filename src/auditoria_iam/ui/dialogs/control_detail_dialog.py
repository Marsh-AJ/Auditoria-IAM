"""
Diálogo modal para la visualización detallada de un Control ISO/IEC 27001:2022.
Presenta objetivo, alcance técnico auditado en AWS IAM, criterios de evaluación,
interpretación de estados y delimitación formal de certificación mediante tarjetas limpias.
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
from src.auditoria_iam.ui.icons import create_icon_badge


class IsoControlDetailDialog(QDialog):
    """Diálogo modal interactivo para consultar el detalle de un control ISO 27001."""

    def __init__(self, control_code: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.control_code = control_code
        self.data = get_control_detail(control_code) or {}

        name = self.data.get("name", "Control de Seguridad")
        self.setWindowTitle(f"Detalle Técnico — Control ISO/IEC 27001:2022 {control_code}: {name}")
        self.resize(780, 690)
        self.setMinimumSize(620, 480)
        self.setModal(True)
        self.setObjectName("iso_detail_dialog")
        self.setStyleSheet(
            "QDialog#iso_detail_dialog { background-color: #F5F7FA; color: #0F172A; } "
            "QLabel { background-color: transparent; border: none; }"
        )

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 16)
        main_layout.setSpacing(12)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        content = QWidget()
        content.setObjectName("iso_modal_canvas")
        content.setStyleSheet("QWidget#iso_modal_canvas { background-color: #F5F7FA; }")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 6, 12, 12)
        layout.setSpacing(14)

        # 1. Tarjeta de encabezado principal
        hero_card = QFrame()
        hero_card.setObjectName("hero_card")
        hero_card.setStyleSheet(
            "QFrame#hero_card { background-color: #FFFFFF; border: 1px solid #E5E9F0; border-radius: 12px; }"
        )
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(20, 18, 20, 18)
        hero_layout.setSpacing(14)

        hero_left = QVBoxLayout()
        hero_left.setSpacing(6)

        badges_row = QHBoxLayout()
        badges_row.setSpacing(8)

        iso_badge = QLabel(f"ISO/IEC 27001:2022 — {self.control_code}")
        iso_badge.setStyleSheet(
            "background-color: #EEF4FF; color: #1E40AF; border: 1px solid #DBEAFE; "
            "border-radius: 6px; padding: 3px 10px; font-weight: 700; font-size: 11.5px;"
        )

        rule_code = self.data.get("rule_code", "N/A")
        rule_badge = QLabel(f"Regla Técnica: {rule_code}")
        rule_badge.setStyleSheet(
            "background-color: #F8FAFC; color: #475569; border: 1px solid #E2E8F0; "
            "border-radius: 6px; padding: 3px 10px; font-weight: 700; font-size: 11.5px; font-family: 'Consolas', monospace;"
        )

        badges_row.addWidget(iso_badge)
        badges_row.addWidget(rule_badge)
        badges_row.addStretch()
        hero_left.addLayout(badges_row)

        title = QLabel(f"Control {self.control_code} — {self.data.get('name', '')}")
        title.setStyleSheet("font-size: 19px; font-weight: 700; color: #0F172A;")
        hero_left.addWidget(title)

        ref_label = QLabel(self.data.get("reference", ""))
        ref_label.setStyleSheet("font-size: 12px; color: #64748B;")
        hero_left.addWidget(ref_label)

        hero_icon = create_icon_badge(
            "shield_check",
            fg_color="#172B46",
            bg_color="#F8FAFC",
            border_color="#E2E8F0",
            box_size=42,
            icon_size=20,
            radius=10,
        )

        hero_layout.addLayout(hero_left, stretch=1)
        hero_layout.addWidget(hero_icon, alignment=Qt.AlignTop)
        layout.addWidget(hero_card)

        # 2. Secciones descriptivas en tarjetas limpias
        layout.addWidget(
            self._create_section(
                "sec_desc",
                "1. Descripción Informativa del Control",
                self.data.get("summary", ""),
            )
        )
        layout.addWidget(
            self._create_section(
                "sec_obj",
                "2. Objetivo de Seguridad",
                self.data.get("security_objective", ""),
            )
        )
        layout.addWidget(
            self._create_section(
                "sec_tech",
                "3. Aspecto Técnico Auditado en AWS IAM",
                self.data.get("technical_aspect", ""),
            )
        )

        # 3. Criterios de Verificación de la Regla IAM
        criteria_box = QFrame()
        criteria_box.setObjectName("criteria_card")
        criteria_box.setStyleSheet(
            "QFrame#criteria_card { background-color: #FFFFFF; border: 1px solid #E5E9F0; border-radius: 12px; }"
        )
        cb_layout = QVBoxLayout(criteria_box)
        cb_layout.setContentsMargins(20, 16, 20, 16)
        cb_layout.setSpacing(10)

        cb_title = QLabel("4. Criterios y Verificaciones de la Regla IAM")
        cb_title.setStyleSheet("font-size: 13.5px; font-weight: 700; color: #0F172A;")
        cb_layout.addWidget(cb_title)

        for crit_code, crit_desc in self.data.get("verification_criteria", []):
            crit_item = QHBoxLayout()
            crit_item.setSpacing(10)

            badge = QLabel(crit_code)
            badge.setStyleSheet(
                "background-color: #F8FAFC; color: #172B46; border: 1px solid #D8E0EA; "
                "border-radius: 5px; padding: 2px 8px; font-weight: 700; font-family: 'Consolas', monospace; font-size: 11px;"
            )
            lbl_desc = QLabel(crit_desc)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("color: #334155; font-size: 12.5px; line-height: 1.4;")

            crit_item.addWidget(badge, alignment=Qt.AlignTop)
            crit_item.addWidget(lbl_desc, stretch=1)
            cb_layout.addLayout(crit_item)

        layout.addWidget(criteria_box)

        # 4. Significado de los Estados de Evaluación
        status_box = QFrame()
        status_box.setObjectName("status_card")
        status_box.setStyleSheet(
            "QFrame#status_card { background-color: #FFFFFF; border: 1px solid #E5E9F0; border-radius: 12px; }"
        )
        sb_layout = QVBoxLayout(status_box)
        sb_layout.setContentsMargins(20, 16, 20, 16)
        sb_layout.setSpacing(10)

        sb_title = QLabel("5. Significado de los Estados de Evaluación")
        sb_title.setStyleSheet("font-size: 13.5px; font-weight: 700; color: #0F172A;")
        sb_layout.addWidget(sb_title)

        status_styles = {
            "Conforme": ("#16845B", "#ECFDF5", "#A7F3D0"),
            "Hallazgo": ("#D64545", "#FEF2F2", "#FECACA"),
            "No evaluable": ("#B45309", "#FFFBEB", "#FDE68A"),
        }

        for st_name, st_text in self.data.get("status_meanings", {}).items():
            fg_col, bg_col, bdr_col = status_styles.get(st_name, ("#64748B", "#F8FAFC", "#E2E8F0"))
            st_layout = QHBoxLayout()
            st_layout.setSpacing(10)

            st_badge = QLabel(f" {st_name} ")
            st_badge.setFixedWidth(98)
            st_badge.setAlignment(Qt.AlignCenter)
            st_badge.setStyleSheet(
                f"background-color: {bg_col}; color: {fg_col}; border: 1px solid {bdr_col}; "
                "border-radius: 6px; padding: 3px 8px; font-weight: 700; font-size: 11px;"
            )
            st_desc = QLabel(st_text)
            st_desc.setWordWrap(True)
            st_desc.setStyleSheet("color: #334155; font-size: 12.5px; line-height: 1.35;")

            st_layout.addWidget(st_badge, alignment=Qt.AlignTop)
            st_layout.addWidget(st_desc, stretch=1)
            sb_layout.addLayout(st_layout)

        layout.addWidget(status_box)

        # 5. Alcance y Limitaciones
        scope_box = QFrame()
        scope_box.setObjectName("scope_card")
        scope_box.setStyleSheet(
            "QFrame#scope_card { background-color: #FFFFFF; border: 1px solid #E5E9F0; "
            "border-left: 3px solid #D49A32; border-radius: 12px; }"
        )
        scope_layout = QVBoxLayout(scope_box)
        scope_layout.setContentsMargins(20, 14, 20, 14)
        scope_layout.setSpacing(6)

        scope_title = QLabel("Alcance Técnico y Limitaciones de la Evaluación")
        scope_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #B45309;")
        scope_layout.addWidget(scope_title)

        scope_text = QLabel(
            self.data.get("scope_notice", "")
            + "\n\nNota académica: Los resultados generados por este prototipo no representan una "
            "certificación ISO/IEC 27001 ni sustituyen una auditoría organizacional integral."
        )
        scope_text.setWordWrap(True)
        scope_text.setStyleSheet("color: #64748B; font-size: 12px; line-height: 1.4;")
        scope_layout.addWidget(scope_text)

        layout.addWidget(scope_box)
        layout.addStretch()

        scroll_area.setWidget(content)
        main_layout.addWidget(scroll_area)

        # Barra inferior de cierre
        btn_close = QPushButton("Cerrar ventana")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(
            "QPushButton { background-color: #172B46; color: #FFFFFF; border: none; "
            "border-radius: 8px; padding: 8px 22px; font-weight: 600; font-size: 12.5px; } "
            "QPushButton:hover { background-color: #223D63; }"
        )
        btn_close.clicked.connect(self.accept)

        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(8, 2, 12, 0)
        actions_layout.addStretch()
        actions_layout.addWidget(btn_close)
        main_layout.addLayout(actions_layout)

    @staticmethod
    def _create_section(obj_name: str, title_text: str, content_text: str) -> QFrame:
        box = QFrame()
        box.setObjectName(obj_name)
        box.setStyleSheet(
            f"QFrame#{obj_name} {{ background-color: #FFFFFF; border: 1px solid #E5E9F0; border-radius: 12px; }}"
        )
        b_layout = QVBoxLayout(box)
        b_layout.setContentsMargins(20, 14, 20, 14)
        b_layout.setSpacing(6)

        t_lbl = QLabel(title_text)
        t_lbl.setStyleSheet("font-size: 13.5px; font-weight: 700; color: #0F172A;")
        b_layout.addWidget(t_lbl)

        c_lbl = QLabel(content_text)
        c_lbl.setWordWrap(True)
        c_lbl.setStyleSheet("color: #334155; font-size: 12.5px; line-height: 1.45;")
        b_layout.addWidget(c_lbl)

        return box
