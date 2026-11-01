"""
Pruebas unitarias para la Regla IAM-002 (ISO/IEC 27001:2022 Control 5.16 - Gestión de identidades).
Valida la evaluación de identidades inactivas, umbral configurable y validación numérica estricta.
"""
import pytest

from src.auditoria_iam.audit.rules.iam_002_identity_management import RuleIAM002IdentityManagement


@pytest.fixture
def rule():
    return RuleIAM002IdentityManagement(inactivity_threshold_days=90)


def test_iam_002_recent_activity_conforme(rule):
    """Verifica que una identidad activa con acceso reciente (<= 90 días) sea Conforme."""
    res = {
        "id": 1,
        "resource_status": "active",
        "attributes": {"last_access_days": 15}
    }
    results = rule.evaluate(res)
    assert len(results) == 2
    c16_01, c16_02 = results

    assert c16_01.criterion_code == "C16-01"
    assert c16_01.result_status == "Conforme"

    assert c16_02.criterion_code == "C16-02"
    assert c16_02.result_status == "Conforme"
    assert "dentro del umbral operativo" in c16_02.justification


def test_iam_002_inactivity_exceeds_threshold_hallazgo(rule):
    """Verifica que una inactividad superior al umbral resulte en Hallazgo para C16-02."""
    res = {
        "id": 2,
        "resource_status": "active",
        "attributes": {"last_access_days": 95}
    }
    results = rule.evaluate(res)
    _, c16_02 = results
    assert c16_02.result_status == "Hallazgo"
    assert "superando el umbral operativo definido" in c16_02.justification


def test_iam_002_configurable_threshold():
    """Verifica que el umbral de inactividad sea configurable."""
    custom_rule = RuleIAM002IdentityManagement(inactivity_threshold_days=30)
    res = {
        "id": 3,
        "resource_status": "active",
        "attributes": {"last_access_days": 35}
    }
    results = custom_rule.evaluate(res)
    _, c16_02 = results
    assert c16_02.result_status == "Hallazgo"
    assert "30 días" in c16_02.justification


def test_iam_002_negative_days_rejected(rule):
    """Verifica que números de días negativos sean rechazados y produzcan No evaluable."""
    res = {
        "id": 4,
        "resource_status": "active",
        "attributes": {"last_access_days": -5}
    }
    results = rule.evaluate(res)
    _, c16_02 = results
    assert c16_02.result_status == "No evaluable"
    assert "No se dispone de metadatos válidos" in c16_02.justification


def test_iam_002_decimal_days_rejected(rule):
    """Verifica que valores decimales/flotantes no se conviertan automáticamente a entero."""
    res = {
        "id": 5,
        "resource_status": "active",
        "attributes": {"last_access_days": 15.7}
    }
    results = rule.evaluate(res)
    _, c16_02 = results
    assert c16_02.result_status == "No evaluable"


def test_iam_002_missing_activity_metadata_no_evaluable(rule):
    """Verifica que la falta de metadatos de actividad produzca No evaluable en C16-02."""
    res = {
        "id": 6,
        "resource_status": "active",
        "attributes": {}
    }
    results = rule.evaluate(res)
    _, c16_02 = results
    assert c16_02.result_status == "No evaluable"


def test_iam_002_disabled_status_without_deprovisioning_flaw_no_evaluable(rule):
    """Verifica que una identidad deshabilitada sin metadatos de deficiencia resulte No evaluable."""
    res = {
        "id": 7,
        "resource_status": "disabled",
        "attributes": {"last_access_days": 10}
    }
    results = rule.evaluate(res)
    c16_01, _ = results
    assert c16_01.result_status == "No evaluable"
    assert "No se dispone de metadatos de ciclo de vida para discernir" in c16_01.justification


def test_iam_002_disabled_status_with_deprovisioning_flaw_hallazgo(rule):
    """Verifica que una identidad deshabilitada con deficiencia de desprovisionamiento comprobada resulte Hallazgo."""
    res = {
        "id": 8,
        "resource_status": "disabled",
        "attributes": {"last_access_days": 10, "deprovisioning_flaw": True}
    }
    results = rule.evaluate(res)
    c16_01, _ = results
    assert c16_01.result_status == "Hallazgo"
    assert "deficiencia técnica comprobada en el proceso de desprovisionamiento" in c16_01.justification


def test_iam_002_inactive_status_without_deprovisioning_flaw_no_evaluable(rule):
    """Verifica que una identidad inactiva sin metadatos de deficiencia de desprovisionamiento resulte No evaluable."""
    res = {
        "id": 9,
        "resource_status": "inactive",
        "attributes": {"last_access_days": 10}
    }
    results = rule.evaluate(res)
    c16_01, _ = results
    assert c16_01.result_status == "No evaluable"
    assert "No se dispone de metadatos de ciclo de vida para discernir" in c16_01.justification


def test_iam_002_inactive_status_with_deprovisioning_flaw_hallazgo(rule):
    """Verifica que una identidad inactiva con deficiencia de desprovisionamiento resulte Hallazgo."""
    res = {
        "id": 10,
        "resource_status": "inactive",
        "attributes": {"last_access_days": 10, "deprovisioning_flaw": True}
    }
    results = rule.evaluate(res)
    c16_01, _ = results
    assert c16_01.result_status == "Hallazgo"
    assert "deficiencia técnica comprobada en el proceso de desprovisionamiento" in c16_01.justification


def test_iam_002_threshold_zero_conforme_and_hallazgo():
    """Verifica que un umbral de 0 días sea permitido, produciendo Conforme con 0 días y Hallazgo con >=1 día."""
    rule_zero = RuleIAM002IdentityManagement(inactivity_threshold_days=0)
    
    # 0 días de inactividad con umbral 0 -> Conforme
    res_conforme = {
        "id": 11,
        "resource_status": "active",
        "attributes": {"last_access_days": 0}
    }
    results_conforme = rule_zero.evaluate(res_conforme)
    assert results_conforme[1].result_status == "Conforme"
    
    # 1 día de inactividad con umbral 0 -> Hallazgo
    res_hallazgo = {
        "id": 12,
        "resource_status": "active",
        "attributes": {"last_access_days": 1}
    }
    results_hallazgo = rule_zero.evaluate(res_hallazgo)
    assert results_hallazgo[1].result_status == "Hallazgo"


def test_iam_002_invalid_threshold_types_and_values():
    """Verifica que umbrales negativos, booleanos, flotantes o cadenas levanten ValueError."""
    for invalid_val in (-1, -100, True, False, 10.5, "90", [90], None):
        with pytest.raises(ValueError):
            RuleIAM002IdentityManagement(inactivity_threshold_days=invalid_val)


def test_iam_002_arbitrary_deprovisioning_metadata_rejected(rule):
    """Verifica que valores arbitrarios (cadenas aleatorias, números) en deprovisioning_flaw no se acepten como evidencia."""
    # Cadena no unívoca
    res_str = {
        "id": 13,
        "resource_status": "disabled",
        "attributes": {"last_access_days": 10, "deprovisioning_flaw": "arbitrary_value"}
    }
    results = rule.evaluate(res_str)
    assert results[0].result_status == "No evaluable"

    # Número entero
    res_int = {
        "id": 14,
        "resource_status": "inactive",
        "attributes": {"last_access_days": 10, "deprovisioning_flaw": 123}
    }
    results2 = rule.evaluate(res_int)
    assert results2[0].result_status == "No evaluable"
