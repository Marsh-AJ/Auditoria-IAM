"""
Pruebas unitarias para la Regla IAM-004 (ISO/IEC 27001:2022 Control 8.5 - Autenticación segura).
Valida la comprobación del estado de MFA para identidades de usuario y exclusión de roles.
"""
import pytest

from src.auditoria_iam.audit.rules.iam_004_secure_authentication import RuleIAM004SecureAuthentication


@pytest.fixture
def rule():
    return RuleIAM004SecureAuthentication()


def test_iam_004_user_with_mfa_enabled_conforme(rule):
    """Verifica que un usuario con MFA habilitado resulte Conforme."""
    user = {
        "id": 1,
        "resource_type": "IAM_USER",
        "attributes": {"mfa_enabled": True}
    }
    results = rule.evaluate(user)
    assert len(results) == 1
    res = results[0]
    assert res.criterion_code == "C85-01"
    assert res.result_status == "Conforme"
    assert "tiene configurado y activo un dispositivo" in res.justification


def test_iam_004_user_without_mfa_hallazgo(rule):
    """Verifica que un usuario con MFA deshabilitado resulte Hallazgo."""
    user = {
        "id": 2,
        "resource_type": "IAM_USER",
        "attributes": {"mfa_enabled": False}
    }
    results = rule.evaluate(user)
    assert len(results) == 1
    res = results[0]
    assert res.criterion_code == "C85-01"
    assert res.result_status == "Hallazgo"
    assert "carece de dispositivo de autenticación multifactor" in res.justification


def test_iam_004_user_missing_mfa_metadata_no_evaluable(rule):
    """Verifica que la ausencia de metadatos de MFA genere No evaluable."""
    user = {
        "id": 3,
        "resource_type": "IAM_USER",
        "attributes": {}
    }
    results = rule.evaluate(user)
    assert len(results) == 1
    res = results[0]
    assert res.criterion_code == "C85-01"
    assert res.result_status == "No evaluable"
    assert "No se dispone de metadatos válidos" in res.justification


def test_iam_004_user_invalid_mfa_value_no_evaluable(rule):
    """Verifica que valores de texto arbitrarios en MFA generen No evaluable."""
    user = {
        "id": 4,
        "resource_type": "IAM_USER",
        "attributes": {"mfa_enabled": "desconocido"}
    }
    results = rule.evaluate(user)
    assert len(results) == 1
    assert results[0].result_status == "No evaluable"


def test_iam_004_user_numeric_mfa_value_rejected(rule):
    """Verifica que valores numéricos (0, 1) sean rechazados y produzcan No evaluable."""
    for num_val in (1, 0, 2, -1):
        user = {
            "id": 5,
            "resource_type": "IAM_USER",
            "attributes": {"mfa_enabled": num_val}
        }
        results = rule.evaluate(user)
        assert len(results) == 1
        assert results[0].result_status == "No evaluable"


def test_iam_004_role_excluded_without_artificial_result(rule):
    """Verifica que identidades de tipo IAM_ROLE sean excluidas sin emitir C85-01 artificial."""
    role = {
        "id": 6,
        "resource_type": "IAM_ROLE",
        "attributes": {"mfa_enabled": True}
    }
    results = rule.evaluate(role)
    assert len(results) == 0  # Lista vacía: exclusión documentada
