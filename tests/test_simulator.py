"""
Pruebas unitarias para el módulo simulador de datos (simulator.py).
Verifica que los datos y el contexto simulados produzcan los 3 estados en el motor,
cumplan los catálogos y mantengan la matriz exacta de referencia.
"""
from collections import Counter

from src.auditoria_iam.audit.engine import AuditEngine
from src.auditoria_iam.data_sources.simulator import (
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


def test_simulator_data_integrity():
    """Verifica que el simulador entregue las 10 identidades esperadas y perfiles completos."""
    resources = get_simulated_resources()
    context = get_simulated_audit_context()

    assert len(resources) == 10
    assert len(context.profiles) == 3
    assert len(context.expected_groups) == 2
    assert len(context.expected_trust_principals) == 1


def test_simulator_produces_all_three_statuses_in_engine():
    """Verifica que la ejecución del motor sobre el dataset simulado obtenga Conforme, Hallazgo y No evaluable."""
    engine = AuditEngine()
    resources = get_simulated_resources()
    context = get_simulated_audit_context()

    results = engine.evaluate_all(resources=resources, context=context)

    statuses = {r.result_status for r in results}
    assert "Conforme" in statuses
    assert "Hallazgo" in statuses
    assert "No evaluable" in statuses

    # Contar distribución de resultados
    conforme_count = sum(1 for r in results if r.result_status == "Conforme")
    hallazgo_count = sum(1 for r in results if r.result_status == "Hallazgo")
    no_evaluable_count = sum(1 for r in results if r.result_status == "No evaluable")

    assert conforme_count > 0
    assert hallazgo_count > 0
    assert no_evaluable_count > 0


def test_simulator_get_users_and_roles_filtering():
    """Verifica que get_simulated_users y get_simulated_roles filtren correctamente por tipo."""
    users = get_simulated_users()
    roles = get_simulated_roles()

    assert len(users) == 7
    assert len(roles) == 3
    assert len(users) + len(roles) == 10

    for u in users:
        assert u["resource_type"] == "IAM_USER"
        assert "resource_key" in u
        assert "attributes" in u

    for r in roles:
        assert r["resource_type"] == "IAM_ROLE"
        assert "resource_key" in r
        assert "attributes" in r


def test_simulator_groups_catalog_and_memberships():
    """Verifica que el catálogo de grupos contenga las definiciones y miembros correspondientes."""
    groups = get_simulated_groups()
    assert len(groups) == 6

    group_names = {g["group_name"] for g in groups}
    expected_names = {"Operaciones", "LecturaContratos", "SoporteTI", "SeguridadTI", "Finanzas", "AuditoriaInterna"}
    assert group_names == expected_names

    # Validar membresías cruzadas con recursos
    group_map = {g["group_name"]: g for g in groups}
    assert "ana.operaciones" in group_map["Operaciones"]["members"]
    assert "ana.operaciones" in group_map["LecturaContratos"]["members"]
    assert "carlos.soporte" in group_map["SoporteTI"]["members"]
    assert "carlos.soporte" in group_map["SeguridadTI"]["members"]
    assert "usuario.grupos_discrepantes" in group_map["Finanzas"]["members"]
    assert "usuario.grupos_discrepantes" in group_map["AuditoriaInterna"]["members"]


def test_simulator_policies_catalog():
    """Verifica que el catálogo de políticas técnicas simuladas contenga las políticas esperadas."""
    policies = get_simulated_policies()
    assert len(policies) == 3

    policy_names = {p["policy_name"] for p in policies}
    assert "UpharvenOperacionesS3Policy" in policy_names
    assert "AdministratorAccessSimulated" in policy_names
    assert "UpharvenEC2S3ReadPolicy" in policy_names

    for p in policies:
        assert "policy_document" in p
        doc = p["policy_document"]
        assert "Statement" in doc
        assert isinstance(doc["Statement"], list)


def test_simulator_profiles_catalog():
    """Verifica el catálogo enriquecido de perfiles de referencia autorizados."""
    profiles = get_simulated_profiles()
    assert len(profiles) == 3

    p1 = profiles[1]
    assert p1["profile_code"] == "PRF-USR-OPERACIONES"
    assert p1["expected_groups"] == ["Operaciones", "LecturaContratos"]
    assert p1["expected_trust_principals"] == []

    p2 = profiles[2]
    assert p2["profile_code"] == "PRF-USR-SOPORTE"
    assert p2["expected_groups"] == ["SoporteTI"]

    p3 = profiles[3]
    assert p3["profile_code"] == "PRF-ROL-EC2-OPS"
    assert p3["expected_groups"] == []
    assert len(p3["expected_trust_principals"]) == 1
    assert p3["expected_trust_principals"][0]["principal_identifier"] == "ec2.amazonaws.com"


def test_validate_simulated_data_integrity():
    """Verifica la función de auditoría técnica interna del dataset simulado."""
    report = validate_simulated_data_integrity()

    assert report["valid"] is True
    assert report["total_resources"] == 10
    assert report["users_count"] == 7
    assert report["roles_count"] == 3
    assert report["groups_count"] == 6
    assert report["profiles_count"] == 3
    assert report["policies_count"] == 3
    assert report["issues"] == []
    assert report["degraded_resources_count"] == 8


def test_iam_simulator_data_source_class():
    """Verifica que la clase IAMSimulatorDataSource exponga correctamente la interfaz estática."""
    assert len(IAMSimulatorDataSource.get_resources()) == 10
    assert len(IAMSimulatorDataSource.get_users()) == 7
    assert len(IAMSimulatorDataSource.get_roles()) == 3
    assert len(IAMSimulatorDataSource.get_groups()) == 6
    assert len(IAMSimulatorDataSource.get_policies()) == 3
    assert len(IAMSimulatorDataSource.get_profiles()) == 3

    ctx = IAMSimulatorDataSource.get_audit_context()
    assert len(ctx.profiles) == 3

    report = IAMSimulatorDataSource.validate_integrity()
    assert report["valid"] is True


def test_simulator_reference_matrix_exact_match():
    """
    Verifica que la ejecución completa del motor sobre el dataset simulado
    produzca de manera exacta e invariable la matriz de referencia de 67 evaluaciones:
    36 Conforme (53.73%), 25 No evaluable (37.31%), 6 Hallazgo (8.96%).
    """
    engine = AuditEngine()
    resources = get_simulated_resources()
    context = get_simulated_audit_context()

    results = engine.evaluate_all(resources=resources, context=context)

    assert len(results) == 67

    counts = Counter(r.result_status for r in results)
    assert counts["Conforme"] == 36
    assert counts["No evaluable"] == 25
    assert counts["Hallazgo"] == 6
