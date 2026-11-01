"""
Pruebas unitarias para la capa de acceso a datos (repository.py).
Utiliza mocks para verificar consultas parametrizadas, manejo de resultados vacíos,
manejo de excepciones y garantía de operaciones estrictamente de lectura.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.auditoria_iam.database import (
    get_resources,
    get_resource_by_id,
    get_resource_by_key,
    get_active_rules,
    get_rule_by_code,
    get_rule_by_id,
    get_active_profiles,
    get_profile_by_code,
    get_profile_by_id,
    get_resource_active_profile,
    get_profile_expected_groups,
    get_profile_expected_trust_principals,
    get_audit_runs,
    get_audit_run_by_id,
    get_audit_results_by_run,
    get_findings_by_run,
    get_evidence_by_finding,
    get_evidence_by_audit_result
)


@pytest.fixture
def mock_cursor():
    cursor = MagicMock()
    return cursor


# =============================================================================
# 1. PRUEBAS DE RECURSOS
# =============================================================================

def test_get_resources_simulacion_parameterized():
    """Verifica que get_resources consulte por source_type parametrizado con ('simulacion',)."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            {"id": 1, "resource_key": "ana.operaciones", "source_type": "simulacion"}
        ]
        mock_ctx.return_value.__enter__.return_value = cursor

        results = get_resources(source_type="simulacion")

        assert len(results) == 1
        assert results[0]["resource_key"] == "ana.operaciones"
        cursor.execute.assert_called_once()
        query, params = cursor.execute.call_args[0]
        assert "WHERE source_type = %s" in query
        assert params == ("simulacion",)


def test_get_resources_backward_compatibility():
    """Verifica que get_resources admita user y password por compatibilidad con scripts originales."""
    with patch("src.auditoria_iam.database.repository.get_connection") as mock_get_conn:
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        mock_get_conn.return_value = conn
        cursor.fetchall.return_value = [{"id": 2, "resource_key": "carlos.admin"}]

        results = get_resources("user_test", "pass_test", source_type="simulacion")

        assert len(results) == 1
        mock_get_conn.assert_called_once_with(user="user_test", password="pass_test", db_name=None)
        cursor.close.assert_called_once()
        conn.close.assert_called_once()


def test_get_resource_by_id():
    """Verifica la consulta parametrizada por ID de recurso."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchone.return_value = {"id": 1, "resource_key": "ana.operaciones"}
        mock_ctx.return_value.__enter__.return_value = cursor

        resource = get_resource_by_id(1)

        assert resource is not None
        assert resource["id"] == 1
        cursor.execute.assert_called_once()
        query, params = cursor.execute.call_args[0]
        assert "WHERE id = %s" in query
        assert params == (1,)


def test_get_resource_by_id_empty():
    """Verifica el retorno de None si el recurso no existe."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        mock_ctx.return_value.__enter__.return_value = cursor

        resource = get_resource_by_id(999)

        assert resource is None


def test_get_resource_by_key():
    """Verifica la consulta parametrizada por clave de recurso y fuente."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchone.return_value = {"id": 2, "resource_key": "carlos.admin"}
        mock_ctx.return_value.__enter__.return_value = cursor

        resource = get_resource_by_key("carlos.admin", source_type="simulacion")

        assert resource is not None
        query, params = cursor.execute.call_args[0]
        assert "WHERE resource_key = %s AND source_type = %s" in query
        assert params == ("carlos.admin", "simulacion")


# =============================================================================
# 2. PRUEBAS DE REGLAS DE AUDITORÍA
# =============================================================================

def test_get_active_rules():
    """Verifica que se consulten únicamente reglas activas (is_active = 1)."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            {"id": 1, "rule_code": "IAM-001", "is_active": 1},
            {"id": 2, "rule_code": "IAM-002", "is_active": 1}
        ]
        mock_ctx.return_value.__enter__.return_value = cursor

        rules = get_active_rules()

        assert len(rules) == 2
        query = cursor.execute.call_args[0][0]
        assert "WHERE is_active = 1" in query


def test_get_rule_by_code():
    """Verifica la consulta parametrizada de una regla por código."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchone.return_value = {"id": 1, "rule_code": "IAM-001"}
        mock_ctx.return_value.__enter__.return_value = cursor

        rule = get_rule_by_code("IAM-001")

        assert rule is not None
        query, params = cursor.execute.call_args[0]
        assert "WHERE rule_code = %s" in query
        assert params == ("IAM-001",)


def test_get_rule_by_id():
    """Verifica la consulta parametrizada de una regla por ID."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchone.return_value = {"id": 4, "rule_code": "IAM-004"}
        mock_ctx.return_value.__enter__.return_value = cursor

        rule = get_rule_by_id(4)

        assert rule is not None
        assert rule["rule_code"] == "IAM-004"


# =============================================================================
# 3. PRUEBAS DE PERFILES DE ACCESO
# =============================================================================

def test_get_active_profiles_filtered_by_type():
    """Verifica la consulta parametrizada de perfiles activos filtrados por identity_type."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            {"id": 1, "profile_code": "PRF-USR-OPERACIONES", "identity_type": "user"}
        ]
        mock_ctx.return_value.__enter__.return_value = cursor

        profiles = get_active_profiles(identity_type="user")

        assert len(profiles) == 1
        query, params = cursor.execute.call_args[0]
        assert "WHERE status = 'active' AND identity_type = %s" in query
        assert params == ("user",)


def test_get_active_profiles_all():
    """Verifica la consulta de todos los perfiles activos sin filtro de tipo."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        mock_ctx.return_value.__enter__.return_value = cursor

        profiles = get_active_profiles()

        assert profiles == []
        query, params = cursor.execute.call_args[0]
        assert "WHERE status = 'active'" in query
        assert params == ()


