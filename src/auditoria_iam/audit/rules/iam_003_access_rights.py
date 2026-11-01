"""
Regla IAM-003: Derechos de Acceso (ISO/IEC 27001:2022 Control 5.18).
Analiza las políticas técnicas JSON de IAM para detectar permisos irrestrictos globales
y evaluar el principio de mínimo privilegio dentro del alcance técnico del control 5.18.

ALCANCE Y EXCLUSIÓN:
El control ISO/IEC 27001:2022 8.2 (Derechos de acceso privilegiado) se encuentra EXCLUIDO
del alcance de este proyecto. Esta regla no realiza auditorías de gestión de cuentas
privilegiadas ni utiliza clasificaciones de superusuario o banderas auxiliares
(is_admin, has_admin_access) para determinar incumplimientos o conformidades. Se limita
al análisis técnico estricto de documentos JSON de política IAM bajo el control 5.18.
"""
import json
from typing import Any, Dict, List, Optional, Tuple

from src.auditoria_iam.audit.models import (
    AuditContext,
    AuditResult,
    extract_resource_attributes,
)
from src.auditoria_iam.audit.rules.base import BaseAuditRule


class RuleIAM003AccessRights(BaseAuditRule):
    """
    Evaluación de conformidad con el control ISO/IEC 27001:2022 5.18 (Derechos de acceso).
    Criterios:
      - C18-01: Ausencia de permisos irrestrictos globales (comodines globales en políticas JSON).
      - C18-02: Principio de mínimo privilegio (requiere especificación técnica de permisos esperados).
    """

    @property
    def rule_code(self) -> str:
        return "IAM-003"

    @property
    def rule_name(self) -> str:
        return "Control de derechos de acceso y prevención de privilegios excesivos"

    @property
    def iso_control(self) -> str:
        return "5.18"

    @property
    def default_severity(self) -> str:
        return "CRITICA"

    def evaluate(
        self,
        resource: Dict[str, Any],
        context: Optional[AuditContext] = None
    ) -> List[AuditResult]:
        results: List[AuditResult] = []
        resource_id = resource.get("id")
        attrs = extract_resource_attributes(resource)

        # 1. Obtener y parsear políticas técnicas asociadas
        policies, extraction_error = self._extract_policies(attrs)

        # Criterio C18-01: Detección técnica de permisos irrestrictos globales
        result_c18_01 = self._evaluate_unrestricted_permissions(resource_id, policies, extraction_error)
        results.append(result_c18_01)

        # Criterio C18-02: Principio de mínimo privilegio frente a referencia autorizada
        result_c18_02 = self._evaluate_profile_privilege_scope(resource_id, context)
        results.append(result_c18_02)

        return results

    def _extract_policies(
        self, attrs: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Extrae y valida los documentos de política técnica asociados a la identidad.
        La ausencia o invalidez de atributos no relacionados con políticas (como grupos o MFA)
        no descarta los documentos JSON de política disponibles.

        Distingue claramente entre:
          - Atributo ausente ('missing_attribute')
          - Lista vacía ('empty_list')
          - Sintaxis JSON malformada ('invalid_json')
          - Objeto JSON con estructura no admitida ('invalid_structure')
          - Elemento con tipo no admitido ('unsupported_item_type')
          - Documento válido y analizable
        """
        found_policy_key = False
        raw_items: List[Any] = []

        # Atributos que contienen listas o colecciones de políticas
        for key in ("policies", "attached_policies", "inline_policies"):
            if key in attrs:
                found_policy_key = True
                val = attrs[key]
                if val is None:
                    continue
                if isinstance(val, list):
                    raw_items.extend(val)
                elif isinstance(val, (dict, str)):
                    raw_items.append(val)
                else:
                    return [], "unsupported_item_type"

        # Atributos de política técnica individual
        for key in ("policy_document", "PolicyDocument"):
            if key in attrs:
                found_policy_key = True
                val = attrs[key]
                if val is not None:
                    if isinstance(val, (dict, str)):
                        raw_items.append(val)
                    else:
                        return [], "unsupported_item_type"

        if not found_policy_key:
            return [], "missing_attribute"

        if len(raw_items) == 0:
            return [], "empty_list"

        parsed_policies: List[Dict[str, Any]] = []
        for item in raw_items:
            if isinstance(item, bool):
                return [], "unsupported_item_type"
            if isinstance(item, dict):
                parsed_policies.append(item)
            elif isinstance(item, str):
                try:
                    parsed = json.loads(item)
                    if isinstance(parsed, dict):
                        parsed_policies.append(parsed)
                    else:
                        return [], "invalid_structure"
                except Exception:
                    return [], "invalid_json"
            else:
                return [], "unsupported_item_type"

        return parsed_policies, None

    def _evaluate_unrestricted_permissions(
        self,
        resource_id: Optional[int | str],
        policies: List[Dict[str, Any]],
        extraction_error: Optional[str]
    ) -> AuditResult:
        """
        Analiza las declaraciones JSON de política en busca de permisos irrestrictos globales
        mediante comodines ('*' en Action y Resource, o 'iam:*' en Resource '*').
        No genera hallazgos autónomos por meros nombres de políticas si no se dispone del documento JSON.
        """
        if extraction_error == "missing_attribute":
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C18-01",
                resource_id=resource_id,
                result_status="No evaluable",
                justification="No se dispone de documentos de política técnica JSON para analizar los derechos de acceso asignados.",
                details={},
                evidence={"missing_policy_attributes": True}
            )

        if extraction_error == "empty_list":
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C18-01",
                resource_id=resource_id,
                result_status="No evaluable",
                justification="La lista de políticas técnicas asignadas a la identidad se encuentra vacía.",
                details={},
                evidence={"empty_policy_list": True}
            )

        if extraction_error == "invalid_json":
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C18-01",
                resource_id=resource_id,
                result_status="No evaluable",
                justification="El documento de política técnica contiene sintaxis JSON malformada.",
                details={},
                evidence={"parse_error": "JSON malformado"}
            )

        if extraction_error == "invalid_structure":
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C18-01",
                resource_id=resource_id,
                result_status="No evaluable",
                justification="El documento de política técnica no posee una estructura de objeto JSON válida.",
                details={},
                evidence={"invalid_structure": True}
            )

        if extraction_error == "unsupported_item_type":
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C18-01",
                resource_id=resource_id,
                result_status="No evaluable",
                justification="Elemento de política técnica con tipo no admitido (se requiere objeto o cadena JSON).",
                details={},
                evidence={"invalid_item_type": True}
            )

        if not policies:
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C18-01",
                resource_id=resource_id,
                result_status="No evaluable",
                justification="No se dispone de documentos de política técnica JSON para analizar los derechos de acceso asignados.",
                details={},
                evidence={"missing_policy_documents": True}
            )

        unrestricted_findings: List[Dict[str, Any]] = []

        for policy in policies:
            if not isinstance(policy, dict):
                return AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C18-01",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="El documento de política técnica no posee una estructura de objeto JSON válida.",
                    details={},
                    evidence={"invalid_structure": True}
                )

            statements = policy.get("Statement")
            if statements is None:
                return AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C18-01",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="Documento de política técnica sin campo 'Statement' definido.",
                    details={},
                    evidence={"missing_statement": True}
                )

            if isinstance(statements, dict):
                statements = [statements]
            elif not isinstance(statements, list):
                return AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C18-01",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="El campo 'Statement' de la política técnica no es una lista ni un objeto válido.",
                    details={},
                    evidence={"invalid_statement_type": str(type(statements))}
                )

            if len(statements) == 0:
                return AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C18-01",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="El documento de política técnica contiene una lista vacía de declaraciones ('Statement').",
                    details={},
                    evidence={"empty_statement_list": True}
                )

            for stmt in statements:
                if not isinstance(stmt, dict):
                    return AuditResult(
                        rule_code=self.rule_code,
                        criterion_code="C18-01",
                        resource_id=resource_id,
                        result_status="No evaluable",
                        justification="Declaración 'Statement' inválida o malformada en la política técnica.",
                        details={},
                        evidence={"invalid_statement": True}
                    )

                # Detección de NotAction o NotResource
                if "NotAction" in stmt or "NotResource" in stmt:
                    return AuditResult(
                        rule_code=self.rule_code,
                        criterion_code="C18-01",
                        resource_id=resource_id,
                        result_status="No evaluable",
                        justification=(
                            "La política técnica contiene cláusulas 'NotAction' o 'NotResource' que no pueden "
                            "interpretarse de forma determinista y segura en este analizador acotado."
                        ),
                        details={"has_not_action": "NotAction" in stmt, "has_not_resource": "NotResource" in stmt},
                        evidence={"unsupported_not_operator": True}
                    )

                # Detección y rechazo de la propiedad Condition (vacía, malformada o estructurada)
                if "Condition" in stmt:
                    return AuditResult(
                        rule_code=self.rule_code,
                        criterion_code="C18-01",
                        resource_id=resource_id,
                        result_status="No evaluable",
                        justification=(
                            "La declaración contiene la propiedad 'Condition' (contiene condiciones de autorización que no pueden "
                            "interpretarse de forma determinista y segura en este analizador acotado)."
                        ),
                        details={"has_condition": True},
                        evidence={"unsupported_condition": True}
                    )

                # Validación rigurosa de Effect
                effect = stmt.get("Effect")
                if not isinstance(effect, str) or isinstance(effect, bool) or effect not in ("Allow", "Deny"):
                    return AuditResult(
                        rule_code=self.rule_code,
                        criterion_code="C18-01",
                        resource_id=resource_id,
                        result_status="No evaluable",
                        justification="Declaración en política técnica con valor 'Effect' ausente o no estándar (se requiere 'Allow' o 'Deny').",
                        details={},
                        evidence={"invalid_effect": True}
                    )

                # Validación rigurosa de Action y Resource (aplica a declaraciones Allow y Deny)
                raw_actions = stmt.get("Action")
                raw_resources = stmt.get("Resource")

                if raw_actions is None or raw_resources is None:
                    return AuditResult(
                        rule_code=self.rule_code,
                        criterion_code="C18-01",
                        resource_id=resource_id,
                        result_status="No evaluable",
                        justification="Declaración en política técnica sin atributos obligatorios 'Action' o 'Resource'.",
                        details={},
                        evidence={"incomplete_statement": True}
                    )

                actions = self._validate_and_extract_string_or_list(raw_actions)
                resources = self._validate_and_extract_string_or_list(raw_resources)

                if actions is None or resources is None:
                    return AuditResult(
                        rule_code=self.rule_code,
                        criterion_code="C18-01",
                        resource_id=resource_id,
                        result_status="No evaluable",
                        justification=(
                            "Los atributos 'Action' o 'Resource' contienen tipos o estructuras no admitidas "
                            "(se requieren exclusivamente cadenas no vacías o listas no vacías de cadenas no vacías)."
                        ),
                        details={},
                        evidence={"invalid_action_or_resource_structure": True}
                    )

                # Si es una declaración Deny válida, no concede permisos y se continúa sin generar hallazgo
                if effect == "Deny":
                    continue

                # Detección de comodín total '*' en Action y Resource para declaraciones Allow
                has_star_action = any(a in ("*", "*:*") for a in actions)
                has_star_resource = any(r == "*" for r in resources)
                has_iam_star = any(a == "iam:*" for a in actions)

                if has_star_action and has_star_resource:
                    unrestricted_findings.append({
                        "pattern": "full_wildcard",
                        "reason": "Comodín total '*' en Action y Resource (permiso irrestricto global)"
                    })
                elif has_iam_star and has_star_resource:
                    unrestricted_findings.append({
                        "pattern": "iam_star_wildcard",
                        "reason": "Permiso 'iam:*' sobre recurso '*' (capacidad técnica de modificación irrestricta de IAM)"
                    })

        if unrestricted_findings:
            patterns = sorted(list({f["pattern"] for f in unrestricted_findings}))
            reasons = [f["reason"] for f in unrestricted_findings]
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C18-01",
                resource_id=resource_id,
                result_status="Hallazgo",
                justification=(
                    f"Se detectaron {len(unrestricted_findings)} declaración(es) de permisos irrestrictos "
                    "globales en las políticas técnicas JSON analizadas."
                ),
                details={
                    "findings_count": len(unrestricted_findings),
                    "patterns_detected": patterns
                },
                evidence={
                    "findings_count": len(unrestricted_findings),
                    "patterns_detected": patterns,
                    "findings_summary": reasons
                }
            )

        return AuditResult(
            rule_code=self.rule_code,
            criterion_code="C18-01",
            resource_id=resource_id,
            result_status="Conforme",
            justification=(
                "Las políticas técnicas JSON analizadas no presentan los patrones específicos de permisos "
                "irrestrictos globales evaluados ('*' en Action y Resource, o 'iam:*' en Resource '*')."
            ),
            details={"policies_analyzed": len(policies)},
            evidence={"unrestricted_wildcards_detected": False}
        )

    @staticmethod
    def _validate_and_extract_string_or_list(raw_val: Any) -> Optional[List[str]]:
        """
        Valida que el valor sea exclusivamente:
        - Una cadena no vacía (rechazando booleanos).
        - Una lista no vacía compuesta íntegramente por cadenas no vacías (rechazando booleanos).
        Rechaza números, booleanos, objetos, listas mixtas, listas vacías y cadenas vacías.
        No convierte valores arbitrarios mediante str().
        Retorna la lista de cadenas limpias o None si es inválido.
        """
        if raw_val is None or isinstance(raw_val, bool):
            return None
        if isinstance(raw_val, str):
            val_clean = raw_val.strip()
            return [val_clean] if val_clean else None
        if isinstance(raw_val, list):
            if len(raw_val) == 0:
                return None
            cleaned: List[str] = []
            for item in raw_val:
                if not isinstance(item, str) or isinstance(item, bool):
                    return None
                item_clean = item.strip()
                if not item_clean:
                    return None
                cleaned.append(item_clean)
            return cleaned
        return None

    def _evaluate_profile_privilege_scope(
        self,
        resource_id: Optional[int | str],
        context: Optional[AuditContext]
    ) -> AuditResult:
        """
        Evalúa el principio de mínimo privilegio (C18-02).
        
        NOTA ARQUITECTÓNICA:
        La base de datos actual no cuenta con un catálogo de permisos o políticas esperadas
        definido por perfil de acceso. Para evitar falsos resultados 'Conforme' y respetar
        la rigurosidad de la auditoría, este criterio devuelve 'No evaluable' documentando
        la especificación requerida para su futura habilitación.
        """
        profile = context.get_profile_for_resource(resource_id) if (context and resource_id) else None
        profile_id = profile.get("id") if profile else None

        return AuditResult(
            rule_code=self.rule_code,
            criterion_code="C18-02",
            resource_id=resource_id,
            result_status="No evaluable",
            justification=(
                "No evaluable: El perfil de referencia no cuenta actualmente con un catálogo formal de permisos "
                "o acciones autorizadas para contrastar el principio de mínimo privilegio. Para realizar esta "
                "comprobación técnica se requiere la definición de un catálogo de acciones (Action) y recursos "
                "(Resource) autorizados por perfil."
            ),
            profile_id=profile_id,
            details={"profile_code": profile.get("profile_code") if profile else None},
            evidence={
                "missing_expected_permissions_specification": True,
                "required_specification": "Catálogo de acciones (Action) y recursos (Resource) autorizados por perfil"
            }
        )
