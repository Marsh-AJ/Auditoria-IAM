"""
Módulo Principal de Auditoría IAM basada en ISO/IEC 27001:2022.
"""
from src.auditoria_iam.audit.engine import AuditEngine
from src.auditoria_iam.audit.models import (
    VALID_STATUSES,
    AuditContext,
    AuditResult,
    extract_resource_attributes,
)
from src.auditoria_iam.audit.rules import (
    BaseAuditRule,
    RuleIAM001AccessControl,
    RuleIAM002IdentityManagement,
    RuleIAM003AccessRights,
    RuleIAM004SecureAuthentication,
)

__all__ = [
    "AuditEngine",
    "AuditResult",
    "AuditContext",
    "VALID_STATUSES",
    "extract_resource_attributes",
    "BaseAuditRule",
    "RuleIAM001AccessControl",
    "RuleIAM002IdentityManagement",
    "RuleIAM003AccessRights",
    "RuleIAM004SecureAuthentication",
]