def test_get_resource_active_profile():
    """Verifica la consulta del perfil actualmente vigente para un recurso (valid_to IS NULL)."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchone.return_value = {
            "assignment_id": 10,
            "resource_id": 1,
            "profile_code": "PRF-USR-OPERACIONES",
            "valid_to": None
        }
        mock_ctx.return_value.__enter__.return_value = cursor

        assignment = get_resource_active_profile(1)

        assert assignment is not None
        assert assignment["profile_code"] == "PRF-USR-OPERACIONES"
        query, params = cursor.execute.call_args[0]
        assert "WHERE rap.resource_id = %s" in query
        assert "AND rap.valid_to IS NULL" in query
        assert params == (1,)


def test_get_profile_expected_groups():
    """Verifica la consulta parametrizada de grupos esperados de un perfil."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            {"id": 1, "profile_id": 2, "group_name": "Administrators"}
        ]
        mock_ctx.return_value.__enter__.return_value = cursor

        groups = get_profile_expected_groups(2)

        assert len(groups) == 1
        query, params = cursor.execute.call_args[0]
        assert "WHERE profile_id = %s" in query
        assert params == (2,)


def test_get_profile_expected_trust_principals():
    """Verifica la consulta parametrizada de principales de confianza esperados."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            {"id": 1, "profile_id": 3, "principal_identifier": "ec2.amazonaws.com"}
        ]
        mock_ctx.return_value.__enter__.return_value = cursor

        principals = get_profile_expected_trust_principals(3)

        assert len(principals) == 1
        query, params = cursor.execute.call_args[0]
        assert "WHERE profile_id = %s" in query
        assert params == (3,)


# =============================================================================
# 4. PRUEBAS DE RESULTADOS, HALLAZGOS Y EVIDENCIAS
# =============================================================================

def test_get_audit_runs():
    """Verifica la consulta de ejecuciones de auditoría limitadas."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchall.return_value = [{"id": 4, "status": "COMPLETED"}]
        mock_ctx.return_value.__enter__.return_value = cursor

        runs = get_audit_runs(limit=10)

        assert len(runs) == 1
        query, params = cursor.execute.call_args[0]
        assert "LIMIT %s" in query
        assert params == (10,)


def test_get_audit_results_by_run_filtered():
    """Verifica la consulta de resultados filtrados por ejecución y estado."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            {"id": 1, "audit_run_id": 4, "result_status": "Hallazgo"}
        ]
        mock_ctx.return_value.__enter__.return_value = cursor

        results = get_audit_results_by_run(4, result_status="Hallazgo")

        assert len(results) == 1
        query, params = cursor.execute.call_args[0]
        assert "WHERE ar.audit_run_id = %s AND ar.result_status = %s" in query
        assert params == (4, "Hallazgo")


def test_get_findings_by_run():
    """Verifica la consulta parametrizada de hallazgos por ID de ejecución."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchall.return_value = [{"id": 101, "audit_run_id": 3}]
        mock_ctx.return_value.__enter__.return_value = cursor

        findings = get_findings_by_run(3)

        assert len(findings) == 1
        query, params = cursor.execute.call_args[0]
        assert "WHERE f.audit_run_id = %s" in query
        assert params == (3,)


def test_get_evidence_by_finding():
    """Verifica la consulta parametrizada de evidencias vinculadas a un hallazgo histórico."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchall.return_value = [{"id": 1, "finding_id": 2}]
        mock_ctx.return_value.__enter__.return_value = cursor

        evidence = get_evidence_by_finding(2)

        assert len(evidence) == 1
        query, params = cursor.execute.call_args[0]
        assert "WHERE finding_id = %s" in query
        assert params == (2,)


def test_get_evidence_by_audit_result():
    """Verifica la consulta parametrizada de evidencias vinculadas a un resultado nuevo."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchall.return_value = [{"id": 20, "audit_result_id": 5}]
        mock_ctx.return_value.__enter__.return_value = cursor

        evidence = get_evidence_by_audit_result(5)

        assert len(evidence) == 1
        query, params = cursor.execute.call_args[0]
        assert "WHERE audit_result_id = %s" in query
        assert params == (5,)


# =============================================================================
# 5. SEGURIDAD: AUSENCIA DE OPERACIONES SQL DE ESCRITURA
# =============================================================================

def test_repository_strictly_read_only():
    """
    Inspecciona todas las funciones de consulta del repositorio para garantizar
    que ninguna ejecute sentencias de escritura (INSERT, UPDATE, DELETE, DROP, ALTER).
    """
    import inspect
    import src.auditoria_iam.database.repository as repo

    write_keywords = ["INSERT INTO", "UPDATE ", "DELETE FROM", "DROP TABLE", "ALTER TABLE", "TRUNCATE "]
    
    functions = [
        obj for name, obj in inspect.getmembers(repo, inspect.isfunction)
        if obj.__module__ == repo.__name__
    ]

    for func in functions:
        source = inspect.getsource(func)
        for keyword in write_keywords:
            assert keyword not in source.upper(), (
                f"Violación de seguridad: La función {func.__name__} contiene la sentencia de escritura '{keyword}'."
            )

