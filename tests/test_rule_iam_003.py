"""
Pruebas unitarias para la Regla IAM-003 (ISO/IEC 27001:2022 Control 5.18 - Derechos de acceso).
Valida la detección de permisos administrativos irrestrictos y la rigurosidad de C18-02 sin falsos conformes.
"""
import pytest

from src.auditoria_iam.audit.models import AuditContext
from src.auditoria_iam.audit.rules.iam_003_access_rights import RuleIAM003AccessRights


@pytest.fixture
def rule():
    return RuleIAM003AccessRights()


@pytest.fixture
def sample_context():
    return AuditContext(
        profiles={
            1: {"id": 1, "profile_code": "PRF-DEV", "identity_type": "user", "status": "active"}
        },
        resource_profiles={10: 1}
    )


def test_iam_003_unrestricted_admin_star_action_resource_hallazgo(rule, sample_context):
    """Verifica que una política con Action: * y Resource: * genere Hallazgo en C18-01."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "*",
                            "Resource": "*"
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01, c18_02 = results
    assert c18_01.criterion_code == "C18-01"
    assert c18_01.result_status == "Hallazgo"
    assert "permisos irrestrictos globales" in c18_01.justification


def test_iam_003_unrestricted_iam_star_hallazgo(rule, sample_context):
    """Verifica que una política con Action: iam:* y Resource: * genere Hallazgo en C18-01."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["iam:*"],
                            "Resource": "*"
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "Hallazgo"
    assert "capacidad técnica de modificación irrestricta de IAM" in str(c18_01.evidence)


def test_iam_003_scoped_permissions_without_unrestricted_wildcards_conforme(rule, sample_context):
    """Verifica que permisos acotados con comodines específicos (ej. s3:Get*) sean Conformes en C18-01."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["s3:GetObject*", "s3:ListBucket"],
                            "Resource": "arn:aws:s3:::my-bucket/*"
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01, c18_02 = results
    assert c18_01.result_status == "Conforme"
    assert "no presentan los patrones específicos de permisos irrestrictos globales evaluados" in c18_01.justification


def test_iam_003_invalid_json_policy_no_evaluable(rule, sample_context):
    """Verifica que una política técnica con sintaxis JSON inválida resulte No evaluable."""
    res = {
        "id": 10,
        "attributes": {
            "policies": ["{invalid json format:"]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "JSON malformada" in c18_01.justification


def test_iam_003_incomplete_statement_no_evaluable(rule, sample_context):
    """Verifica que una declaración incompleta (sin Resource o Action) resulte No evaluable."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "s3:GetObject"
                            # Falta Resource
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "sin atributos obligatorios 'Action' o 'Resource'" in c18_01.justification


def test_iam_003_unsupported_condition_no_evaluable(rule, sample_context):
    """Verifica que políticas con condiciones no soportables con certeza resulten No evaluables."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "s3:GetObject",
                            "Resource": "arn:aws:s3:::bucket/*",
                            "Condition": {"StringEquals": {"aws:username": "ana"}}
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "contiene condiciones de autorización que no pueden interpretarse" in c18_01.justification


def test_iam_003_c18_02_always_no_evaluable_without_expected_catalog(rule, sample_context):
    """Verifica que C18-02 no devuelva Conforme sin una comparación real frente a un catálogo formal de permisos."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["s3:GetObject"],
                            "Resource": "arn:aws:s3:::my-bucket/*"
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    _, c18_02 = results
    assert c18_02.criterion_code == "C18-02"
    assert c18_02.result_status == "No evaluable"
    assert "El perfil de referencia no cuenta actualmente con un catálogo formal de permisos" in c18_02.justification
    assert c18_02.evidence["missing_expected_permissions_specification"] is True


