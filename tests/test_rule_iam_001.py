"""
Pruebas unitarias para la Regla IAM-001 (ISO/IEC 27001:2022 Control 5.15 - Control de acceso).
Valida la evaluación diferenciada para usuarios y roles frente a perfiles autorizados.
"""
import pytest

from src.auditoria_iam.audit.models import AuditContext
from src.auditoria_iam.audit.rules.iam_001_access_control import RuleIAM001AccessControl


@pytest.fixture
def rule():
    return RuleIAM001AccessControl()


@pytest.fixture
def sample_context():
    return AuditContext(
        profiles={
            1: {"id": 1, "profile_code": "PRF-USER", "identity_type": "user", "status": "active"},
            2: {"id": 2, "profile_code": "PRF-ROLE", "identity_type": "role", "status": "active"},
            3: {"id": 3, "profile_code": "PRF-INACTIVE", "identity_type": "user", "status": "inactive"}
        },
        expected_groups={
            1: ["Operadores", "Lectores"]
        },
        expected_trust_principals={
            2: [{"principal_type": "service", "principal_identifier": "ec2.amazonaws.com", "trust_action": "sts:AssumeRole"}]
        },
        resource_profiles={
            10: 1,  # user con perfil activo
            20: 2,  # role con perfil activo
            30: 3,  # user con perfil inactivo
            40: 2,  # user con perfil incompatible (perfil de tipo role)
            50: 1   # role con perfil incompatible (perfil de tipo user)
        }
    )


def test_iam_001_user_groups_matching_conforme(rule, sample_context):
    """Verifica que un usuario con los grupos exactos del perfil resulte Conforme."""
    user = {
        "id": 10,
        "resource_type": "IAM_USER",
        "attributes": {"groups": ["Operadores", "Lectores"]}
    }
    results = rule.evaluate(user, context=sample_context)
    assert len(results) == 2
    c15_03, c15_01 = results

    assert c15_03.criterion_code == "C15-03"
    assert c15_03.result_status == "Conforme"

    assert c15_01.criterion_code == "C15-01"
    assert c15_01.result_status == "Conforme"
    assert "coincide exactamente" in c15_01.justification


def test_iam_001_user_additional_group_hallazgo(rule, sample_context):
    """Verifica que un usuario con grupos adicionales no autorizados resulte Hallazgo."""
    user = {
        "id": 10,
        "resource_type": "IAM_USER",
        "attributes": {"groups": ["Operadores", "Lectores", "Administrators"]}
    }
    results = rule.evaluate(user, context=sample_context)
    c15_03, c15_01 = results
    assert c15_01.result_status == "Hallazgo"
    assert "adicional(es) no autorizado(s)" in c15_01.justification
    assert "Administrators" in c15_01.evidence["additional_groups"]


def test_iam_001_user_missing_groups_attribute_no_evaluable(rule, sample_context):
    """Verifica que un usuario sin atributo 'groups' no sea interpretado como lista vacía, sino No evaluable."""
    user = {
        "id": 10,
        "resource_type": "IAM_USER",
        "attributes": {}  # Sin atributo groups
    }
    results = rule.evaluate(user, context=sample_context)
    c15_03, c15_01 = results
    assert c15_03.result_status == "Conforme"
    assert c15_01.result_status == "No evaluable"
    assert "No se encontró el atributo 'groups'" in c15_01.justification


def test_iam_001_user_wrong_profile_type_no_evaluable(rule, sample_context):
    """Verifica que un usuario vinculado a un perfil de tipo 'role' resulte No evaluable por incompatibilidad."""
    user = {
        "id": 40,  # Asignado a profile 2 (identity_type: 'role')
        "resource_type": "IAM_USER",
        "attributes": {"groups": ["Operadores"]}
    }
    results = rule.evaluate(user, context=sample_context)
    c15_03, c15_01 = results
    assert c15_03.result_status == "No evaluable"
    assert "incompatible con la identidad de tipo 'user'" in c15_03.justification
    assert c15_01.result_status == "No evaluable"


