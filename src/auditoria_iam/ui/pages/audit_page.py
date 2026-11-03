"""
Página de Ejecución de Auditoría para el Sistema de Auditoría IAM.
Permite seleccionar la fuente de datos (Simulador / AWS IAM) y ejecutar
procesos de auditoría reales mediante tarjetas ejecutivas limpias.
"""
from typing import Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.auditoria_iam.application.audit_service import AuditService
from src.auditoria_iam.data_sources.aws.exceptions import (
    AWSIAMAuthenticationError,
    AWSIAMConnectionError,
    AWSIAMDataSourceError,
    AWSIAMPermissionError,
)
from src.auditoria_iam.ui.icons import create_icon_badge, render_svg_icon


class AuditPage(QWidget):
    """Pantalla para la configuración y lanzamiento de procesos de auditoría."""

    audit_completed = Signal(list, list, dict)
    navigate_requested = Signal(int)

    def __init__(
        self,
        parent: QWidget | None = None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("audit_page")
        self._audit_service = audit_service or AuditService()
        self._init_ui()

    def _init_ui(self) -> None:
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        content_widget.setObjectName("audit_canvas")
        content_widget.setStyleSheet("QWidget#audit_canvas { background-color: #F5F7FA; }")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(28, 24, 28, 30)
        layout.setSpacing(18)

        # 1. Encabezado de la página
        title_col = QVBoxLayout()
        title_col.setSpacing(3)

        title = QLabel("Ejecutar Auditoría IAM")
        title.setProperty("class", "page_title")

        subtitle = QLabel(
            "Seleccione el origen de identidades para iniciar la evaluación automatizada de controles ISO/IEC 27001:2022."
        )
        subtitle.setProperty("class", "page_subtitle")
        subtitle.setWordWrap(True)

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        layout.addLayout(title_col)

        # 2. Tarjeta principal de configuración de ejecución
        config_card = QFrame()
        config_card.setProperty("class", "card")
        card_layout = QVBoxLayout(config_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # Cabecera de la tarjeta
        cfg_header = QWidget()
        cfg_h_layout = QHBoxLayout(cfg_header)
        cfg_h_layout.setContentsMargins(22, 18, 22, 14)

        cfg_text_col = QVBoxLayout()
        cfg_text_col.setSpacing(2)
        cfg_title = QLabel("Parámetros de Origen")
        cfg_title.setProperty("class", "card_header_title")
        cfg_sub = QLabel("La inspección se realiza estrictamente en modo de solo lectura sin alterar recursos.")
        cfg_sub.setStyleSheet("color: #64748B; font-size: 12px;")
        cfg_text_col.addWidget(cfg_title)
        cfg_text_col.addWidget(cfg_sub)

        cfg_icon = create_icon_badge(
            "play_bolt",
            fg_color="#294F78",
            bg_color="#EEF4FF",
            border_color="#DBEAFE",
            box_size=36,
            icon_size=17,
            radius=9,
        )
        cfg_h_layout.addLayout(cfg_text_col, stretch=1)
        cfg_h_layout.addWidget(cfg_icon)
        card_layout.addWidget(cfg_header)

        line1 = QFrame()
        line1.setFixedHeight(1)
        line1.setStyleSheet("background-color: #F1F5F9; border: none;")
        card_layout.addWidget(line1)

        # Cuerpo del formulario
        cfg_body = QWidget()
        cfg_b_layout = QVBoxLayout(cfg_body)
        cfg_b_layout.setContentsMargins(22, 18, 22, 18)
        cfg_b_layout.setSpacing(8)

        source_label = QLabel("FUENTE DE INFORMACIÓN")
        source_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.6px;")

        self.source_selector = QComboBox()
        self.source_selector.addItem("Simulador de Datos Local — Entorno determinista de validación", "simulador")
        self.source_selector.addItem("Adaptador AWS IAM Cloud (Boto3) — Consulta en vivo de solo lectura", "aws")
        self.source_selector.currentIndexChanged.connect(self._on_source_changed)

        cfg_b_layout.addWidget(source_label)
        cfg_b_layout.addWidget(self.source_selector)
        card_layout.addWidget(cfg_body)

        line2 = QFrame()
        line2.setFixedHeight(1)
        line2.setStyleSheet("background-color: #F1F5F9; border: none;")
        card_layout.addWidget(line2)

        # Pie de acciones de la tarjeta
        cfg_footer = QWidget()
        btn_layout = QHBoxLayout(cfg_footer)
        btn_layout.setContentsMargins(22, 14, 22, 14)
        btn_layout.setSpacing(12)

        self.execute_button = QPushButton("  Ejecutar auditoría")
        self.execute_button.setObjectName("execute_button")
        self.execute_button.setProperty("class", "primary_button")
        self.execute_button.setIcon(render_svg_icon("play_bolt", color="#FFFFFF", disabled_color="#94A3B8", size=15))
        self.execute_button.setIconSize(QSize(15, 15))
        self.execute_button.setCursor(Qt.PointingHandCursor)
        self.execute_button.clicked.connect(self._on_execute_clicked)

        self.view_results_button = QPushButton("Ver resultados detallados  →")
        self.view_results_button.setProperty("class", "secondary_button")
        self.view_results_button.setCursor(Qt.PointingHandCursor)
        self.view_results_button.setVisible(False)
        self.view_results_button.clicked.connect(lambda: self.navigate_requested.emit(2))

        btn_layout.addWidget(self.execute_button)
        btn_layout.addWidget(self.view_results_button)
        btn_layout.addStretch()
        card_layout.addWidget(cfg_footer)

        layout.addWidget(config_card)

        # 3. Tarjeta de Estado de la Operación y Alcance
        status_card = QFrame()
        status_card.setProperty("class", "card")
        status_card_layout = QVBoxLayout(status_card)
        status_card_layout.setContentsMargins(0, 0, 0, 0)
        status_card_layout.setSpacing(0)

        st_header = QWidget()
        st_h_layout = QHBoxLayout(st_header)
        st_h_layout.setContentsMargins(22, 16, 22, 12)

        status_header_lbl = QLabel("Estado de la Operación")
        status_header_lbl.setProperty("class", "card_header_title")
        st_icon = create_icon_badge(
            "shield_check",
            fg_color="#16845B",
            bg_color="#ECFDF5",
            border_color="#D1FAE5",
            box_size=34,
            icon_size=16,
            radius=8,
        )
        st_h_layout.addWidget(status_header_lbl, stretch=1)
        st_h_layout.addWidget(st_icon)
        status_card_layout.addWidget(st_header)

        line3 = QFrame()
        line3.setFixedHeight(1)
        line3.setStyleSheet("background-color: #F1F5F9; border: none;")
        status_card_layout.addWidget(line3)

        st_body = QWidget()
        st_b_layout = QVBoxLayout(st_body)
        st_b_layout.setContentsMargins(22, 16, 22, 18)

        self.status_message = QLabel(
            "✓  Fuente 'Simulador de Datos Local' seleccionada. Pulse 'Ejecutar auditoría' para iniciar "
            "la evaluación técnica automatizada de las reglas IAM-001, IAM-002, IAM-003 e IAM-004."
        )
        self.status_message.setWordWrap(True)
        self.status_message.setStyleSheet("color: #334155; font-size: 13px; line-height: 1.45;")
        st_b_layout.addWidget(self.status_message)
        status_card_layout.addWidget(st_body)

        line4 = QFrame()
        line4.setFixedHeight(1)
        line4.setStyleSheet("background-color: #F1F5F9; border: none;")
        status_card_layout.addWidget(line4)

        # Franja inferior informativa de controles activos
        st_footer = QWidget()
        st_f_layout = QHBoxLayout(st_footer)
        st_f_layout.setContentsMargins(22, 10, 22, 12)
        st_f_layout.setSpacing(8)

        lbl_scope = QLabel("Alcance activo:")
        lbl_scope.setStyleSheet("color: #64748B; font-size: 11.5px; font-weight: 600;")
        st_f_layout.addWidget(lbl_scope)

        for chip_txt in (
            "IAM-001 · ISO 5.15",
            "IAM-002 · ISO 5.16",
            "IAM-003 · ISO 5.18",
            "IAM-004 · ISO 8.5",
        ):
            chip = QLabel(chip_txt)
            chip.setStyleSheet(
                "background-color: #F8FAFC; color: #475569; border: 1px solid #E2E8F0; "
                "border-radius: 6px; padding: 3px 9px; font-size: 11px; font-weight: 600;"
            )
            st_f_layout.addWidget(chip)

        st_f_layout.addStretch()
        status_card_layout.addWidget(st_footer)

        layout.addWidget(status_card)
        layout.addStretch()

        scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

    def _on_source_changed(self, index: int) -> None:
        source_key = self.source_selector.currentData()
        self.view_results_button.setVisible(False)
        self.execute_button.setEnabled(True)

        if source_key == "simulador":
            self.status_message.setText(
                "✓  Fuente 'Simulador de Datos Local' seleccionada. Pulse 'Ejecutar auditoría' para iniciar "
                "la evaluación técnica automatizada de las reglas IAM-001, IAM-002, IAM-003 e IAM-004."
            )
            self.status_message.setStyleSheet("color: #334155; font-size: 13px; line-height: 1.45;")
        elif source_key == "aws":
            self.status_message.setText(
                "✓  Fuente 'Adaptador AWS IAM Cloud (Boto3)' seleccionada. Pulse 'Ejecutar auditoría' para iniciar "
                "la consulta de solo lectura e inspección de usuarios, grupos, roles y políticas en AWS IAM."
            )
            self.status_message.setStyleSheet("color: #334155; font-size: 13px; line-height: 1.45;")

    def _on_execute_clicked(self) -> None:
        source_key = self.source_selector.currentData()

        self.execute_button.setEnabled(False)
        self.view_results_button.setVisible(False)

        if source_key == "aws":
            self.status_message.setText(
                "⏳  Conectando con AWS IAM mediante Boto3 (solo lectura)... Consultando identidades, "
                "grupos, roles y políticas JSON para evaluar las reglas IAM-001, IAM-002, IAM-003 e IAM-004..."
            )
        else:
            self.status_message.setText(
                "⏳  Ejecutando auditoría técnica... Procesando identidades, grupos, roles y políticas JSON "
                "frente a las reglas IAM-001, IAM-002, IAM-003 e IAM-004..."
            )
        self.status_message.setStyleSheet("color: #294F78; font-size: 13px; line-height: 1.45; font-weight: 600;")

        QApplication.processEvents()

        try:
            if source_key == "aws":
                res_tuple = self._audit_service.run_aws_audit()
            else:
                res_tuple = self._audit_service.run_simulated_audit()

            if len(res_tuple) == 4:
                results, resources, summary, persistence_info = res_tuple
            else:
                results, resources, summary = res_tuple[:3]
                persistence_info = {"persisted": False, "run_id": None, "message": ""}

            self.audit_completed.emit(results, resources, summary)

            persistence_msg = f"\n\n{persistence_info['message']}" if persistence_info.get("message") else ""
            source_label = "AWS IAM (Nube)" if source_key == "aws" else "Simulador Local"

            self.status_message.setText(
                f"✓ Auditoría finalizada correctamente ({source_label}).\n\n"
                f"• Total de evaluaciones: {summary['total']}\n"
                f"• Conforme: {summary['conforme']}\n"
                f"• Hallazgo: {summary['hallazgo']}\n"
                f"• No evaluable: {summary['no_evaluable']}"
                f"{persistence_msg}\n\n"
                f"Los resultados detallados se encuentran disponibles en la sección 'Resultados'."
            )
            self.status_message.setStyleSheet("color: #16845B; font-size: 13px; line-height: 1.45; font-weight: 600;")
            self.view_results_button.setVisible(True)

        except AWSIAMAuthenticationError as exc:
            self.status_message.setText(
                f"❌ Error de autenticación en AWS: {exc}\n\n"
                "Verifique que las credenciales estén configuradas mediante variables de entorno "
                "(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) o el archivo ~/.aws/credentials."
            )
            self.status_message.setStyleSheet("color: #D64545; font-size: 13px; line-height: 1.45; font-weight: 600;")

        except AWSIAMPermissionError as exc:
            self.status_message.setText(
                f"❌ Permisos insuficientes en AWS IAM: {exc}\n\n"
                "Asegúrese de que el usuario o rol de AWS cuente con permisos de solo lectura "
                "(acciones iam:List* e iam:Get*)."
            )
            self.status_message.setStyleSheet("color: #D64545; font-size: 13px; line-height: 1.45; font-weight: 600;")

        except AWSIAMConnectionError as exc:
            self.status_message.setText(
                f"❌ Error de conexión con AWS IAM: {exc}\n\n"
                "No fue posible establecer comunicación con el endpoint de AWS. Verifique la conectividad de red."
            )
            self.status_message.setStyleSheet("color: #D64545; font-size: 13px; line-height: 1.45; font-weight: 600;")

        except AWSIAMDataSourceError as exc:
            self.status_message.setText(f"❌ Error en la fuente de datos AWS IAM: {exc}")
            self.status_message.setStyleSheet("color: #D64545; font-size: 13px; line-height: 1.45; font-weight: 600;")

        except Exception as exc:
            self.status_message.setText(
                f"❌ Error durante la ejecución de la auditoría: {type(exc).__name__} - {str(exc)}"
            )
            self.status_message.setStyleSheet("color: #D64545; font-size: 13px; line-height: 1.45; font-weight: 600;")

        finally:
            self.execute_button.setEnabled(True)
