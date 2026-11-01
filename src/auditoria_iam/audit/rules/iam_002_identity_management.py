"""
Regla IAM-002: Gestión de Identidades (ISO/IEC 27001:2022 Control 5.16).
Evalúa identidades inactivas y actividad reciente de credenciales según metadatos técnicos.

NOTA TÉCNICA:
El umbral operativo de inactividad (90 días por defecto) es un parámetro técnico definido
para el prototipo de auditoría de UPHARVEN C.A., y no constituye un requisito textual ni
una regla rígida prescrita en la redacción de la norma ISO/IEC 27001:2022.
"""
from typing import Any, Dict, List, Optional

from src.auditoria_iam.audit.models import (
    AuditContext,
    AuditResult,
    extract_resource_attributes,
)
from src.auditoria_iam.audit.rules.base import BaseAuditRule


class RuleIAM002IdentityManagement(BaseAuditRule):
    """
    Evaluación de conformidad con el control ISO/IEC 27001:2022 5.16 (Gestión de identidades).
    Criterios:
      - C16-01: Estado de vigencia y activación de la identidad (diferenciando deshabilitación de desprovisionamiento).
      - C16-02: Actividad reciente de credenciales frente al umbral operativo configurable.
    """

    def __init__(self, inactivity_threshold_days: int = 90) -> None:
        if (
            not isinstance(inactivity_threshold_days, int)
            or isinstance(inactivity_threshold_days, bool)
            or inactivity_threshold_days < 0
        ):
            raise ValueError("El umbral de inactividad debe ser un número entero no negativo (cero o mayor).")
        self.inactivity_threshold_days = inactivity_threshold_days

    @property
    def rule_code(self) -> str:
        return "IAM-002"

    @property
    def rule_name(self) -> str:
        return "Gestión del ciclo de vida y estado de actividad de identidades"

    @property
    def iso_control(self) -> str:
        return "5.16"

    @property
    def default_severity(self) -> str:
        return "MEDIA"

    def evaluate(
        self,
        resource: Dict[str, Any],
        context: Optional[AuditContext] = None
    ) -> List[AuditResult]:
        results: List[AuditResult] = []
        resource_id = resource.get("id")
        resource_status = str(resource.get("resource_status", "")).strip().lower()
        attrs = extract_resource_attributes(resource)

        # 1. Criterio C16-01: Estado de vigencia y activación de la identidad
        if not resource_status:
            results.append(
                AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C16-01",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="El recurso no presenta un valor definido en el atributo 'resource_status'.",
                    details={"raw_status": resource_status},
                    evidence={"missing_field": "resource_status"}
                )
            )
        elif resource_status in ("active", "activo", "enabled"):
            results.append(
                AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C16-01",
                    resource_id=resource_id,
                    result_status="Conforme",
                    justification=f"La identidad se encuentra formalmente registrada y en estado '{resource_status}'.",
                    details={"resource_status": resource_status},
                    evidence={"status_detected": resource_status}
                )
            )
        elif resource_status in ("inactive", "inactivo", "suspended", "disabled", "deshabilitado"):
            # Validar que los metadatos de deficiencia de desprovisionamiento sean explícitos y no arbitrarios
            has_deprovisioning_flaw = self._is_explicit_deprovisioning_flaw(attrs)
            if has_deprovisioning_flaw:
                results.append(
                    AuditResult(
                        rule_code=self.rule_code,
                        criterion_code="C16-01",
                        resource_id=resource_id,
                        result_status="Hallazgo",
                        justification=(
                            f"La identidad se encuentra en estado '{resource_status}' con deficiencia técnica comprobada "
                            f"en el proceso de desprovisionamiento definitivo del ciclo de vida."
                        ),
                        details={"resource_status": resource_status, "deprovisioning_flaw": True},
                        evidence={"deprovisioning_flaw": True}
                    )
                )
            else:
                # El estado inactivo o deshabilitado sin metadatos explícitos de deficiencia no acredita por sí solo hallazgo
                results.append(
                    AuditResult(
                        rule_code=self.rule_code,
                        criterion_code="C16-01",
                        resource_id=resource_id,
                        result_status="No evaluable",
                        justification=(
                            f"La identidad se encuentra en estado '{resource_status}'. No se dispone de metadatos de ciclo "
                            f"de vida para discernir si corresponde a una suspensión administrativa temporal autorizada o a un retraso de desprovisionamiento."
                        ),
                        details={"resource_status": resource_status},
                        evidence={"insufficient_lifecycle_metadata": True}
                    )
                )
        else:
            results.append(
                AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C16-01",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification=f"Estado de recurso '{resource_status}' no reconocido para la evaluación.",
                    details={"resource_status": resource_status},
                    evidence={"unknown_status": resource_status}
                )
            )

        # 2. Criterio C16-02: Actividad reciente de credenciales frente al umbral operativo
        days_inactive = self._extract_days_inactive(attrs)

        if days_inactive is None:
            results.append(
                AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C16-02",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification=(
                        "No se dispone de metadatos válidos de último acceso o actividad "
                        "para determinar el estado operativo de las credenciales."
                    ),
                    details={"attributes_present": [k for k in attrs.keys() if not k.startswith("_")]},
                    evidence={"missing_activity_metadata": True}
                )
            )
        elif days_inactive > self.inactivity_threshold_days:
            results.append(
                AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C16-02",
                    resource_id=resource_id,
                    result_status="Hallazgo",
                    justification=(
                        f"Identidad con inactividad prolongada de {days_inactive} días desde su último acceso registrado, "
                        f"superando el umbral operativo definido para el prototipo ({self.inactivity_threshold_days} días)."
                    ),
                    details={"days_inactive": days_inactive, "threshold_days": self.inactivity_threshold_days},
                    evidence={
                        "days_inactive": days_inactive,
                        "threshold_days": self.inactivity_threshold_days,
                        "exceeded_by": days_inactive - self.inactivity_threshold_days
                    }
                )
            )
        else:
            results.append(
                AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C16-02",
                    resource_id=resource_id,
                    result_status="Conforme",
                    justification=(
                        f"Actividad reciente de la identidad verificada con {days_inactive} días desde su último acceso, "
                        f"dentro del umbral operativo definido ({self.inactivity_threshold_days} días)."
                    ),
                    details={"days_inactive": days_inactive, "threshold_days": self.inactivity_threshold_days},
                    evidence={"days_inactive": days_inactive, "threshold_days": self.inactivity_threshold_days}
                )
            )

        return results

    def _extract_days_inactive(self, attrs: Dict[str, Any]) -> Optional[int]:
        """
        Extrae y valida que los días de inactividad sean enteros no negativos.
        Rechaza flotantes/decimales, booleanos y números negativos sin conversión automática.
        """
        if attrs.get("_invalid_attributes") or attrs.get("_missing_attributes"):
            return None

        for key in ("last_access_days", "days_since_last_access", "days_inactive", "inactivity_days"):
            if key in attrs and attrs[key] is not None:
                val = attrs[key]
                # Rechazar booleanos
                if isinstance(val, bool):
                    return None
                # Rechazar decimales/flotantes
                if isinstance(val, float):
                    return None
                # Enteros no negativos
                if isinstance(val, int):
                    return val if val >= 0 else None
                # Cadenas numéricas estrictamente enteras
                if isinstance(val, str):
                    val_str = val.strip()
                    if val_str.isdigit():
                        return int(val_str)
                    return None
        return None

    @staticmethod
    def _is_explicit_deprovisioning_flaw(attrs: Dict[str, Any]) -> bool:
        """
        Valida que los metadatos de deficiencia de desprovisionamiento sean explícitos.
        Acepta únicamente booleanos True o confirmaciones textuales unívocas ('true', 'confirmed', 'confirmado').
        Rechaza estructuras o valores arbitrarios (enteros, listas, cadenas no unívocas).
        """
        for key in ("deprovisioning_flaw", "deprovisioning_pending"):
            if key in attrs:
                val = attrs[key]
                if val is True:
                    return True
                if isinstance(val, str) and val.strip().lower() in ("true", "confirmed", "confirmado"):
                    return True
        return False