def test_iam_001_role_matching_principal_and_action_conforme(rule, sample_context):
    """Verifica que un rol con principal y acción coincidentes con el perfil resulte Conforme."""
    role = {
        "id": 20,
        "resource_type": "IAM_ROLE",
        "attributes": {
            "assume_role_policy_document": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
        }
    }
    results = rule.evaluate(role, context=sample_context)
    c15_03, c15_02 = results
    assert c15_03.result_status == "Conforme"
    assert c15_02.result_status == "Conforme"
    assert "coinciden exactamente" in c15_02.justification


def test_iam_001_role_different_action_hallazgo(rule, sample_context):
    """Verifica que un rol con acción de confianza diferente (ej. sts:TagSession en vez de sts:AssumeRole) resulte Hallazgo."""
    role = {
        "id": 20,
        "resource_type": "IAM_ROLE",
        "attributes": {
            "assume_role_policy_document": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:TagSession"
                    }
                ]
            }
        }
    }
    results = rule.evaluate(role, context=sample_context)
    c15_03, c15_02 = results
    assert c15_02.result_status == "Hallazgo"
    assert "Discrepancia en la política de confianza" in c15_02.justification


def test_iam_001_role_unsupported_condition_no_evaluable(rule, sample_context):
    """Verifica que una condición de confianza compleja produzca No evaluable."""
    role = {
        "id": 20,
        "resource_type": "IAM_ROLE",
        "attributes": {
            "assume_role_policy_document": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                        "Condition": {"StringLike": {"aws:PrincipalTag/Dept": "Fin*"}}
                    }
                ]
            }
        }
    }
    results = rule.evaluate(role, context=sample_context)
    c15_03, c15_02 = results
    assert c15_02.result_status == "No evaluable"
    assert "contiene condiciones o expresiones que no pueden interpretarse" in c15_02.justification


def test_iam_001_role_malformed_trust_policy_no_evaluable(rule, sample_context):
    """Verifica que una política de confianza malformada (JSON inválido) retorne No evaluable."""
    role = {
        "id": 20,
        "resource_type": "IAM_ROLE",
        "attributes": {
            "assume_role_policy_document": "{bad json syntax}"
        }
    }
    results = rule.evaluate(role, context=sample_context)
    c15_03, c15_02 = results
    assert c15_02.result_status == "No evaluable"
    assert "JSON malformado" in c15_02.justification


def test_iam_001_user_profile_no_expected_groups_no_evaluable(rule):
    """Verifica que un perfil activo de usuario sin grupos esperados definidos en el catálogo retorne No evaluable."""
    context = AuditContext(
        profiles={1: {"id": 1, "profile_code": "PRF-VACIO", "identity_type": "user", "status": "active"}},
        expected_groups={},  # Sin grupos esperados
        resource_profiles={10: 1}
    )
    user = {
        "id": 10,
        "resource_type": "IAM_USER",
        "attributes": {"groups": ["Operadores"]}
    }
    results = rule.evaluate(user, context=context)
    c15_03, c15_01 = results
    assert c15_03.result_status == "Conforme"
    assert c15_01.result_status == "No evaluable"
    assert "no cuenta con grupos esperados definidos" in c15_01.justification


def test_iam_001_role_profile_no_expected_trust_principals_no_evaluable(rule):
    """Verifica que un perfil activo de rol sin principales de confianza esperados retorne No evaluable."""
    context = AuditContext(
        profiles={2: {"id": 2, "profile_code": "PRF-ROL-VACIO", "identity_type": "role", "status": "active"}},
        expected_trust_principals={},  # Sin principales esperados
        resource_profiles={20: 2}
    )
    role = {
        "id": 20,
        "resource_type": "IAM_ROLE",
        "attributes": {
            "assume_role_policy_document": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
        }
    }
    results = rule.evaluate(role, context=context)
    c15_03, c15_02 = results
    assert c15_03.result_status == "Conforme"
    assert c15_02.result_status == "No evaluable"
    assert "no cuenta con principales de confianza esperados" in c15_02.justification


