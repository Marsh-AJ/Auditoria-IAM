"""
Pruebas unitarias para el motor central de auditoría (engine.py).
Verifica registro de reglas, ejecución individual y conjunta, y captura defensiva de errores.
"""
import pytest

from src.auditoria_iam.audit.engine import AuditEngine
from src.auditoria_iam.audit.models import AuditContext, AuditResult
from src.auditoria_iam.audit.rules.base import BaseAuditRule


class DummyFailingRule(BaseAuditRule):
    """Regla simulada que detona una excepción inesperada para probar captura defensiva."""
    @property
    def rule_code(self) -> str:
        return "TEST-FAIL"

    @property
    def rule_name(self) -> str:
        return "Regla con fallo forzado"

    @property
    def iso_control(self) -> str:
        return "9.99"

    @property
    def default_severity(self) -> str:
        return "BAJA"

    def evaluate(self, resource, context=None):
        raise ZeroDivisionError("Error simulado de cálculo")


def test_audit_engine_initializes_with_default_rules():
    """Verifica que el motor inicialice automáticamente con las 4 reglas estándar."""
    engine = AuditEngine()
    rules = engine.list_rules()
    assert len(rules) == 4
    codes = [r.rule_code for r in rules]
    assert "IAM-001" in codes
    assert "IAM-002" in codes
    assert "IAM-003" in codes
    assert "IAM-004" in codes


def test_audit_engine_register_custom_rule():
    """Verifica que sea posible registrar nuevas reglas sin alterar el motor."""
    engine = AuditEngine(auto_register_default_rules=False)
    assert len(engine.list_rules()) == 0

    engine.register_rule(DummyFailingRule())
    assert len(engine.list_rules()) == 1
    assert engine.get_rule("TEST-FAIL") is not None


def test_audit_engine_invalid_rule_type():
    """Verifica que registrar un objeto que no herede de BaseAuditRule lance TypeError."""
    engine = AuditEngine()
    with pytest.raises(TypeError):
        engine.register_rule("not_a_rule")


def test_audit_engine_evaluate_single_rule():
    """Verifica la ejecución de una regla individualmente."""
    engine = AuditEngine()
    resource = {
        "id": 1,
        "resource_type": "IAM_USER",
        "attributes": {"mfa_enabled": True}
    }
    # Solo ejecutar IAM-004
    results = engine.evaluate_resource(resource, rule_codes=["IAM-004"])
    assert len(results) == 1
    assert results[0].rule_code == "IAM-004"
    assert results[0].result_status == "Conforme"


def test_audit_engine_evaluate_all_rules():
    """Verifica la ejecución conjunta de las 4 reglas sobre un recurso."""
    engine = AuditEngine()
    context = AuditContext(
        profiles={1: {"id": 1, "profile_code": "PRF-TEST", "status": "active"}},
        expected_groups={1: ["Operadores"]},
        resource_profiles={1: 1}
    )
    resource = {
        "id": 1,
        "resource_type": "IAM_USER",
        "resource_status": "active",
        "attributes": {
            "groups": ["Operadores"],
            "last_access_days": 10,
            "mfa_enabled": True,
            "is_admin": False
        }
    }
    results = engine.evaluate_resource(resource, context=context)
    # IAM-001: 2 resultados (C15-03, C15-01)
    # IAM-002: 2 resultados (C16-01, C16-02)
    # IAM-003: 2 resultados (C18-01, C18-02)
    # IAM-004: 1 resultado (C85-01)
    assert len(results) == 7
    rule_codes = {r.rule_code for r in results}
    assert rule_codes == {"IAM-001", "IAM-002", "IAM-003", "IAM-004"}


def test_audit_engine_evaluate_all_resources():
    """Verifica la evaluación en lote de una colección de recursos."""
    engine = AuditEngine()
    resources = [
        {"id": 1, "resource_type": "IAM_USER", "attributes": {"mfa_enabled": True}},
        {"id": 2, "resource_type": "IAM_USER", "attributes": {"mfa_enabled": False}}
    ]
    results = engine.evaluate_all(resources, rule_codes=["IAM-004"])
    assert len(results) == 2
    assert results[0].result_status == "Conforme"
    assert results[1].result_status == "Hallazgo"


def test_audit_engine_defensive_error_handling():
    """Verifica que una excepción en una regla no aborte el motor ni se convierta en Conforme."""
    engine = AuditEngine(auto_register_default_rules=False)
    engine.register_rule(DummyFailingRule())

    resource = {"id": 1, "resource_type": "IAM_USER"}
    results = engine.evaluate_resource(resource)

    assert len(results) == 1
    res = results[0]
    assert res.result_status == "No evaluable"
    assert "Error durante la ejecución técnica de la regla TEST-FAIL: ZeroDivisionError" in res.justification
    assert res.evidence["error_type"] == "ZeroDivisionError"


def test_audit_engine_unknown_rule_code_raises_key_error():
    """Verifica que solicitar un código de regla inexistente levante KeyError."""
    engine = AuditEngine()
    with pytest.raises(KeyError) as exc:
        engine.evaluate_resource({"id": 1}, rule_codes=["IAM-999"])
    assert "IAM-999" in str(exc.value)
