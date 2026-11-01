"""
Pruebas unitarias para los modelos del motor de auditoría (models.py).
Verifica validación de estados permitidos, obligatoriedad de campos y conversión de datos.
"""
import pytest

from src.auditoria_iam.audit.models import (
    VALID_STATUSES,
    AuditContext,
    AuditResult,
    extract_resource_attributes,
)


def test_audit_result_valid_statuses():
    """Verifica que los tres estados válidos ('Conforme', 'Hallazgo', 'No evaluable') sean aceptados."""
    for status in ("Conforme", "Hallazgo", "No evaluable"):
        res = AuditResult(
            rule_code="IAM-001",
            criterion_code="C15-01",
            resource_id=1,
            result_status=status,
            justification=f"Resultado en estado {status}"
        )
        assert res.result_status == status


def test_audit_result_invalid_status_raises_error():
    """Verifica que estados no permitidos (ej. 'PASS', 'FAIL', 'WARNING') levanten ValueError."""
    for invalid in ("PASS", "FAIL", "ERROR", "WARNING", "APROBADO", "NO_CONFORME", ""):
        with pytest.raises(ValueError) as excinfo:
            AuditResult(
                rule_code="IAM-001",
                criterion_code="C15-01",
                resource_id=1,
                result_status=invalid,
                justification="Prueba estado inválido"
            )
        assert "Estado de resultado inválido" in str(excinfo.value)


def test_audit_result_missing_required_fields():
    """Verifica que falten campos esenciales levanten ValueError."""
    # Sin rule_code
    with pytest.raises(ValueError) as exc:
        AuditResult(rule_code="", criterion_code="C15-01", resource_id=1, result_status="Conforme", justification="ok")
    assert "rule_code" in str(exc.value)

    # Sin criterion_code
    with pytest.raises(ValueError) as exc:
        AuditResult(rule_code="IAM-001", criterion_code="", resource_id=1, result_status="Conforme", justification="ok")
    assert "criterion_code" in str(exc.value)

    # Justification vacía
    with pytest.raises(ValueError) as exc:
        AuditResult(rule_code="IAM-001", criterion_code="C15-01", resource_id=1, result_status="Conforme", justification="   ")
    assert "justification" in str(exc.value)


def test_audit_result_to_dict():
    """Verifica la serialización correcta del modelo a diccionario."""
    res = AuditResult(
        rule_code="IAM-002",
        criterion_code="C16-01",
        resource_id=10,
        result_status="Conforme",
        justification="Identidad activa y vigente",
        profile_id=2,
        details={"status": "active"},
        evidence={"observed": "active"}
    )
    d = res.to_dict()
    assert d["rule_code"] == "IAM-002"
    assert d["criterion_code"] == "C16-01"
    assert d["resource_id"] == 10
    assert d["result_status"] == "Conforme"
    assert d["profile_id"] == 2
    assert d["details"] == {"status": "active"}
    assert d["evidence"] == {"observed": "active"}


def test_audit_context_lookups():
    """Verifica los métodos de búsqueda y resolución del contexto de auditoría."""
    context = AuditContext(
        profiles={1: {"id": 1, "profile_code": "PRF-TEST", "status": "active"}},
        expected_groups={1: ["GroupA", "GroupB"]},
        expected_trust_principals={1: [{"principal_type": "service", "principal_identifier": "ec2.amazonaws.com"}]},
        resource_profiles={100: 1}
    )

    profile = context.get_profile_for_resource(100)
    assert profile is not None
    assert profile["profile_code"] == "PRF-TEST"

    assert context.get_profile_for_resource(999) is None
    assert context.get_profile_for_resource("invalid") is None

    assert context.get_expected_groups(1) == ["GroupA", "GroupB"]
    assert context.get_expected_groups(999) == []

    principals = context.get_expected_trust_principals(1)
    assert len(principals) == 1
    assert principals[0]["principal_identifier"] == "ec2.amazonaws.com"


def test_extract_resource_attributes():
    """Verifica la extracción segura de atributos en formato dict y JSON serializado."""
    # Dict directo
    assert extract_resource_attributes({"attributes": {"mfa": True}}) == {"mfa": True}

    # JSON serializado
    assert extract_resource_attributes({"attributes": '{"mfa": false, "groups": ["admin"]}'}) == {
        "mfa": False,
        "groups": ["admin"]
    }

    # JSON malformado -> Retorna marcador de atributos inválidos (no dict vacío silencioso)
    malformed = extract_resource_attributes({"attributes": '{bad json}'})
    assert malformed.get("_invalid_attributes") is True

    # Sin campo attributes -> Retorna marcador de atributos ausentes
    missing = extract_resource_attributes({})
    assert missing.get("_missing_attributes") is True

