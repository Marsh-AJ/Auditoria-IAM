"""
Pruebas unitarias para la capa de persistencia e integración relacional de auditorías en MySQL.
Verifica:
1. Inserción atómica en audit_runs, audit_results, findings y audit_evidence.
2. Resolución segura de recursos mediante (resource_key, source_type) cuando los IDs del simulador difieren de MySQL.
3. Rechazo estricto y rollback inmediato ante recursos inexistentes o ambiguos (sin fallback a ID 1).
4. Rechazo estricto y rollback inmediato ante reglas faltantes en audit_rules (sin IDs de respaldo).
5. Asociación de perfiles por correspondencia inequívoca de profile_code (o NULL si no corresponde).
6. Cumplimiento de la restricción chk_evidence_target (exclusión mutua entre finding_id y audit_result_id).
7. Control transaccional completo (commit/rollback atómico).
8. Consulta de historial y reconstrucción de resultados en AuditService.
9. Ausencia total de sentencias INSERT, UPDATE o DELETE sobre las tablas de catálogo (resources, audit_rules, access_profiles).
"""
from datetime import datetime
import inspect
import json
from unittest.mock import MagicMock, call, patch

import pytest

from src.auditoria_iam.application.audit_service import AuditService
from src.auditoria_iam.audit.models import AuditContext, AuditResult
from src.auditoria_iam.database.persistence import save_audit_run
from src.auditoria_iam.data_sources.simulator.simulator import (
    IAMSimulatorDataSource,
    get_simulated_resources,
)


@pytest.fixture
def sample_results():
    """Genera un lote controlado de AuditResult para validación de persistencia."""
    return [
        AuditResult(
            rule_code="IAM-001",
            criterion_code="C15-01",
            resource_id=1,
            result_status="Conforme",
            justification="Correspondencia exacta de grupos asignados.",
            profile_id=1,
            details={"status": "ok", "profile_code": "PRF-USR-OPERACIONES"},
            evidence={"profile_name": "Perfil Estándar"},
        ),
        AuditResult(
            rule_code="IAM-003",
            criterion_code="C18-01",
            resource_id=2,
            result_status="Hallazgo",
            justification="Permiso excesivamente amplio (Action: *, Resource: *).",
            profile_id=2,
            details={"severity": "CRITICA", "findings_count": 1, "profile_code": "PRF-USR-SOPORTE"},
            evidence={"wildcard_actions": ["*"], "wildcard_resources": ["*"]},
        ),
        AuditResult(
            rule_code="IAM-002",
            criterion_code="C16-01",
            resource_id=3,
            result_status="No evaluable",
            justification="Metadatos incompletos de actividad.",
            profile_id=None,
            details={},
            evidence={},
        ),
    ]


@pytest.fixture
def sample_resources():
    return [
        {"id": 1, "resource_key": "ana.operaciones", "display_name": "Ana Morales"},
        {"id": 2, "resource_key": "carlos.soporte", "display_name": "Carlos Rodríguez"},
        {"id": 3, "resource_key": "usuario.inactivo", "display_name": "Usuario Inactivo"},
    ]


@pytest.fixture
def sample_summary():
    return {"total": 3, "conforme": 1, "hallazgo": 1, "no_evaluable": 1}


@pytest.fixture
def default_db_catalogs():
    """Catálogos válidos simulados para las consultas de resolución referencial en MySQL."""
    rules = [
        {"id": 10, "rule_code": "IAM-001", "default_severity": "ALTA"},
        {"id": 20, "rule_code": "IAM-002", "default_severity": "MEDIA"},
        {"id": 30, "rule_code": "IAM-003", "default_severity": "CRITICA"},
        {"id": 40, "rule_code": "IAM-004", "default_severity": "ALTA"},
    ]
    resources = [
        {"id": 101, "resource_key": "ana.operaciones"},
        {"id": 102, "resource_key": "carlos.soporte"},
        {"id": 103, "resource_key": "usuario.inactivo"},
    ]
    profiles = [
        {"id": 501, "profile_code": "PRF-USR-OPERACIONES"},
        {"id": 502, "profile_code": "PRF-USR-SOPORTE"},
    ]
    return rules, resources, profiles


