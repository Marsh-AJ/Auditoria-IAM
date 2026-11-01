"""
Regla IAM-004: Autenticación Segura (ISO/IEC 27001:2022 Control 8.5).
Evalúa la activación de Autenticación Multifactor (MFA) para identidades de usuario IAM.

ALCANCE Y EXCLUSIÓN:
Los roles IAM ('IAM_ROLE') quedan explícitamente excluidos de esta regla y no generan resultados
artificiales en C85-01, dado que los roles asumen sesiones temporales mediante AWS STS (AssumeRole)
y no disponen de mecanismos de inicio de sesión interactivo de consola con credenciales permanentes.
"""
from typing import Any, Dict, List, Optional

from src.auditoria_iam.audit.models import (
    AuditContext,
    AuditResult,
    extract_resource_attributes,
)
from src.auditoria_iam.audit.rules.base import BaseAuditRule


class RuleIAM004SecureAuthentication(BaseAuditRule):
    """
    Evaluación de conformidad con el control ISO/IEC 27001:2022 8.5 (Autenticación segura).
    Criterios:
      - C85-01: Estado de Autenticación Multifactor (MFA) para usuarios IAM.
    """

    @property
    def rule_code(self) -> str:
        return "IAM-004"

    @property
    def rule_name(self) -> str:
        return "Autenticación segura y obligatoriedad de MFA en identidades"

    @property
    def iso_control(self) -> str:
        return "8.5"

    @property
    def default_severity(self) -> str:
        return "ALTA"

    def evaluate(
        self,
        resource: Dict[str, Any],
        context: Optional[AuditContext] = None
    ) -> List[AuditResult]:
        resource_type = str(resource.get("resource_type", "")).upper()

        # Los roles IAM quedan excluidos de la evaluación interactiva de MFA (no se emite C85-01)
        if "ROLE" in resource_type:
            return []

        resource_id = resource.get("id")
        attrs = extract_resource_attributes(resource)

        # Para usuarios IAM, evaluar el estado de MFA
        mfa_status = self._extract_mfa_status(attrs)

        if mfa_status is None:
            return [
                AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C85-01",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="No se dispone de metadatos válidos sobre el estado de Autenticación Multifactor (MFA) para el usuario.",
                    details={"attributes_present": [k for k in attrs.keys() if not k.startswith("_")]},
                    evidence={"missing_or_invalid_mfa_metadata": True}
                )
            ]

        if mfa_status is True:
            return [
                AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C85-01",
                    resource_id=resource_id,
                    result_status="Conforme",
                    justification="El usuario IAM tiene configurado y activo un dispositivo de autenticación multifactor (MFA).",
                    details={"mfa_enabled": True},
                    evidence={"mfa_active": True}
                )
            ]

        return [
            AuditResult(
                rule_code=self.rule_code,
                criterion_code="C85-01",
                resource_id=resource_id,
                result_status="Hallazgo",
                justification="El usuario IAM carece de dispositivo de autenticación multifactor (MFA) habilitado.",
                details={"mfa_enabled": False},
                evidence={"mfa_active": False}
            )
        ]

    def _extract_mfa_status(self, attrs: Dict[str, Any]) -> Optional[bool]:
        """
        Extrae el estado de MFA aceptando exclusivamente booleanos y cadenas reconocidas.
        Rechaza valores numéricos arbitrarios (0, 1) y tipos no autorizados.
        """
        if attrs.get("_invalid_attributes") or attrs.get("_missing_attributes"):
            return None

        for key in ("mfa_enabled", "mfa_active", "has_mfa", "mfa"):
            if key in attrs and attrs[key] is not None:
                val = attrs[key]
                # Aceptación de booleanos puros
                if isinstance(val, bool):
                    return val
                # Aceptación de representaciones textuales expresamente reconocidas
                if isinstance(val, str):
                    lower_val = val.strip().lower()
                    if lower_val in ("true", "enabled", "activo", "habilitado"):
                        return True
                    if lower_val in ("false", "disabled", "inactivo", "deshabilitado"):
                        return False
                # Rechazar números y cualquier otro tipo
                return None
        return None