def test_iam_003_simulated_flags_do_not_substitute_json_analysis(rule, sample_context):
    """Verifica que banderas simuladas como 'is_admin=False' no sustituyan la ausencia de políticas."""
    res = {
        "id": 10,
        "attributes": {
            "is_admin": False
            # Sin políticas
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01, c18_02 = results
    assert c18_01.result_status == "No evaluable"
    assert "No se dispone de documentos de política técnica JSON" in c18_01.justification


def test_iam_003_administrator_access_name_without_json_policy_no_evaluable(rule, sample_context):
    """Verifica que un nombre de política como 'AdministratorAccess' sin documento JSON resulte No evaluable."""
    res = {
        "id": 10,
        "attributes": {
            "attached_policy_names": ["AdministratorAccess"]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "No se dispone de documentos de política técnica JSON" in c18_01.justification


def test_iam_003_empty_statement_list_no_evaluable(rule, sample_context):
    """Verifica que una política técnica con lista vacía de Statement resulte No evaluable."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": []
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "lista vacía de declaraciones" in c18_01.justification


def test_iam_003_not_action_not_resource_no_evaluable(rule, sample_context):
    """Verifica que políticas con NotAction o NotResource produzcan No evaluable."""
    res_not_action = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "NotAction": "s3:DeleteBucket",
                            "Resource": "*"
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res_not_action, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "NotAction" in c18_01.justification

    res_not_resource = {
        "id": 11,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "s3:GetObject",
                            "NotResource": "arn:aws:s3:::secret/*"
                        }
                    ]
                }
            ]
        }
    }
    results2 = rule.evaluate(res_not_resource, context=sample_context)
    assert results2[0].result_status == "No evaluable"
    assert "NotResource" in results2[0].justification


def test_iam_003_action_with_number_no_evaluable(rule, sample_context):
    """Verifica que una política con Action numérico produzca No evaluable."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": 123,
                            "Resource": "arn:aws:s3:::my-bucket/*"
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "estructuras no admitidas" in c18_01.justification


def test_iam_003_resource_with_boolean_no_evaluable(rule, sample_context):
    """Verifica que una política con Resource booleano produzca No evaluable."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "s3:GetObject",
                            "Resource": True
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "estructuras no admitidas" in c18_01.justification


def test_iam_003_action_mixed_elements_no_evaluable(rule, sample_context):
    """Verifica que una lista de Action con elementos mixtos (cadena y número) produzca No evaluable."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["s3:GetObject", 100],
                            "Resource": "arn:aws:s3:::my-bucket/*"
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "estructuras no admitidas" in c18_01.justification


def test_iam_003_resource_empty_list_no_evaluable(rule, sample_context):
    """Verifica que una lista de Resource vacía produzca No evaluable."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "s3:GetObject",
                            "Resource": []
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "estructuras no admitidas" in c18_01.justification


def test_iam_003_empty_condition_no_evaluable(rule, sample_context):
    """Verifica que una declaración con propiedad Condition vacía {} retorne No evaluable."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "s3:GetObject",
                            "Resource": "arn:aws:s3:::my-bucket/*",
                            "Condition": {}
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "propiedad 'Condition'" in c18_01.justification


def test_iam_003_invalid_condition_type_no_evaluable(rule, sample_context):
    """Verifica que una declaración con Condition de tipo inválido (ej. número) retorne No evaluable."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "s3:GetObject",
                            "Resource": "arn:aws:s3:::my-bucket/*",
                            "Condition": 123
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "propiedad 'Condition'" in c18_01.justification


def test_iam_003_malformed_statement_element_no_evaluable(rule, sample_context):
    """Verifica que una declaración que no sea un objeto JSON retorne No evaluable."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": ["string statement not a dict"]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "inválida o malformada" in c18_01.justification


def test_iam_003_unrelated_missing_attribute_does_not_discard_policies(rule, sample_context):
    """Verifica que la ausencia de atributos ajenos a políticas (como groups) no descarte políticas válidas."""
    res = {
        "id": 10,
        "attributes": {
            # groups no está presente
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["s3:GetObject"],
                            "Resource": "arn:aws:s3:::upharven-datos/*"
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "Conforme"
    assert "no presentan los patrones específicos" in c18_01.justification


def test_iam_003_deny_statement_valid_structure_no_hallazgo(rule, sample_context):
    """Verifica que una declaración Deny con estructura válida no genere un Hallazgo."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Deny",
                            "Action": "*",
                            "Resource": "*"
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status != "Hallazgo"
    assert c18_01.result_status == "Conforme"


def test_iam_003_deny_statement_missing_resource_no_evaluable(rule, sample_context):
    """Verifica que una declaración Deny a la que le falta Resource retorne No evaluable."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Deny",
                            "Action": "s3:DeleteBucket"
                            # Falta Resource
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "sin atributos obligatorios" in c18_01.justification


def test_iam_003_deny_statement_numeric_action_no_evaluable(rule, sample_context):
    """Verifica que una declaración Deny con Action numérico retorne No evaluable."""
    res = {
        "id": 10,
        "attributes": {
            "policies": [
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Deny",
                            "Action": 12345,
                            "Resource": "*"
                        }
                    ]
                }
            ]
        }
    }
    results = rule.evaluate(res, context=sample_context)
    c18_01 = results[0]
    assert c18_01.result_status == "No evaluable"
    assert "estructuras no admitidas" in c18_01.justification
