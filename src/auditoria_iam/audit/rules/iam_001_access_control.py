"""
Regla IAM-001: Control de Acceso (ISO/IEC 27001:2022 Control 5.15).
Evalúa por separado usuarios IAM (pertenencia a grupos) y roles IAM (principales y acciones de confianza).
"""
import json
from typing import Any, Dict, List, Optional, Set, Tuple

from src.auditoria_iam.audit.models import (
    AuditContext,
    AuditResult,
    extract_resource_attributes,
)
from src.auditoria_iam.audit.rules.base import BaseAuditRule


class RuleIAM001AccessControl(BaseAuditRule):
    """
    Evaluación de conformidad con el control ISO/IEC 27001:2022 5.15 (Control de acceso).
    Criterios:
      - C15-01: Correspondencia de pertenencia a grupos para usuarios.
      - C15-02: Correspondencia de entidades autorizadas para asumir roles (principal y acción).
      - C15-03: Disponibilidad y validez del perfil de referencia.
    """

    @property
    def rule_code(self) -> str:
        return "IAM-001"

    @property
    def rule_name(self) -> str:
        return "Control de acceso a identidades según perfil autorizado"

    @property
    def iso_control(self) -> str:
        return "5.15"

    @property
    def default_severity(self) -> str:
        return "ALTA"

    def evaluate(
        self,
        resource: Dict[str, Any],
        context: Optional[AuditContext] = None
    ) -> List[AuditResult]:
        results: List[AuditResult] = []
        resource_id = resource.get("id")
        resource_type = str(resource.get("resource_type", "")).upper()
        attrs = extract_resource_attributes(resource)

        # 1. Obtener y validar perfil de acceso de referencia
        profile: Optional[Dict[str, Any]] = None
        if context is not None and resource_id is not None:
            profile = context.get_profile_for_resource(resource_id)

        # Criterio C15-03: Disponibilidad y validez del perfil de referencia
        if profile is None or str(profile.get("status", "")).lower() != "active":
            results.append(
                AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C15-03",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="La identidad no posee un perfil de acceso de referencia activo y válido asignado.",
                    profile_id=None,
                    details={"resource_type": resource_type, "profile_found": False},
                    evidence={"reason": "Perfil de referencia ausente o inactivo en resource_access_profiles."}
                )
            )

            # Si no hay perfil, los criterios dependientes son estrictamente No evaluables
            dependent_criterion = "C15-01" if "USER" in resource_type else "C15-02"
            results.append(
                AuditResult(
                    rule_code=self.rule_code,
                    criterion_code=dependent_criterion,
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification=(
                        "No es posible evaluar la correspondencia de asignaciones de acceso "
                        "debido a la ausencia de un perfil de referencia activo."
                    ),
                    profile_id=None,
                    details={"resource_type": resource_type},
                    evidence={"missing_profile": True}
                )
            )
            return results

        profile_id = profile.get("id")
        is_user = "USER" in resource_type
        is_role = "ROLE" in resource_type

        # Validar que el tipo de recurso sea soportado (USER o ROLE)
        if not is_user and not is_role:
            results.append(
                AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C15-03",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification=f"Tipo de recurso '{resource_type}' no soportado para la evaluación de perfiles de control de acceso.",
                    profile_id=profile_id,
                    details={"resource_type": resource_type},
                    evidence={"unsupported_type": resource_type}
                )
            )
            results.append(
                AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C15-01",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification=f"Tipo de recurso '{resource_type}' no soportado para la evaluación de asignaciones de acceso.",
                    profile_id=profile_id,
                    details={"resource_type": resource_type},
                    evidence={"unsupported_type": resource_type}
                )
            )
            return results

        expected_identity_type = "user" if is_user else "role"
        actual_profile_type = str(profile.get("identity_type", "")).lower()

        # Validar compatibilidad estricta de tipo entre la identidad y el perfil
        if actual_profile_type != expected_identity_type:
            results.append(
                AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C15-03",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification=(
                        f"El perfil de referencia asignado ('{profile.get('profile_code')}') es de tipo '{actual_profile_type}', "
                        f"incompatible con la identidad de tipo '{expected_identity_type}'."
                    ),
                    profile_id=profile_id,
                    details={"expected_identity_type": expected_identity_type, "profile_type": actual_profile_type},
                    evidence={"type_mismatch": True}
                )
            )
            dependent_criterion = "C15-01" if is_user else "C15-02"
            results.append(
                AuditResult(
                    rule_code=self.rule_code,
                    criterion_code=dependent_criterion,
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification=(
                        "No es posible evaluar la correspondencia de asignaciones debido a la incompatibilidad "
                        "de tipo del perfil de referencia asignado."
                    ),
                    profile_id=profile_id,
                    details={"expected_identity_type": expected_identity_type, "profile_type": actual_profile_type},
                    evidence={"type_mismatch": True}
                )
            )
            return results

        # Perfil presente, activo y con tipo compatible
        results.append(
            AuditResult(
                rule_code=self.rule_code,
                criterion_code="C15-03",
                resource_id=resource_id,
                result_status="Conforme",
                justification=(
                    f"La identidad cuenta con el perfil de acceso activo "
                    f"'{profile.get('profile_code', '')}' (tipo '{actual_profile_type}', versión {profile.get('version', '1.0')})."
                ),
                profile_id=profile_id,
                details={"profile_code": profile.get("profile_code"), "status": profile.get("status")},
                evidence={"profile_id": profile_id, "profile_name": profile.get("profile_name")}
            )
        )

        # 2. Evaluación diferenciada por tipo de identidad
        if is_user:
            results.append(self._evaluate_user_groups(resource_id, attrs, profile_id, context))
        else:
            results.append(self._evaluate_role_trust(resource_id, attrs, profile_id, context))

        return results

    def _evaluate_user_groups(
        self,
        resource_id: Optional[int | str],
        attrs: Dict[str, Any],
        profile_id: Optional[int | str],
        context: Optional[AuditContext]
    ) -> AuditResult:
        """Evalúa la pertenencia a grupos IAM del usuario frente a su perfil esperado."""
        if attrs.get("_invalid_attributes"):
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C15-01",
                resource_id=resource_id,
                result_status="No evaluable",
                justification=f"Atributos de la identidad inválidos o malformados: {attrs.get('_raw_error')}.",
                profile_id=profile_id,
                details={},
                evidence={"invalid_attributes": True}
            )

        # Validar obligatoriedad y formato del atributo 'groups' (no asumir lista vacía si falta)
        if "groups" not in attrs or attrs.get("groups") is None:
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C15-01",
                resource_id=resource_id,
                result_status="No evaluable",
                justification="No se encontró el atributo 'groups' en los metadatos de la identidad de usuario.",
                profile_id=profile_id,
                details={},
                evidence={"missing_attribute": "groups"}
            )

        observed_groups_list = attrs.get("groups")
        if not isinstance(observed_groups_list, list):
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C15-01",
                resource_id=resource_id,
                result_status="No evaluable",
                justification="El atributo 'groups' no posee una estructura de lista válida.",
                profile_id=profile_id,
                details={"raw_type": type(observed_groups_list).__name__},
                evidence={"invalid_groups_structure": True}
            )

        observed_groups: Set[str] = set(str(g).strip() for g in observed_groups_list if str(g).strip())
        expected_groups_list = context.get_expected_groups(profile_id) if (context and profile_id) else []
        
        # Si el perfil no tiene grupos esperados definidos en el catálogo
        if not expected_groups_list:
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C15-01",
                resource_id=resource_id,
                result_status="No evaluable",
                justification="El perfil de referencia activo no cuenta con grupos esperados definidos en el catálogo para contrastar la pertenencia.",
                profile_id=profile_id,
                details={"profile_id": profile_id},
                evidence={"missing_expected_groups": True}
            )

        expected_groups: Set[str] = set(str(g).strip() for g in expected_groups_list if str(g).strip())

        missing_groups = sorted(list(expected_groups - observed_groups))
        additional_groups = sorted(list(observed_groups - expected_groups))

        if missing_groups or additional_groups:
            justification_parts = []
            if additional_groups:
                justification_parts.append(
                    f"Presenta {len(additional_groups)} grupo(s) adicional(es) no autorizado(s) en su perfil: {additional_groups}"
                )
            if missing_groups:
                justification_parts.append(
                    f"Carece de {len(missing_groups)} grupo(s) esperado(s) según su perfil: {missing_groups}"
                )
            justification = "Discrepancia detectada en grupos IAM. " + "; ".join(justification_parts) + "."

            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C15-01",
                resource_id=resource_id,
                result_status="Hallazgo",
                justification=justification,
                profile_id=profile_id,
                details={
                    "observed_groups": sorted(list(observed_groups)),
                    "expected_groups": sorted(list(expected_groups)),
                    "additional_groups": additional_groups,
                    "missing_groups": missing_groups
                },
                evidence={
                    "additional_groups": additional_groups,
                    "missing_groups": missing_groups,
                    "total_observed": len(observed_groups),
                    "total_expected": len(expected_groups)
                }
            )

        return AuditResult(
            rule_code=self.rule_code,
            criterion_code="C15-01",
            resource_id=resource_id,
            result_status="Conforme",
            justification="La pertenencia a grupos IAM del usuario coincide exactamente con los grupos autorizados en su perfil.",
            profile_id=profile_id,
            details={
                "observed_groups": sorted(list(observed_groups)),
                "expected_groups": sorted(list(expected_groups))
            },
            evidence={
                "matching_groups": sorted(list(observed_groups))
            }
        )

    def _evaluate_role_trust(
        self,
        resource_id: Optional[int | str],
        attrs: Dict[str, Any],
        profile_id: Optional[int | str],
        context: Optional[AuditContext]
    ) -> AuditResult:
        """Evalúa la política de confianza del rol IAM frente a los principales y acciones autorizados en el perfil."""
        if attrs.get("_invalid_attributes"):
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C15-02",
                resource_id=resource_id,
                result_status="No evaluable",
                justification=f"Atributos del rol inválidos o malformados: {attrs.get('_raw_error')}.",
                profile_id=profile_id,
                details={},
                evidence={"invalid_attributes": True}
            )

        raw_doc = (
            attrs.get("assume_role_policy_document")
            or attrs.get("trust_policy")
            or attrs.get("AssumeRolePolicyDocument")
        )

        if not raw_doc:
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C15-02",
                resource_id=resource_id,
                result_status="No evaluable",
                justification="No se encontró el documento de política de confianza (AssumeRolePolicyDocument) en los metadatos del rol.",
                profile_id=profile_id,
                details={},
                evidence={"missing_trust_policy": True}
            )

        policy_doc = raw_doc
        if isinstance(raw_doc, str):
            try:
                policy_doc = json.loads(raw_doc)
            except Exception:
                return AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C15-02",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="El documento de política de confianza contiene JSON malformado.",
                    profile_id=profile_id,
                    details={},
                    evidence={"parse_error": "JSON malformado"}
                )

        if not isinstance(policy_doc, dict) or "Statement" not in policy_doc:
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C15-02",
                resource_id=resource_id,
                result_status="No evaluable",
                justification="La política de confianza no posee la estructura JSON estándar de AWS IAM ('Statement' ausente).",
                profile_id=profile_id,
                details={},
                evidence={"invalid_structure": True}
            )

        statements = policy_doc.get("Statement")
        if isinstance(statements, dict):
            statements = [statements]
        elif not isinstance(statements, list):
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C15-02",
                resource_id=resource_id,
                result_status="No evaluable",
                justification="El campo 'Statement' de la política de confianza no es una lista ni un objeto válido.",
                profile_id=profile_id,
                details={},
                evidence={"invalid_statement_type": str(type(statements))}
            )

        if len(statements) == 0:
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C15-02",
                resource_id=resource_id,
                result_status="No evaluable",
                justification="La política de confianza contiene una lista vacía de declaraciones ('Statement').",
                profile_id=profile_id,
                details={},
                evidence={"empty_statement_list": True}
            )

        # Extraer principales y acciones de confianza observadas: tuplas (principal_type, identifier, action)
        observed_trust_entries: Set[Tuple[str, str, str]] = set()

        for stmt in statements:
            if not isinstance(stmt, dict):
                return AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C15-02",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="La política de confianza contiene una declaración ('Statement') no válida o malformada.",
                    profile_id=profile_id,
                    details={},
                    evidence={"invalid_statement": True}
                )

            effect = stmt.get("Effect")
            if effect not in ("Allow", "Deny"):
                return AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C15-02",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="Declaración en política de confianza con valor 'Effect' ausente o no estándar.",
                    profile_id=profile_id,
                    details={},
                    evidence={"invalid_effect": str(effect)}
                )

            # Las declaraciones explícitas Deny en políticas de confianza alteran la evaluación determinista
            if effect == "Deny":
                return AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C15-02",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification=(
                        "La política de confianza contiene una declaración explícita de denegación ('Deny'). "
                        "La resolución de conflictos entre Allow y Deny con posibles condiciones o alcances específicos "
                        "no puede determinarse de forma segura en este evaluador acotado."
                    ),
                    profile_id=profile_id,
                    details={"effect": "Deny"},
                    evidence={"explicit_deny_statement": True}
                )

            # Si contiene condiciones, evaluar si pueden interpretarse de manera segura
            conditions = stmt.get("Condition")
            if conditions is not None and bool(conditions):
                return AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C15-02",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification=(
                        "La política de confianza del rol contiene condiciones o expresiones que no pueden "
                        "interpretarse de manera determinista y segura en esta versión del evaluador."
                    ),
                    profile_id=profile_id,
                    details={"condition_keys": list(conditions.keys()) if isinstance(conditions, dict) else []},
                    evidence={"unsupported_conditions": True}
                )

            # Extraer y validar rigurosamente acciones de confianza (Action)
            raw_action = stmt.get("Action")
            if raw_action is None:
                return AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C15-02",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="Declaración en política de confianza sin atributo 'Action' definido.",
                    profile_id=profile_id,
                    details={},
                    evidence={"missing_action": True}
                )

            actions: List[str] = []
            if isinstance(raw_action, str) and not isinstance(raw_action, bool):
                act_str = raw_action.strip()
                if not act_str:
                    return AuditResult(
                        rule_code=self.rule_code,
                        criterion_code="C15-02",
                        resource_id=resource_id,
                        result_status="No evaluable",
                        justification="El atributo 'Action' contiene un valor de cadena vacío.",
                        profile_id=profile_id,
                        details={},
                        evidence={"empty_action": True}
                    )
                actions.append(act_str)
            elif isinstance(raw_action, list):
                if len(raw_action) == 0:
                    return AuditResult(
                        rule_code=self.rule_code,
                        criterion_code="C15-02",
                        resource_id=resource_id,
                        result_status="No evaluable",
                        justification="El atributo 'Action' contiene una lista vacía.",
                        profile_id=profile_id,
                        details={},
                        evidence={"empty_action_list": True}
                    )
                for act in raw_action:
                    if not isinstance(act, str) or isinstance(act, bool) or not act.strip():
                        return AuditResult(
                            rule_code=self.rule_code,
                            criterion_code="C15-02",
                            resource_id=resource_id,
                            result_status="No evaluable",
                            justification="El atributo 'Action' contiene elementos de tipo no admitido o cadenas vacías.",
                            profile_id=profile_id,
                            details={"element_type": type(act).__name__},
                            evidence={"invalid_action_element": True}
                        )
                    actions.append(act.strip())
            else:
                return AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C15-02",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="El atributo 'Action' de la política de confianza tiene un tipo o formato no admitido.",
                    profile_id=profile_id,
                    details={"action_type": type(raw_action).__name__},
                    evidence={"invalid_action_type": True}
                )

            # Extraer y validar rigurosamente el principal de confianza (Principal)
            principal_obj = stmt.get("Principal")
            if principal_obj is None:
                return AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C15-02",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="Declaración en política de confianza sin atributo 'Principal' definido.",
                    profile_id=profile_id,
                    details={},
                    evidence={"missing_principal": True}
                )

            if principal_obj == "*":
                for act in actions:
                    observed_trust_entries.add(("all", "*", str(act)))
                continue

            if isinstance(principal_obj, dict) and principal_obj.get("AWS") == "*":
                for act in actions:
                    observed_trust_entries.add(("all", "*", str(act)))
                continue

            if not isinstance(principal_obj, dict):
                return AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C15-02",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="Estructura no estándar en el campo 'Principal' de la política de confianza.",
                    profile_id=profile_id,
                    details={"principal_type": type(principal_obj).__name__},
                    evidence={"invalid_principal_structure": True}
                )

            if len(principal_obj) == 0:
                return AuditResult(
                    rule_code=self.rule_code,
                    criterion_code="C15-02",
                    resource_id=resource_id,
                    result_status="No evaluable",
                    justification="El campo 'Principal' contiene un objeto vacío.",
                    profile_id=profile_id,
                    details={},
                    evidence={"empty_principal_object": True}
                )

            for p_type, p_val in principal_obj.items():
                if not isinstance(p_type, str) or isinstance(p_type, bool) or not p_type.strip():
                    return AuditResult(
                        rule_code=self.rule_code,
                        criterion_code="C15-02",
                        resource_id=resource_id,
                        result_status="No evaluable",
                        justification="El tipo de entidad en el campo 'Principal' no tiene un formato válido.",
                        profile_id=profile_id,
                        details={"key_type": type(p_type).__name__},
                        evidence={"invalid_principal_key": True}
                    )
                p_type_norm = p_type.strip().lower()

                identifiers: List[str] = []
                if isinstance(p_val, str) and not isinstance(p_val, bool):
                    val_str = p_val.strip()
                    if not val_str:
                        return AuditResult(
                            rule_code=self.rule_code,
                            criterion_code="C15-02",
                            resource_id=resource_id,
                            result_status="No evaluable",
                            justification="El identificador en el campo 'Principal' es una cadena vacía.",
                            profile_id=profile_id,
                            details={},
                            evidence={"empty_principal_identifier": True}
                        )
                    identifiers.append(val_str)
                elif isinstance(p_val, list):
                    if len(p_val) == 0:
                        return AuditResult(
                            rule_code=self.rule_code,
                            criterion_code="C15-02",
                            resource_id=resource_id,
                            result_status="No evaluable",
                            justification="La lista de identificadores en el campo 'Principal' está vacía.",
                            profile_id=profile_id,
                            details={},
                            evidence={"empty_principal_list": True}
                        )
                    for ident in p_val:
                        if not isinstance(ident, str) or isinstance(ident, bool) or not ident.strip():
                            return AuditResult(
                                rule_code=self.rule_code,
                                criterion_code="C15-02",
                                resource_id=resource_id,
                                result_status="No evaluable",
                                justification="El campo 'Principal' contiene identificadores de tipo no admitido o cadenas vacías.",
                                profile_id=profile_id,
                                details={"element_type": type(ident).__name__},
                                evidence={"invalid_principal_element": True}
                            )
                        identifiers.append(ident.strip())
                else:
                    return AuditResult(
                        rule_code=self.rule_code,
                        criterion_code="C15-02",
                        resource_id=resource_id,
                        result_status="No evaluable",
                        justification="El campo 'Principal' contiene valores internos de formato no admitido.",
                        profile_id=profile_id,
                        details={"value_type": type(p_val).__name__},
                        evidence={"invalid_principal_value_type": True}
                    )

                for ident in identifiers:
                    for act in actions:
                        observed_trust_entries.add((p_type_norm, ident, act))

        # Comparar con los principales y acciones esperados en el perfil de referencia
        expected_records = context.get_expected_trust_principals(profile_id) if (context and profile_id) else []
        if not expected_records:
            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C15-02",
                resource_id=resource_id,
                result_status="No evaluable",
                justification="El perfil de referencia activo no cuenta con principales de confianza esperados definidos en el catálogo para contrastar la política.",
                profile_id=profile_id,
                details={"profile_id": profile_id},
                evidence={"missing_expected_trust_principals": True}
            )

        expected_set: Set[Tuple[str, str, str]] = {
            (
                str(rec.get("principal_type", "")).lower(),
                str(rec.get("principal_identifier", "")),
                str(rec.get("trust_action", "sts:AssumeRole"))
            )
            for rec in expected_records
        }

        diff_unexpected = observed_trust_entries - expected_set
        diff_missing = expected_set - observed_trust_entries

        if diff_unexpected or diff_missing:
            unexpected_display = [f"Principal '{t}:{i}' con acción '{a}'" for t, i, a in sorted(diff_unexpected)]
            missing_display = [f"Principal '{t}:{i}' con acción '{a}'" for t, i, a in sorted(diff_missing)]
            parts = []
            if unexpected_display:
                parts.append(f"Entradas no autorizadas: {unexpected_display}")
            if missing_display:
                parts.append(f"Entradas esperadas ausentes: {missing_display}")

            return AuditResult(
                rule_code=self.rule_code,
                criterion_code="C15-02",
                resource_id=resource_id,
                result_status="Hallazgo",
                justification="Discrepancia en la política de confianza del rol. " + "; ".join(parts) + ".",
                profile_id=profile_id,
                details={
                    "observed": [f"{t}:{i}:{a}" for t, i, a in sorted(observed_trust_entries)],
                    "expected": [f"{t}:{i}:{a}" for t, i, a in sorted(expected_set)],
                    "unexpected": unexpected_display,
                    "missing": missing_display
                },
                evidence={
                    "unexpected_entries": unexpected_display,
                    "missing_entries": missing_display
                }
            )

        return AuditResult(
            rule_code=self.rule_code,
            criterion_code="C15-02",
            resource_id=resource_id,
            result_status="Conforme",
            justification="Las entidades y acciones de confianza autorizadas en la política coinciden exactamente con el perfil de referencia.",
            profile_id=profile_id,
            details={"trust_entries": [f"{t}:{i}:{a}" for t, i, a in sorted(observed_trust_entries)]},
            evidence={"matching_entries": [f"{t}:{i}:{a}" for t, i, a in sorted(observed_trust_entries)]}
        )
