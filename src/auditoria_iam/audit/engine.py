"""
Motor Central de Auditoría Algorítmica IAM.
Coordina la ejecución desacoplada de reglas técnicas frente a identidades y recursos,
recopilando resultados uniformes con captura defensiva de errores.
"""
import logging
from typing import Any, Dict, List, Optional, Sequence

from src.auditoria_iam.audit.models import AuditContext, AuditResult
from src.auditoria_iam.audit.rules.base import BaseAuditRule
from src.auditoria_iam.audit.rules.iam_001_access_control import RuleIAM001AccessControl
from src.auditoria_iam.audit.rules.iam_002_identity_management import RuleIAM002IdentityManagement
from src.auditoria_iam.audit.rules.iam_003_access_rights import RuleIAM003AccessRights
from src.auditoria_iam.audit.rules.iam_004_secure_authentication import RuleIAM004SecureAuthentication

logger = logging.getLogger(__name__)


class AuditEngine:
    """
    Motor algorítmico central del sistema de auditoría.
    Gestiona el registro de reglas técnicas, ejecución individual o conjunta,
    y generación uniforme de resultados sin dependencias directas de MySQL o AWS.
    """

    def __init__(self, auto_register_default_rules: bool = True) -> None:
        self._rules: Dict[str, BaseAuditRule] = {}
        if auto_register_default_rules:
            self.register_rule(RuleIAM001AccessControl())
            self.register_rule(RuleIAM002IdentityManagement())
            self.register_rule(RuleIAM003AccessRights())
            self.register_rule(RuleIAM004SecureAuthentication())

    def register_rule(self, rule: BaseAuditRule) -> None:
        """Registra una nueva regla en el catálogo del motor."""
        if not isinstance(rule, BaseAuditRule):
            raise TypeError("La regla debe heredar de BaseAuditRule.")
        self._rules[rule.rule_code] = rule

    def get_rule(self, rule_code: str) -> Optional[BaseAuditRule]:
        """Obtiene una regla registrada a partir de su código."""
        return self._rules.get(rule_code)

    def list_rules(self) -> List[BaseAuditRule]:
        """Retorna la lista de reglas actualmente registradas en el motor."""
        return list(self._rules.values())

    def evaluate_resource(
        self,
        resource: Dict[str, Any],
        context: Optional[AuditContext] = None,
        rule_codes: Optional[Sequence[str]] = None
    ) -> List[AuditResult]:
        """
        Evalúa un único recurso frente a las reglas seleccionadas (o todas si no se especifica).
        
        Args:
            resource: Datos y metadatos de la identidad IAM.
            context: Contexto de perfiles de referencia autorizados.
            rule_codes: Lista opcional de códigos de regla a ejecutar (ej. ['IAM-001']).
            
        Returns:
            Lista de resultados AuditResult generados para el recurso.
        """
        results: List[AuditResult] = []
        selected_rules = self._get_selected_rules(rule_codes)

        resource_id = resource.get("id")

        for rule in selected_rules:
            try:
                rule_results = rule.evaluate(resource=resource, context=context)
                results.extend(rule_results)
            except Exception as exc:
                # Control defensivo de excepciones: jamás ocultar ni convertir a Conforme
                logger.error(f"Error imprevisto ejecutando {rule.rule_code} en recurso {resource_id}: {exc}")
                results.append(
                    AuditResult(
                        rule_code=rule.rule_code,
                        criterion_code=f"ERR-{rule.iso_control}",
                        resource_id=resource_id,
                        result_status="No evaluable",
                        justification=f"Error durante la ejecución técnica de la regla {rule.rule_code}: {type(exc).__name__}.",
                        profile_id=None,
                        details={"error_type": type(exc).__name__, "rule_code": rule.rule_code},
                        evidence={"error_type": type(exc).__name__}
                    )
                )

        return results

    def evaluate_all(
        self,
        resources: List[Dict[str, Any]],
        context: Optional[AuditContext] = None,
        rule_codes: Optional[Sequence[str]] = None
    ) -> List[AuditResult]:
        """
        Evalúa una colección de recursos IAM frente a las reglas seleccionadas.
        
        Args:
            resources: Colección de recursos e identidades IAM a auditar.
            context: Contexto de perfiles de referencia autorizados.
            rule_codes: Filtro opcional de reglas a ejecutar.
            
        Returns:
            Lista uniforme con la totalidad de resultados AuditResult.
        """
        all_results: List[AuditResult] = []
        for resource in resources:
            res_results = self.evaluate_resource(resource=resource, context=context, rule_codes=rule_codes)
            all_results.extend(res_results)
        return all_results

    def _get_selected_rules(self, rule_codes: Optional[Sequence[str]]) -> List[BaseAuditRule]:
        """Filtra y ordena las reglas a ejecutar según los códigos solicitados."""
        if rule_codes is None:
            return list(self._rules.values())

        selected: List[BaseAuditRule] = []
        for code in rule_codes:
            if code in self._rules:
                selected.append(self._rules[code])
            else:
                raise KeyError(f"La regla de auditoría con código '{code}' no está registrada en el motor.")
        return selected