# =============================================================================
# 1. PRUEBAS DE PERSISTENCIA TRANSACCIONAL (GUARDADO ATÓMICO)
# =============================================================================

def test_save_audit_run_success(sample_results, sample_resources, sample_summary, default_db_catalogs):
    """1. Verifica el guardado completo de una ejecución, resultados, hallazgos y evidencias."""
    rules_cat, res_cat, prof_cat = default_db_catalogs
    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = [rules_cat, res_cat, prof_cat]
    mock_cursor.lastrowid = 100

    with patch("src.auditoria_iam.database.persistence.get_db_transaction") as mock_tx:
        mock_tx.return_value.__enter__.return_value = mock_cursor

        run_id = save_audit_run(
            source_type="simulacion",
            results=sample_results,
            resources=sample_resources,
            summary=sample_summary,
        )

        assert run_id == 100
        executed_sqls = [c[0][0] for c in mock_cursor.execute.call_args_list]

        assert any("INSERT INTO audit_runs" in sql for sql in executed_sqls)
        assert any("INSERT INTO audit_results" in sql for sql in executed_sqls)
        assert any("INSERT INTO findings" in sql for sql in executed_sqls)
        assert any("INSERT INTO audit_evidence" in sql for sql in executed_sqls)


def test_save_audit_run_records_individual_results(sample_results, sample_resources, sample_summary, default_db_catalogs):
    """2. Verifica que cada AuditResult se inserte como un registro en audit_results con IDs reales de MySQL."""
    rules_cat, res_cat, prof_cat = default_db_catalogs
    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = [rules_cat, res_cat, prof_cat]
    mock_cursor.lastrowid = 50

    with patch("src.auditoria_iam.database.persistence.get_db_transaction") as mock_tx:
        mock_tx.return_value.__enter__.return_value = mock_cursor

        save_audit_run("simulacion", sample_results, sample_resources, sample_summary)

        result_inserts = [
            c[0] for c in mock_cursor.execute.call_args_list
            if "INSERT INTO audit_results" in c[0][0]
        ]
        assert len(result_inserts) == 3

        # Primer resultado (Conforme, resource_id simulado 1 -> MySQL ID 101)
        _, params_0 = result_inserts[0]
        assert params_0[0] == 50   # audit_run_id
        assert params_0[1] == 101  # resource_id resuelto de MySQL
        assert params_0[2] == 10   # audit_rule_id resuelto de MySQL
        assert params_0[4] == "Conforme"
        assert params_0[6] == 501  # profile_id resuelto por profile_code

        # Segundo resultado (Hallazgo, resource_id simulado 2 -> MySQL ID 102)
        _, params_1 = result_inserts[1]
        assert params_1[1] == 102
        assert params_1[2] == 30   # audit_rule_id IAM-003
        assert params_1[4] == "Hallazgo"
        assert params_1[6] == 502

        # Tercer resultado (No evaluable, resource_id simulado 3 -> MySQL ID 103)
        _, params_2 = result_inserts[2]
        assert params_2[1] == 103
        assert params_2[2] == 20   # audit_rule_id IAM-002
        assert params_2[4] == "No evaluable"
        assert params_2[6] is None  # Sin perfil -> NULL


def test_save_audit_run_records_findings_only_for_hallazgo(sample_results, sample_resources, sample_summary, default_db_catalogs):
    """3. Verifica que solo los resultados de estado 'Hallazgo' generen registros en findings."""
    rules_cat, res_cat, prof_cat = default_db_catalogs
    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = [rules_cat, res_cat, prof_cat]
    mock_cursor.lastrowid = 10

    with patch("src.auditoria_iam.database.persistence.get_db_transaction") as mock_tx:
        mock_tx.return_value.__enter__.return_value = mock_cursor

        save_audit_run("simulacion", sample_results, sample_resources, sample_summary)

        finding_inserts = [
            c[0] for c in mock_cursor.execute.call_args_list
            if "INSERT INTO findings" in c[0][0]
        ]
        assert len(finding_inserts) == 1
        query, params = finding_inserts[0]
        assert params[1] == 102        # resource_id MySQL del hallazgo
        assert params[2] == 30         # audit_rule_id IAM-003
        assert params[4] == "Hallazgo"
        assert "IAM-003" in params[6]  # finding_title
        assert params[5] == "CRITICA"  # severity


