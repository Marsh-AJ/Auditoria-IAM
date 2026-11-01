"""
Clase Base Abstracta para las Reglas de Auditoría IAM.
Define el contrato unificado que debe implementar cada regla técnica.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.auditoria_iam.audit.models import AuditContext, AuditResult


class BaseAuditRule(ABC):
    """Contrato base para todas las reglas algorítmicas de auditoría IAM."""

    @property
    @abstractmethod
    def rule_code(self) -> str:
        """Código de catálogo de la regla (ej. 'IAM-001')."""
        pass

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Nombre descriptivo de la regla."""
        pass

    @property
    @abstractmethod
    def iso_control(self) -> str:
        """Control técnico ISO/IEC 27001:2022 asociado (ej. '5.15')."""
        pass

    @property
    @abstractmethod
    def default_severity(self) -> str:
        """Severidad formal por defecto (ej. 'ALTA', 'MEDIA', 'BAJA')."""
        pass

    @abstractmethod
    def evaluate(
        self,
        resource: Dict[str, Any],
        context: Optional[AuditContext] = None
    ) -> List[AuditResult]:
        """
        Ejecuta la evaluación técnica de la regla sobre un recurso específico.
        
        Args:
            resource: Diccionario con los datos y atributos del recurso IAM.
            context: Contexto opcional con perfiles de acceso y listas esperadas.
            
        Returns:
            Lista de instancias AuditResult con los estados y evidencias generados.
        """
        pass

