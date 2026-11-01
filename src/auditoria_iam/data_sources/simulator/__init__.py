"""
Paquete Simulador de Datos IAM para Auditoría ISO/IEC 27001.
"""
from src.auditoria_iam.data_sources.simulator.simulator import (
    IAMSimulatorDataSource,
    get_simulated_audit_context,
    get_simulated_groups,
    get_simulated_policies,
    get_simulated_profiles,
    get_simulated_resources,
    get_simulated_roles,
    get_simulated_users,
    validate_simulated_data_integrity,
)

__all__ = [
    "IAMSimulatorDataSource",
    "get_simulated_audit_context",
    "get_simulated_groups",
    "get_simulated_policies",
    "get_simulated_profiles",
    "get_simulated_resources",
    "get_simulated_roles",
    "get_simulated_users",
    "validate_simulated_data_integrity",
]