def test_save_audit_evidence_respects_chk_evidence_target(sample_results, sample_resources, sample_summary, default_db_catalogs):
    """4. Verifica que las evidencias cumplan chk_evidence_target (exclusión mutua entre finding_id y audit_result_id)."""
    rules_cat, res_cat, prof_cat = default_db_catalogs
    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = [rules_cat, res_cat, prof_cat]
    mock_cursor.lastrowid = 200

    with patch("src.auditoria_iam.database.persistence.get_db_transaction") as mock_tx:
        mock_tx.return_value.__enter__.return_value = mock_cursor

        save_audit_run("simulacion", sample_results, sample_resources, sample_summary)

        evidence_inserts = [
            c[0] for c in mock_cursor.execute.call_args_list
            if "INSERT INTO audit_evidence" in c[0][0]
        ]

        for query, params in evidence_inserts:
            finding_id, audit_result_id = params[0], params[1]
            is_valid = (finding_id is not None and audit_result_id is None) or (finding_id is None and audit_result_id is not None)
            assert is_valid, f"Violación de chk_evidence_target: finding_id={finding_id}, audit_result_id={audit_result_id}"


def test_save_audit_run_transaction_rollback_on_error(sample_results, sample_resources, sample_summary, default_db_catalogs):
    """5. Verifica que ante una excepción se produzca un rollback y se re-lance la excepción sin guardar registros."""
    rules_cat, res_cat, prof_cat = default_db_catalogs
    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = [rules_cat, res_cat, prof_cat]

    def side_effect_execute(sql, *args, **kwargs):
        if "INSERT INTO audit_runs" in sql:
            raise RuntimeError("Error de escritura en disco / violación de restricción")

    mock_cursor.execute.side_effect = side_effect_execute

    with patch("src.auditoria_iam.database.connection.get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        with pytest.raises(RuntimeError) as exc_info:
            save_audit_run("simulacion", sample_results, sample_resources, sample_summary)

        assert "Error de escritura" in str(exc_info.value)
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()


# =============================================================================
# 2. PRUEBAS DE RESOLUCIÓN SEGURA DE RECURSOS E INTEGRIDAD REFERENCIAL
# =============================================================================

def test_resource_mapping_when_simulator_and_mysql_ids_differ():
    """6. Verifica que la resolución use resource_key y asigne el ID de MySQL cuando los IDs difieren."""
    sim_results = [
        AuditResult("IAM-001", "C15-01", 1, "Conforme", "Simulador ID 1"),
        AuditResult("IAM-003", "C18-01", 2, "Hallazgo", "Simulador ID 2"),
    ]
    sim_resources = [
        {"id": 1, "resource_key": "ana.operaciones"},
        {"id": 2, "resource_key": "carlos.soporte"},
    ]
    summary = {"total": 2, "conforme": 1, "hallazgo": 1, "no_evaluable": 0}

    # En MySQL, los recursos tienen IDs totalmente distintos (ej. 888 y 999)
    rules_cat = [
        {"id": 10, "rule_code": "IAM-001"},
        {"id": 30, "rule_code": "IAM-003"},
    ]
    res_cat = [
        {"id": 888, "resource_key": "ana.operaciones"},
        {"id": 999, "resource_key": "carlos.soporte"},
    ]
    prof_cat = []

    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = [rules_cat, res_cat, prof_cat]
    mock_cursor.lastrowid = 1

    with patch("src.auditoria_iam.database.persistence.get_db_transaction") as mock_tx:
        mock_tx.return_value.__enter__.return_value = mock_cursor

        save_audit_run("simulacion", sim_results, sim_resources, summary)

        result_inserts = [
            c[0] for c in mock_cursor.execute.call_args_list
            if "INSERT INTO audit_results" in c[0][0]
        ]
        assert len(result_inserts) == 2
        # El recurso con id simulado 1 debe insertarse con resource_id=888 en MySQL
        assert result_inserts[0][1][1] == 888
        # El recurso con id simulado 2 debe insertarse con resource_id=999 en MySQL
        assert result_inserts[1][1][1] == 999

        finding_inserts = [
            c[0] for c in mock_cursor.execute.call_args_list
            if "INSERT INTO findings" in c[0][0]
        ]
        assert len(finding_inserts) == 1
        # El hallazgo debe usar el ID real de MySQL (999), no el simulado (2)
        assert finding_inserts[0][1][1] == 999


def test_nonexistent_resource_causes_rollback_and_never_maps_to_fallback():
    """7. Verifica que un recurso no registrado en MySQL interrumpa la transacción y haga rollback."""
    sim_results = [
        AuditResult("IAM-001", "C15-01", 99, "Conforme", "Recurso no registrado"),
    ]
    sim_resources = [
        {"id": 99, "resource_key": "recurso.fantasma"},
    ]
    summary = {"total": 1, "conforme": 1, "hallazgo": 0, "no_evaluable": 0}

    rules_cat = [{"id": 10, "rule_code": "IAM-001"}]
    # MySQL NO tiene registrado 'recurso.fantasma'
    res_cat = [{"id": 1, "resource_key": "otro.recurso"}]
    prof_cat = []

    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = [rules_cat, res_cat, prof_cat]

    with patch("src.auditoria_iam.database.connection.get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        with pytest.raises(RuntimeError) as exc_info:
            save_audit_run("simulacion", sim_results, sim_resources, summary)

        err_msg = str(exc_info.value)
        assert "recurso.fantasma" in err_msg
        assert "no existe en la tabla 'resources'" in err_msg
        # Asegurar rollback y ningún commit
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()


def test_ambiguous_resource_correspondence_causes_rollback():
    """8. Verifica que si MySQL tiene claves duplicadas para el mismo origen, se aborte con rollback."""
    sim_results = [
        AuditResult("IAM-001", "C15-01", 1, "Conforme", "Recurso ambiguo"),
    ]
    sim_resources = [
        {"id": 1, "resource_key": "ana.operaciones"},
    ]
    summary = {"total": 1, "conforme": 1, "hallazgo": 0, "no_evaluable": 0}

    rules_cat = [{"id": 10, "rule_code": "IAM-001"}]
    # En MySQL hay duplicados para la misma clave y origen
    res_cat = [
        {"id": 101, "resource_key": "ana.operaciones"},
        {"id": 102, "resource_key": "ana.operaciones"},
    ]
    prof_cat = []

    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = [rules_cat, res_cat, prof_cat]

    with patch("src.auditoria_iam.database.connection.get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        with pytest.raises(RuntimeError) as exc_info:
            save_audit_run("simulacion", sim_results, sim_resources, summary)

        assert "Correspondencia ambigua" in str(exc_info.value)
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()


def test_missing_audit_rule_causes_rollback_without_fallback_ids():
    """9. Verifica que una regla faltante en audit_rules cancele la transacción y no use diccionarios fijos."""
    sim_results = [
        AuditResult("IAM-001", "C15-01", 1, "Conforme", "Regla válida"),
        AuditResult("IAM-999", "C99-01", 1, "Conforme", "Regla inexistente en DB"),
    ]
    sim_resources = [{"id": 1, "resource_key": "ana.operaciones"}]
    summary = {"total": 2, "conforme": 2, "hallazgo": 0, "no_evaluable": 0}

    rules_cat = [{"id": 1, "rule_code": "IAM-001"}]  # IAM-999 falta
    res_cat = [{"id": 101, "resource_key": "ana.operaciones"}]
    prof_cat = []

    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = [rules_cat, res_cat, prof_cat]

    with patch("src.auditoria_iam.database.connection.get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        with pytest.raises(RuntimeError) as exc_info:
            save_audit_run("simulacion", sim_results, sim_resources, summary)

        err_msg = str(exc_info.value)
        assert "IAM-999" in err_msg
        assert "no existen en la tabla 'audit_rules'" in err_msg
        assert "no se permite asociar IDs de respaldo" in err_msg
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()


def test_profile_resolution_strict_matching_and_null_fallback():
    """10. Verifica correspondencia inequívoca de perfiles por profile_code y uso de NULL cuando no corresponde."""
    sim_results = [
        # Perfil con código coincidente en MySQL -> Debe asociar ID real 501
        AuditResult(
            rule_code="IAM-001",
            criterion_code="C15-01",
            resource_id=1,
            result_status="Conforme",
            justification="Perfil coincidente",
            profile_id=1,
            details={"profile_code": "PRF-USR-OPERACIONES"},
        ),
        # Perfil con código no coincidente en MySQL -> Debe asociar None (NULL)
        AuditResult(
            rule_code="IAM-001",
            criterion_code="C15-02",
            resource_id=1,
            result_status="Conforme",
            justification="Perfil desconocido",
            profile_id=99,
            details={"profile_code": "PRF-DESCONOCIDO"},
        ),
        # Sin perfil -> Debe asociar None (NULL)
        AuditResult(
            rule_code="IAM-002",
            criterion_code="C16-01",
            resource_id=1,
            result_status="Conforme",
            justification="Sin perfil",
            profile_id=None,
        ),
    ]
    sim_resources = [{"id": 1, "resource_key": "ana.operaciones"}]
    summary = {"total": 3, "conforme": 3, "hallazgo": 0, "no_evaluable": 0}

    rules_cat = [
        {"id": 10, "rule_code": "IAM-001"},
        {"id": 20, "rule_code": "IAM-002"},
    ]
    res_cat = [{"id": 101, "resource_key": "ana.operaciones"}]
    prof_cat = [{"id": 501, "profile_code": "PRF-USR-OPERACIONES"}]

    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = [rules_cat, res_cat, prof_cat]
    mock_cursor.lastrowid = 1

    with patch("src.auditoria_iam.database.persistence.get_db_transaction") as mock_tx:
        mock_tx.return_value.__enter__.return_value = mock_cursor

        save_audit_run("simulacion", sim_results, sim_resources, summary)

        result_inserts = [
            c[0] for c in mock_cursor.execute.call_args_list
            if "INSERT INTO audit_results" in c[0][0]
        ]
        assert len(result_inserts) == 3
        # 1. Coincidente -> ID 501
        assert result_inserts[0][1][6] == 501
        # 2. Desconocido -> None (NULL)
        assert result_inserts[1][1][6] is None
        # 3. Sin perfil -> None (NULL)
        assert result_inserts[2][1][6] is None


def test_strictly_no_modifications_on_catalog_tables(sample_results, sample_resources, sample_summary, default_db_catalogs):
    """11. Verifica que bajo ninguna circunstancia se ejecuten INSERT, UPDATE o DELETE en tablas de catálogo."""
    rules_cat, res_cat, prof_cat = default_db_catalogs
    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = [rules_cat, res_cat, prof_cat]
    mock_cursor.lastrowid = 1

    with patch("src.auditoria_iam.database.persistence.get_db_transaction") as mock_tx:
        mock_tx.return_value.__enter__.return_value = mock_cursor

        save_audit_run("simulacion", sample_results, sample_resources, sample_summary)

        catalog_tables = ["resources", "audit_rules", "access_profiles", "iso_controls"]
        modifying_verbs = ["INSERT INTO", "UPDATE", "DELETE FROM"]

        executed_sqls = [c[0][0].strip().upper() for c in mock_cursor.execute.call_args_list]

        for sql in executed_sqls:
            for verb in modifying_verbs:
                if sql.startswith(verb):
                    for tbl in catalog_tables:
                        assert f" {tbl.upper()} " not in f" {sql} ", (
                            f"Violación de integridad: Operación prohibida '{verb}' ejecutada sobre '{tbl}': {sql}"
                        )


# =============================================================================
# 3. PRUEBAS DE INTEGRACIÓN EN AUDIT_SERVICE
# =============================================================================

def test_audit_service_run_simulated_audit_with_persistence():
    """12. Verifica que AuditService.run_simulated_audit persista exitosamente en MySQL."""
    service = AuditService()

    with patch("src.auditoria_iam.application.audit_service.save_audit_run", return_value=123) as mock_save:
        results, resources, summary, p_info = service.run_simulated_audit(persist=True)

        assert len(results) == 67
        assert summary["total"] == 67
        assert p_info["persisted"] is True
        assert p_info["run_id"] == 123
        assert "ID #123" in p_info["message"]
        mock_save.assert_called_once()


def test_audit_service_run_simulated_audit_retains_memory_on_db_failure():
    """13. Verifica que si MySQL falla, AuditService conserve los resultados y reporte persistencia fallida."""
    service = AuditService()

    with patch("src.auditoria_iam.application.audit_service.save_audit_run", side_effect=RuntimeError("MySQL no disponible")):
        results, resources, summary, p_info = service.run_simulated_audit(persist=True)

        assert len(results) == 67
        assert summary["total"] == 67
        assert summary["conforme"] == 36
        assert summary["hallazgo"] == 6
        assert summary["no_evaluable"] == 25
        assert p_info["persisted"] is False
        assert p_info["run_id"] is None
        assert "No se pudo conectar o guardar en MySQL" in p_info["message"]


def test_audit_service_get_audit_history():
    """14. Verifica que AuditService.get_audit_history recupere el listado desde el repositorio."""
    service = AuditService()
    mock_runs = [{"id": 1, "source_type": "simulacion", "total_findings": 6}]

    with patch("src.auditoria_iam.application.audit_service.get_audit_runs", return_value=mock_runs) as mock_get:
        history = service.get_audit_history(limit=10)
        assert len(history) == 1
        assert history[0]["id"] == 1
        mock_get.assert_called_once_with(limit=10, db_name=None)


def test_audit_service_get_historical_run_results():
    """15. Verifica la recuperación y reconstrucción de AuditResult históricos desde la base de datos."""
    service = AuditService()
    db_rows = [
        {
            "id": 1,
            "resource_id": 1,
            "rule_code": "IAM-001",
            "criterion_code": "C15-01",
            "result_status": "Conforme",
            "justification": "Histórico Conforme",
            "profile_id": 1,
            "details": json.dumps({"test": "ok"}),
            "resource_key": "ana.operaciones",
            "display_name": "Ana Morales",
        },
        {
            "id": 2,
            "resource_id": 2,
            "rule_code": "IAM-003",
            "criterion_code": "C18-01",
            "result_status": "Hallazgo",
            "justification": "Histórico Hallazgo",
            "profile_id": 2,
            "details": {"test": "finding"},
            "resource_key": "carlos.soporte",
            "display_name": "Carlos Rodríguez",
        },
    ]

    with patch("src.auditoria_iam.application.audit_service.get_audit_results_by_run", return_value=db_rows):
        results, resources, summary = service.get_historical_run_results(run_id=5)

        assert len(results) == 2
        assert isinstance(results[0], AuditResult)
        assert results[0].rule_code == "IAM-001"
        assert results[0].result_status == "Conforme"
        assert results[1].rule_code == "IAM-003"
        assert results[1].result_status == "Hallazgo"

        assert summary["total"] == 2
        assert summary["conforme"] == 1
        assert summary["hallazgo"] == 1
        assert summary["no_evaluable"] == 0

        assert len(resources) == 2


# =============================================================================
# 4. SEGURIDAD: AUSENCIA DE OPERACIONES UPDATE, DELETE O DDL DESTRUCTIVO
# =============================================================================

def test_persistence_strictly_no_update_or_delete():
    """16. Verifica mediante análisis de código que no existan sentencias UPDATE, DELETE, DROP o ALTER."""
    import src.auditoria_iam.database.persistence as pers_mod

    forbidden_keywords = [
        "UPDATE ",
        "DELETE FROM",
        "DROP TABLE",
        "ALTER TABLE",
        "TRUNCATE ",
        "ON DUPLICATE KEY UPDATE",
        "REPLACE INTO",
    ]

    functions = [
        obj for name, obj in inspect.getmembers(pers_mod, inspect.isfunction)
        if obj.__module__ == pers_mod.__name__
    ]

    for func in functions:
        source = inspect.getsource(func)
        for keyword in forbidden_keywords:
            assert keyword not in source.upper(), (
                f"Violación de restricciones de seguridad: La función {func.__name__} contiene '{keyword}'."
            )
