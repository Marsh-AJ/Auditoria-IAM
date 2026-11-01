"""
Página de Ejecución de Auditoría para el Sistema de Auditoría IAM.
Permite seleccionar la fuente de datos (Simulador / AWS IAM) y presenta el panel de control.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class AuditPage(QWidget):
    """Pantalla para la configuración y lanzamiento de procesos de auditoría."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("audit_page")
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
        title = QLabel("Nueva auditoría")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")

        subtitle = QLabel(
            "Seleccione los parámetros de origen para iniciar la evaluación automatizada "
            "de controles ISO/IEC 27001:2022."
        )
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # 2. Tarjeta de configuración de ejecución
        config_card = QFrame()
        config_card.setProperty("class", "card")
        config_card.setStyleSheet(
            "background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px;"
        )
        card_layout = QVBoxLayout(config_card)
        card_layout.setSpacing(16)

        # Selector de fuente
        source_label = QLabel("Fuente de Información:")
        source_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #e2e8f0;")

        self.source_selector = QComboBox()
        self.source_selector.addItem("Simulador de Datos Local (Fase 4 - Entrega 1)", "simulador")
        self.source_selector.addItem("Adaptador AWS IAM Cloud - Boto3 (Fase 4 - Entrega 2)", "aws")
        self.source_selector.setStyleSheet(
            "background-color: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 8px 12px; color: #f8fafc;"
        )

        card_layout.addWidget(source_label)
        card_layout.addWidget(self.source_selector)

        # Botón de ejecución
        btn_layout = QHBoxLayout()
        self.execute_button = QPushButton("Ejecutar auditoría")
        self.execute_button.setObjectName("execute_button")
        self.execute_button.setStyleSheet(
            "background-color: #0284c7; color: #ffffff; border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold; font-size: 13px;"
        )
        self.execute_button.clicked.connect(self._on_execute_clicked)

        btn_layout.addWidget(self.execute_button)
        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)

        layout.addWidget(config_card)

        # 3. Panel de Estado y Mensajes de Operación
        status_box = QFrame()
        status_box.setStyleSheet(
            "background-color: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 16px;"
        )
        status_layout = QVBoxLayout(status_box)
        status_layout.setSpacing(8)

        status_header = QLabel("Estado de la Operación")
        status_header.setStyleSheet("font-size: 13px; font-weight: 600; color: #38bdf8;")

        self.status_message = QLabel(
            "ℹ La ejecución automatizada de auditorías estará habilitada en la Fase 5 - Entrega 2. "
            "En esta entrega estructural, los componentes de interfaz se encuentran desacoplados del motor de auditoría."
        )
        self.status_message.setWordWrap(True)
        self.status_message.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.4;")

        status_layout.addWidget(status_header)
        status_layout.addWidget(self.status_message)
        layout.addWidget(status_box)

        layout.addStretch()

        scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

    def _on_execute_clicked(self) -> None:
        """Muestra el mensaje informativo indicando que la ejecución se activará en la Fase 5 - Entrega 2."""
        selected_text = self.source_selector.currentText()
        self.status_message.setText(
            f"ℹ Solicitud de auditoría registrada para '{selected_text}'.\n\n"
            "La vinculación funcional del motor algorítmico y la persistencia relacional "
            "se completará en la Fase 5 - Entrega 2 conforme al plan de desarrollo aprobado. "
            "No se han efectuado consultas a la base de datos ni a AWS."
        )
        self.status_message.setStyleSheet("color: #38bdf8; font-size: 13px; line-height: 1.4; font-weight: 500;")

