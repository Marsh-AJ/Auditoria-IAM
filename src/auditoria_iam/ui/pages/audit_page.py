"""
Página de Ejecución de Auditoría para el Sistema de Auditoría IAM.
Permite seleccionar la fuente de datos (Simulador / AWS IAM) y ejecutar
procesos de auditoría reales a través del motor algorítmico existente.
"""
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
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


class AuditPage(QWidget):
    """Pantalla para la configuración y lanzamiento de procesos de auditoría."""

    # Señal emitida al completar exitosamente una auditoría: (results, resources, summary)
    audit_completed = Signal(list, list, dict)
    # Señal para solicitar navegación a otra vista por índice (ej. resultados = 2)
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
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 1. Encabezado de la página
        title = QLabel("Nueva auditoría")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")

        subtitle = QLabel(
            "Seleccione los parámetros de origen para iniciar la evaluación automatizada "
            "de controles ISO/IEC 27001:2022 mediante el motor algorítmico central."
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
        self.source_selector.currentIndexChanged.connect(self._on_source_changed)

        card_layout.addWidget(source_label)
        card_layout.addWidget(self.source_selector)

        # Botón de ejecución y botón de ver resultados
        btn_layout = QHBoxLayout()
        self.execute_button = QPushButton("Ejecutar auditoría")
        self.execute_button.setObjectName("execute_button")
        self.execute_button.setCursor(Qt.PointingHandCursor)
        self.execute_button.setStyleSheet(
            "background-color: #0284c7; color: #ffffff; border: none; border-radius: 6px; "
            "padding: 10px 24px; font-weight: bold; font-size: 13px;"
        )
        self.execute_button.clicked.connect(self._on_execute_clicked)

        self.view_results_button = QPushButton("Ver resultados detallados →")
        self.view_results_button.setCursor(Qt.PointingHandCursor)
        self.view_results_button.setVisible(False)
        self.view_results_button.setStyleSheet(
            "background-color: #334155; color: #38bdf8; border: 1px solid #38bdf8; "
            "border-radius: 6px; padding: 10px 18px; font-weight: 600; font-size: 13px;"
        )
        self.view_results_button.clicked.connect(lambda: self.navigate_requested.emit(2))

        btn_layout.addWidget(self.execute_button)
        btn_layout.addWidget(self.view_results_button)
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
            "✓ Fuente 'Simulador de Datos Local' seleccionada. Pulse 'Ejecutar auditoría' para iniciar "
            "la evaluación técnica automatizada de las reglas IAM-001, IAM-002, IAM-003 e IAM-004."
        )
        self.status_message.setWordWrap(True)
        self.status_message.setStyleSheet("color: #cbd5e1; font-size: 13px; line-height: 1.4;")

        status_layout.addWidget(status_header)
        status_layout.addWidget(self.status_message)
        layout.addWidget(status_box)

        layout.addStretch()

        scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

    def _on_source_changed(self, index: int) -> None:
        """Gestiona el cambio de fuente de información seleccionada."""
        source_key = self.source_selector.currentData()
        self.view_results_button.setVisible(False)
        self.execute_button.setEnabled(True)

        if source_key == "simulador":
            self.status_message.setText(
                "✓ Fuente 'Simulador de Datos Local' seleccionada. Pulse 'Ejecutar auditoría' para iniciar "
                "la evaluación técnica automatizada de las reglas IAM-001, IAM-002, IAM-003 e IAM-004."
            )
            self.status_message.setStyleSheet("color: #cbd5e1; font-size: 13px; line-height: 1.4;")
        elif source_key == "aws":
            self.status_message.setText(
                "✓ Fuente 'Adaptador AWS IAM Cloud (Boto3)' seleccionada. Pulse 'Ejecutar auditoría' para iniciar "
                "la consulta de solo lectura e inspección de usuarios, grupos, roles y políticas en AWS IAM."
            )
            self.status_message.setStyleSheet("color: #cbd5e1; font-size: 13px; line-height: 1.4;")

    def _on_execute_clicked(self) -> None:
        """Inicia la ejecución de la auditoría utilizando el motor centralizado."""
        source_key = self.source_selector.currentData()

        # Deshabilitar botón temporalmente para evitar ejecuciones concurrentes
        self.execute_button.setEnabled(False)
        self.view_results_button.setVisible(False)

        if source_key == "aws":
            self.status_message.setText(
                "⏳ Conectando con AWS IAM mediante Boto3 (solo lectura)... Consultando identidades, "
                "grupos, roles y políticas JSON para evaluar las reglas IAM-001, IAM-002, IAM-003 e IAM-004..."
            )
        else:
            self.status_message.setText(
                "⏳ Ejecutando auditoría técnica... Procesando identidades, grupos, roles y políticas JSON "
                "frente a las reglas IAM-001, IAM-002, IAM-003 e IAM-004..."
            )
        self.status_message.setStyleSheet("color: #38bdf8; font-size: 13px; line-height: 1.4;")

        # Procesar eventos de Qt para actualizar inmediatamente la interfaz
        QApplication.processEvents()

        try:
            # Invocar la ejecución del motor a través del servicio desacoplado
            if source_key == "aws":
                res_tuple = self._audit_service.run_aws_audit()
            else:
                res_tuple = self._audit_service.run_simulated_audit()

            if len(res_tuple) == 4:
                results, resources, summary, persistence_info = res_tuple
            else:
                results, resources, summary = res_tuple[:3]
                persistence_info = {"persisted": False, "run_id": None, "message": ""}

            # Emitir señal con los resultados reales
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
            self.status_message.setStyleSheet("color: #22c55e; font-size: 13px; line-height: 1.4; font-weight: 500;")
            self.view_results_button.setVisible(True)

        except AWSIAMAuthenticationError as exc:
            self.status_message.setText(
                f"❌ Error de autenticación en AWS: {exc}\n\n"
                "Verifique que las credenciales estén configuradas mediante variables de entorno "
                "(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) o el archivo de credenciales de AWS (~/.aws/credentials)."
            )
            self.status_message.setStyleSheet("color: #ef4444; font-size: 13px; line-height: 1.4; font-weight: 500;")

        except AWSIAMPermissionError as exc:
            self.status_message.setText(
                f"❌ Permisos insuficientes en AWS IAM: {exc}\n\n"
                "Asegúrese de que el usuario o rol de AWS cuente con permisos de solo lectura "
                "(acciones iam:List* e iam:Get*)."
            )
            self.status_message.setStyleSheet("color: #ef4444; font-size: 13px; line-height: 1.4; font-weight: 500;")

        except AWSIAMConnectionError as exc:
            self.status_message.setText(
                f"❌ Error de conexión con AWS IAM: {exc}\n\n"
                "No fue posible establecer comunicación con el endpoint de AWS. Verifique la conectividad de red."
            )
            self.status_message.setStyleSheet("color: #ef4444; font-size: 13px; line-height: 1.4; font-weight: 500;")

        except AWSIAMDataSourceError as exc:
            self.status_message.setText(
                f"❌ Error en la fuente de datos AWS IAM: {exc}"
            )
            self.status_message.setStyleSheet("color: #ef4444; font-size: 13px; line-height: 1.4; font-weight: 500;")

        except Exception as exc:
            self.status_message.setText(
                f"❌ Error durante la ejecución de la auditoría: {type(exc).__name__} - {str(exc)}"
            )
            self.status_message.setStyleSheet("color: #ef4444; font-size: 13px; line-height: 1.4; font-weight: 500;")

        finally:
            # Restaurar estado del botón para permitir nuevas auditorías
            self.execute_button.setEnabled(True)
