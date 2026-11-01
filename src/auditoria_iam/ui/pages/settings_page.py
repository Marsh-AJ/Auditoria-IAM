"""
Página de Configuración para el Sistema de Auditoría IAM.
Presenta las secciones visuales de configuración sin exponer credenciales ni mutar .env.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class SettingsPage(QWidget):
    """Pantalla para la previsualización y gestión de parámetros de configuración del sistema."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("settings_page")
        self._init_ui()

    def _init_ui(self) -> None:
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 1. Encabezado de la página
        title = QLabel("Configuración del Sistema")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")

        subtitle = QLabel(
            "Parámetros operativos de evaluación y preferencias de ejecución de auditorías IAM."
        )
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Banner de advertencia de seguridad / alcance
        banner = QFrame()
        banner.setStyleSheet(
            "background-color: #1e293b; border-left: 4px solid #38bdf8; border-radius: 6px; padding: 12px;"
        )
        b_layout = QVBoxLayout(banner)
        b_text = QLabel(
            "ℹ En esta entrega estructural, los controles de configuración se presentan en modo demostrativo "
            "y no modifican el archivo .env, la base de datos ni credenciales del sistema."
        )
        b_text.setWordWrap(True)
        b_text.setStyleSheet("color: #cbd5e1; font-size: 12px; line-height: 1.4;")
        b_layout.addWidget(b_text)
        layout.addWidget(banner)

        # 2. Sección: Fuente de Información
        source_group = self._create_section_card(
            title="Fuente de Información Predeterminada",
            description="Configuración de la fuente predeterminada para nuevas sesiones de auditoría."
        )
        sg_layout = QVBoxLayout(source_group)

        source_combo = QComboBox()
        source_combo.addItem("Simulador de Datos Local (Recomendado para pruebas)", "simulador")
        source_combo.addItem("Adaptador AWS IAM (Boto3)", "aws")
        source_combo.setStyleSheet(
            "background-color: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 8px 12px; color: #f8fafc;"
        )
        sg_layout.addWidget(QLabel("Fuente primaria de auditoría:"))
        sg_layout.addWidget(source_combo)
        layout.addWidget(source_group)

        # 3. Sección: Configuración General
        general_group = self._create_section_card(
            title="Configuración General de Auditoría",
            description="Umbrales y criterios técnicos conforme a la norma ISO/IEC 27001:2022."
        )
        gg_layout = QGridLayout(general_group)
        gg_layout.setSpacing(12)

        gg_layout.addWidget(QLabel("Umbral de inactividad de credenciales (Control 5.16):"), 0, 0)
        inactivity_input = QLineEdit("90")
        inactivity_input.setReadOnly(True)
        inactivity_input.setStyleSheet(
            "background-color: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 6px 12px; color: #94a3b8; max-width: 80px;"
        )
        gg_layout.addWidget(inactivity_input, 0, 1)
        gg_layout.addWidget(QLabel("días (parámetro definido para el prototipo)"), 0, 2)

        gg_layout.addWidget(QLabel("Nivel de severidad para permisos irrestrictos (Control 5.18):"), 1, 0)
        severity_label = QLabel("CRÍTICA")
        severity_label.setStyleSheet("color: #f43f5e; font-weight: bold;")
        gg_layout.addWidget(severity_label, 1, 1)

        layout.addWidget(general_group)

        # 4. Sección: Parámetros de Ejecución
        exec_group = self._create_section_card(
            title="Parámetros de Ejecución",
            description="Opciones de procesamiento y comportamiento del motor de auditoría."
        )
        eg_layout = QVBoxLayout(exec_group)
        eg_layout.setSpacing(10)

        chk_stop = QCheckBox("Detener ejecución ante errores no recuperables de fuente")
        chk_stop.setChecked(True)
        chk_stop.setEnabled(False)
        chk_stop.setStyleSheet("color: #cbd5e1;")

        chk_readonly = QCheckBox("Modo estricto de solo lectura forzado (Garantía de no modificación en nube/BD)")
        chk_readonly.setChecked(True)
        chk_readonly.setEnabled(False)
        chk_readonly.setStyleSheet("color: #10b981; font-weight: 500;")

        eg_layout.addWidget(chk_stop)
        eg_layout.addWidget(chk_readonly)
        layout.addWidget(exec_group)

        layout.addStretch()

        scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

    def _create_section_card(self, title: str, description: str) -> QFrame:
        """Crea un contenedor tipo tarjeta con encabezado y descripción formal."""
        card = QFrame()
        card.setProperty("class", "card")
        card.setStyleSheet(
            "background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 18px;"
        )
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 12)
        header_layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #38bdf8;")

        lbl_desc = QLabel(description)
        lbl_desc.setStyleSheet("font-size: 12px; color: #94a3b8;")

        header_layout.addWidget(lbl_title)
        header_layout.addWidget(lbl_desc)

        # Se inserta el layout de encabezado como primer hijo del layout principal de la tarjeta al inicializar
        card_main_layout = QVBoxLayout(card)
        card_main_layout.addLayout(header_layout)
        return card

