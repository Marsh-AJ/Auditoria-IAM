"""
Página de Inicio para la aplicación de escritorio del Sistema de Auditoría IAM.
Presenta la descripción formal del sistema, controles ISO 27001 evaluados y fuentes disponibles.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class HomePage(QWidget):
    """Vista principal de bienvenida y resumen de alcance del sistema."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("home_page")
        self._init_ui()

    def _init_ui(self) -> None:
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 1. Encabezado principal
        header_layout = QVBoxLayout()
        header_layout.setSpacing(6)

        title = QLabel("Sistema de Auditoría IAM")
        title.setProperty("class", "page_title")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #38bdf8;")

        subtitle = QLabel(
            "Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube "
            "basado en el estándar ISO/IEC 27001 para UPHARVEN C.A."
        )
        subtitle.setProperty("class", "page_subtitle")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 14px; color: #94a3b8; line-height: 1.4;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

        # 2. Banner de estado del sistema
        status_banner = QFrame()
        status_banner.setProperty("class", "card")
        status_banner.setStyleSheet(
            "background-color: #1e293b; border-left: 4px solid #10b981; border-radius: 6px; padding: 16px;"
        )
        status_layout = QHBoxLayout(status_banner)
        status_layout.setContentsMargins(16, 12, 16, 12)

        status_text = QLabel(
            "✓ Interfaz inicial disponible. Seleccione 'Ejecutar auditoría' en el menú lateral para iniciar una nueva evaluación técnica."
        )
        status_text.setStyleSheet("color: #e2e8f0; font-size: 13px; font-weight: 500;")
        status_layout.addWidget(status_text)
        layout.addWidget(status_banner)

        # 3. Sección: Controles ISO/IEC 27001:2022 Evaluados
        controls_title = QLabel("Controles ISO/IEC 27001:2022 Evaluados")
        controls_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(controls_title)

        controls_grid = QGridLayout()
        controls_grid.setSpacing(16)

        controls_data = [
            ("5.15", "Control de acceso", "IAM-001", "Verificación de correspondencia de grupos asignados y relaciones de confianza en roles."),
            ("5.16", "Gestión de identidades", "IAM-002", "Identificación de identidades con actividad inactiva superior al umbral configurable de 90 días, mediante los metadatos disponibles."),
            ("5.18", "Derechos de acceso", "IAM-003", "Análisis sintáctico estricto de políticas JSON para prevenir patrones de permisos excesivamente amplios."),
            ("8.5", "Autenticación segura", "IAM-004", "Exigencia de autenticación multifactor (MFA) obligatoria en usuarios activos de la plataforma.")
        ]

        for idx, (iso_code, name, rule_code, desc) in enumerate(controls_data):
            card = QFrame()
            card.setProperty("class", "card")
            card.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 14px;")
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(6)

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

            card_layout.addLayout(badge_layout)
            card_layout.addWidget(ctrl_name)
            card_layout.addWidget(ctrl_desc)
            card_layout.addStretch()

            row = idx // 2
            col = idx % 2
            controls_grid.addWidget(card, row, col)

        layout.addLayout(controls_grid)

        # 4. Sección: Fuentes de Información Disponibles
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