def test_iam_001_unknown_resource_type_no_evaluable(rule, sample_context):
    """Verifica que un tipo de recurso desconocido (no USER ni ROLE) retorne No evaluable en C15-03 y dependiente."""
    unknown_resource = {
        "id": 10,
        "resource_type": "IAM_POLICY",
        "attributes": {"groups": ["Operadores"]}
    }
    results = rule.evaluate(unknown_resource, context=sample_context)
    c15_03, c15_01 = results
    assert c15_03.result_status == "No evaluable"
    assert "Tipo de recurso 'IAM_POLICY' no soportado" in c15_03.justification
    assert c15_01.result_status == "No evaluable"


def test_iam_001_role_trust_policy_explicit_deny_no_evaluable(rule, sample_context):
    """Verifica que una política de confianza con declaración explícita Deny retorne No evaluable."""
    role = {
        "id": 20,
        "resource_type": "IAM_ROLE",
        "attributes": {
            "assume_role_policy_document": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Deny",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
        }
    }
    results = rule.evaluate(role, context=sample_context)
    c15_03, c15_02 = results
    assert c15_02.result_status == "No evaluable"
    assert "declaración explícita de denegación ('Deny')" in c15_02.justification


def test_iam_001_role_trust_policy_empty_statement_no_evaluable(rule, sample_context):
    """Verifica que una política de confianza con Statement vacío retorne No evaluable en C15-02."""
    role = {
        "id": 20,
        "resource_type": "IAM_ROLE",
        "attributes": {
            "assume_role_policy_document": {
                "Version": "2012-10-17",
                "Statement": []
            }
        }
    }
    results = rule.evaluate(role, context=sample_context)
    c15_03, c15_02 = results
    assert c15_02.result_status == "No evaluable"
    assert "lista vacía de declaraciones" in c15_02.justification


def test_iam_001_role_trust_policy_numeric_principal_no_evaluable(rule, sample_context):
    """Verifica que un Principal con valor numérico directo retorne No evaluable."""
    role = {
        "id": 20,
        "resource_type": "IAM_ROLE",
        "attributes": {
            "assume_role_policy_document": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": 123456789012,
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
        }
    }
    results = rule.evaluate(role, context=sample_context)
    c15_03, c15_02 = results
    assert c15_02.result_status == "No evaluable"
    assert "Estructura no estándar en el campo 'Principal'" in c15_02.justification


def test_iam_001_role_trust_policy_numeric_internal_principal_no_evaluable(rule, sample_context):
    """Verifica que un Principal con valor interno numérico dentro del diccionario retorne No evaluable."""
    role = {
        "id": 20,
        "resource_type": "IAM_ROLE",
        "attributes": {
            "assume_role_policy_document": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": 123456789012},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
        }
    }
    results = rule.evaluate(role, context=sample_context)
    c15_03, c15_02 = results
    assert c15_02.result_status == "No evaluable"
    assert "valores internos de formato no admitido" in c15_02.justification


def test_iam_001_role_trust_policy_invalid_action_element_type_no_evaluable(rule, sample_context):
    """Verifica que una Action con elementos numéricos o de tipo no admitido retorne No evaluable."""
    role = {
        "id": 20,
        "resource_type": "IAM_ROLE",
        "attributes": {
            "assume_role_policy_document": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": ["sts:AssumeRole", 999]
                    }
                ]
            }
        }
    }
    results = rule.evaluate(role, context=sample_context)
    c15_03, c15_02 = results
    assert c15_02.result_status == "No evaluable"
    assert "elementos de tipo no admitido" in c15_02.justification
