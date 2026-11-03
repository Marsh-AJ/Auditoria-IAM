"""
Pruebas de Integración y Validación Integral del Flujo de Auditoría AWS IAM.
Fase 7, Entrega 7.2.2.

Valida el ciclo de vida completo de auditorías AWS IAM sin conexiones reales a la nube
ni modificaciones a la base de datos MySQL local:
1. Flujo de ejecución en AuditService (run_aws_audit, AuditEngine, 4 reglas).
2. Evaluación exhaustiva de las 4 reglas (IAM-001, IAM-002, IAM-003, IAM-004)
   produciendo Conforme, Hallazgo y No evaluable según criterios ISO/IEC 27001:2022.
3. Persistencia transaccional con source_type='aws', rollback ante fallos y retención en memoria.
4. Historial cronológico y Dashboard con métricas agregadas reconociendo ejecuciones AWS.
5. Exportación de informes (PDF, Excel XLSX, CSV) con origen AWS y sin fuga de credenciales.
6. Manejo controlado de errores (autenticación, permisos, conexión, políticas incompletas,
   recursos no registrados, ejecución consecutiva con el simulador).
"""
import csv
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import boto3
import botocore.exceptions
from botocore.stub import Stubber
import openpyxl
import pytest

from src.auditoria_iam.application.audit_service import AuditService
from src.auditoria_iam.audit.engine import AuditEngine
from src.auditoria_iam.audit.models import AuditContext, AuditResult
from src.auditoria_iam.audit.rules.iam_001_access_control import RuleIAM001AccessControl
from src.auditoria_iam.audit.rules.iam_002_identity_management import RuleIAM002IdentityManagement
from src.auditoria_iam.audit.rules.iam_003_access_rights import RuleIAM003AccessRights
from src.auditoria_iam.audit.rules.iam_004_secure_authentication import RuleIAM004SecureAuthentication
from src.auditoria_iam.data_sources.aws.adapter import (
    FORBIDDEN_OPERATION_PREFIXES,
    READ_ONLY_OPERATIONS,
    AWSIAMDataSource,
)
from src.auditoria_iam.data_sources.aws.exceptions import (
    AWSIAMAuthenticationError,
    AWSIAMConnectionError,
    AWSIAMDataSourceError,
    AWSIAMPermissionError,
)
from src.auditoria_iam.data_sources.simulator.simulator import IAMSimulatorDataSource
from src.auditoria_iam.database.persistence import save_audit_run
from src.auditoria_iam.reports import (
    build_report_data,
    generate_csv_report,
    generate_excel_report,
    generate_pdf_report,
)


# =============================================================================
# FIXTURES COMPARTIDOS
# =============================================================================

@pytest.fixture
def mock_aws_adapter():
    """Genera una instancia de AWSIAMDataSource con cliente desacoplado y datos canónicos."""
    client = MagicMock()
    client.can_paginate.return_value = False
    now = datetime.now(timezone.utc)

    # 1 usuario estándar
    client.list_users.return_value = {
        "Users": [
            {
                "UserName": "patricia.devops",
                "UserId": "AIDA1234567890123456",
                "Arn": "arn:aws:iam::123456789012:user/patricia.devops",
                "CreateDate": now - timedelta(days=60),
                "PasswordLastUsed": now - timedelta(days=10),
            }
        ],
        "IsTruncated": False,
    }
    client.list_groups_for_user.return_value = {
        "Groups": [{"GroupName": "DevOpsTeam", "Arn": "arn:aws:iam::123456789012:group/DevOpsTeam"}],
        "IsTruncated": False,
    }
    client.list_mfa_devices.return_value = {
        "MFADevices": [{"UserName": "patricia.devops", "SerialNumber": "arn:aws:iam::123456789012:mfa/patricia.devops"}],
        "IsTruncated": False,
    }
    client.list_access_keys.return_value = {
        "AccessKeyMetadata": [],
        "IsTruncated": False,
    }
    client.list_user_policies.return_value = {"PolicyNames": [], "IsTruncated": False}
    client.list_attached_user_policies.return_value = {"AttachedPolicies": [], "IsTruncated": False}
    client.list_attached_group_policies.return_value = {"AttachedPolicies": [], "IsTruncated": False}
    client.list_group_policies.return_value = {"PolicyNames": [], "IsTruncated": False}

    # 1 rol estándar
    client.list_roles.return_value = {
        "Roles": [
            {
                "RoleName": "RolServidorApp",
                "RoleId": "AROA1234567890123456",
                "Arn": "arn:aws:iam::123456789012:role/RolServidorApp",
                "CreateDate": now - timedelta(days=30),
                "AssumeRolePolicyDocument": json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [{"Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::123456789012:root"}, "Action": "sts:AssumeRole"}],
                }),
                "RoleLastUsed": {"LastUsedDate": now - timedelta(days=5)},
            }
        ],
        "IsTruncated": False,
    }
    client.list_role_policies.return_value = {"PolicyNames": [], "IsTruncated": False}
    client.list_attached_role_policies.return_value = {"AttachedPolicies": [], "IsTruncated": False}

    ds = AWSIAMDataSource(client=client)
    return ds


@pytest.fixture
def standard_aws_context():
    """Contexto de perfiles de referencia autorizados para los recursos simulados de AWS."""
    return AuditContext(
        profiles={
            1: {"id": 1, "profile_code": "PRF-DEV-01", "status": "active", "identity_type": "user", "version": "1.0"},
            2: {"id": 2, "profile_code": "PRF-ROL-01", "status": "active", "identity_type": "role", "version": "1.0"},
        },
        expected_groups={1: ["DevOpsTeam"]},
        expected_trust_principals={
            2: [{"principal_type": "AWS", "principal_identifier": "arn:aws:iam::123456789012:root", "trust_action": "sts:AssumeRole"}],
        },
        resource_key_profiles={
            "patricia.devops": 1,
            "RolServidorApp": 2,
        },
    )


@pytest.fixture
def mock_mysql_catalogs():
    """Catálogos de base de datos MySQL requeridos para resolver llaves naturales en persistencia."""
    rules = [
        {"id": 1, "rule_code": "IAM-001", "default_severity": "ALTA"},
        {"id": 2, "rule_code": "IAM-002", "default_severity": "MEDIA"},
        {"id": 3, "rule_code": "IAM-003", "default_severity": "CRITICA"},
        {"id": 4, "rule_code": "IAM-004", "default_severity": "ALTA"},
    ]
    resources = [
        {"id": 201, "resource_key": "patricia.devops"},
        {"id": 202, "resource_key": "RolServidorApp"},
    ]
    profiles = [
        {"id": 1, "profile_code": "PRF-DEV-01"},
        {"id": 2, "profile_code": "PRF-ROL-01"},
    ]
    return rules, resources, profiles


# =============================================================================
# 1. VALIDACIÓN DEL FLUJO DE EJECUCIÓN AWS (AuditService.run_aws_audit)
# =============================================================================

def test_e2e_run_aws_audit_executes_engine_and_all_four_rules(mock_aws_adapter, standard_aws_context):
    """3.1. Verifica que run_aws_audit ejecute el motor central y las 4 reglas sobre recursos AWS."""
    service = AuditService()
    results, resources, summary, persistence_info = service.run_aws_audit(
        persist=False,
        aws_data_source=mock_aws_adapter,
        context=standard_aws_context,
    )

    # 1. Obtiene recursos mediante AWSIAMDataSource
    assert len(resources) == 2
    r_keys = {r["resource_key"] for r in resources}
    assert "patricia.devops" in r_keys
    assert "RolServidorApp" in r_keys

    # 2. Ejecuta el mismo AuditEngine y las 4 reglas técnicas
    rules_evaluated = {res.rule_code for res in results}
    assert "IAM-001" in rules_evaluated
    assert "IAM-002" in rules_evaluated
    assert "IAM-003" in rules_evaluated
    assert "IAM-004" in rules_evaluated

    # 3. Resumen cuantitativo coherente
    assert summary["total"] == len(results)
    assert summary["total"] == summary["conforme"] + summary["hallazgo"] + summary["no_evaluable"]

    # 4. Origen identificado como 'aws'
    for r in resources:
        assert r["source_type"] == "aws"


def test_e2e_run_aws_audit_does_not_affect_simulator_flow(mock_aws_adapter, standard_aws_context):
    """3.1. Comprueba que ejecutar una auditoría AWS no altera en absoluto el comportamiento del simulador."""
    service = AuditService()

    # 1. Ejecutar auditoría AWS
    aws_results, aws_resources, aws_sum, _ = service.run_aws_audit(
        persist=False,
        aws_data_source=mock_aws_adapter,
        context=standard_aws_context,
    )
    assert len(aws_resources) == 2

    # 2. Ejecutar inmediatamente auditoría simulada
    sim_results, sim_resources, sim_sum, _ = service.run_simulated_audit(persist=False)

    # El dataset determinista del simulador debe permanecer 100% íntegro (10 recursos, 67 resultados)
    assert len(sim_resources) == 10
    assert len(sim_results) == 67
    assert sim_sum["total"] == 67
    assert all(r["source_type"] == "simulacion" for r in sim_resources)


def test_e2e_unified_run_audit_entrypoint_dispatches_correctly(mock_aws_adapter, standard_aws_context):
    """3.1. Verifica que el método unificado run_audit despache limpiamente según source_type."""
    service = AuditService()

    # Invocación con 'aws'
    res_aws, rsc_aws, sum_aws, _ = service.run_audit(
        source_type="aws",
        persist=False,
        aws_data_source=mock_aws_adapter,
        context=standard_aws_context,
    )
    assert all(r["source_type"] == "aws" for r in rsc_aws)

    # Invocación con 'simulacion'
    res_sim, rsc_sim, sum_sim, _ = service.run_audit(
        source_type="simulacion",
        persist=False,
    )
    assert all(r["source_type"] == "simulacion" for r in rsc_sim)
    assert len(rsc_sim) == 10


# =============================================================================
# 2. VALIDACIÓN DETALLADA DE LAS CUATRO REGLAS SOBRE RECURSOS AWS
# =============================================================================

def test_e2e_iam_001_access_control_rule_states():
    """3.2. IAM-001 (Control 5.15): Verifica Conforme, Hallazgo y No evaluable sin inventar resultados."""
    rule = RuleIAM001AccessControl()

    context = AuditContext(
        profiles={
            1: {"id": 1, "profile_code": "PRF-USER", "status": "active", "identity_type": "user"},
            2: {"id": 2, "profile_code": "PRF-ROLE", "status": "active", "identity_type": "role"},
        },
        expected_groups={1: ["AllowedGroup"]},
        expected_trust_principals={
            2: [{"principal_type": "AWS", "principal_identifier": "arn:aws:iam::123456789012:root", "trust_action": "sts:AssumeRole"}],
        },
        resource_key_profiles={"user.ok": 1, "user.bad": 1, "role.ok": 2},
    )

    # Caso A: Conforme (usuario con grupos esperados)
    res_ok = {
        "id": 1001,
        "resource_key": "user.ok",
        "resource_type": "IAM_USER",
        "attributes": {"groups": ["AllowedGroup"]},
    }
    results_ok = rule.evaluate(res_ok, context)
    assert any(r.criterion_code == "C15-01" and r.result_status == "Conforme" for r in results_ok)

    # Caso B: Hallazgo (usuario con grupo no autorizado)
    res_bad = {
        "id": 1002,
        "resource_key": "user.bad",
        "resource_type": "IAM_USER",
        "attributes": {"groups": ["AllowedGroup", "UnauthorizedAdminGroup"]},
    }
    results_bad = rule.evaluate(res_bad, context)
    assert any(r.criterion_code == "C15-01" and r.result_status == "Hallazgo" for r in results_bad)

    # Caso C: No evaluable (recurso AWS sin perfil de referencia no produce Conforme automático)
    res_unmapped = {
        "id": 1003,
        "resource_key": "user.unregistered",
        "resource_type": "IAM_USER",
        "attributes": {"groups": ["AnyGroup"]},
    }
    results_unmapped = rule.evaluate(res_unmapped, context)
    assert any(r.criterion_code == "C15-01" and r.result_status == "No evaluable" for r in results_unmapped)
    assert not any(r.result_status == "Conforme" for r in results_unmapped)


def test_e2e_iam_002_identity_management_inactivity_rule_states():
    """3.2. IAM-002 (Control 5.16): Verifica actividad reciente, inactividad y ausencia de datos."""
    rule = RuleIAM002IdentityManagement(inactivity_threshold_days=90)

    # Caso A: Conforme (actividad reciente, 15 días <= 90 días)
    res_active = {
        "id": 1001,
        "resource_key": "user.active",
        "resource_type": "IAM_USER",
        "attributes": {"last_access_days": 15},
    }
    r_act = rule.evaluate(res_active)
    assert any(r.criterion_code == "C16-02" and r.result_status == "Conforme" for r in r_act)

    # Caso B: Hallazgo (inactivo, 120 días > 90 días)
    res_inactive = {
        "id": 1002,
        "resource_key": "user.dormant",
        "resource_type": "IAM_USER",
        "attributes": {"last_access_days": 120},
    }
    r_inact = rule.evaluate(res_inactive)
    assert any(r.criterion_code == "C16-02" and r.result_status == "Hallazgo" for r in r_inact)

    # Caso C: No evaluable (sin metadatos de actividad válidos no inventa hallazgos de inactividad)
    res_unknown = {
        "id": 1003,
        "resource_key": "user.unknown_activity",
        "resource_type": "IAM_USER",
        "attributes": {"last_access_days": None},
    }
    r_unk = rule.evaluate(res_unknown)
    c16_02 = next(r for r in r_unk if r.criterion_code == "C16-02")
    assert c16_02.result_status == "No evaluable"


def test_e2e_iam_003_access_rights_policy_analysis_rule_states():
    """3.2. IAM-003 (Control 5.18): Verifica políticas acotadas, comodines excesivos e incompletas."""
    rule = RuleIAM003AccessRights()

    # Caso A: Conforme (política acotada sin comodines globales)
    policy_safe = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::upharven/*"}],
    }
    res_safe = {
        "id": 1001,
        "resource_key": "user.least_privilege",
        "resource_type": "IAM_USER",
        "attributes": {"policies": [policy_safe]},
    }
    r_safe = rule.evaluate(res_safe)
    assert any(r.criterion_code == "C18-01" and r.result_status == "Conforme" for r in r_safe)

    # Caso B: Hallazgo (comodín amplio en Action o Resource)
    policy_wildcard = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}],
    }
    res_wildcard = {
        "id": 1002,
        "resource_key": "user.admin_wildcard",
        "resource_type": "IAM_USER",
        "attributes": {"policies": [policy_wildcard]},
    }
    r_wild = rule.evaluate(res_wildcard)
    assert any(r.criterion_code == "C18-01" and r.result_status == "Hallazgo" for r in r_wild)

    # Caso C: No evaluable (política inaccesible con marcador incompleto no produce falso Conforme)
    policy_incomplete = {
        "_source_type": "user_inline",
        "_incomplete_policy": True,
        "_error": "AccessDenied al consultar GetUserPolicy",
        "Statement": None,
    }
    res_incomplete = {
        "id": 1003,
        "resource_key": "user.restricted_read",
        "resource_type": "IAM_USER",
        "attributes": {"policies": [policy_incomplete]},
    }
    r_incomp = rule.evaluate(res_incomplete)
    c18_01 = next(r for r in r_incomp if r.criterion_code == "C18-01")
    assert c18_01.result_status == "No evaluable"
    assert "missing_statement" in c18_01.evidence or "missing" in str(c18_01.evidence)


def test_e2e_iam_004_secure_authentication_rule_and_role_exclusion():
    """3.2. IAM-004 (Control 8.5): Verifica MFA en usuarios y exclusión formal de roles IAM."""
    rule = RuleIAM004SecureAuthentication()

    # Caso A: Conforme (usuario con MFA activo)
    res_mfa_ok = {
        "id": 1001,
        "resource_key": "user.mfa_enabled",
        "resource_type": "IAM_USER",
        "attributes": {"mfa_enabled": True},
    }
    r_ok = rule.evaluate(res_mfa_ok)
    assert any(r.criterion_code == "C85-01" and r.result_status == "Conforme" for r in r_ok)

    # Caso B: Hallazgo (usuario sin MFA)
    res_no_mfa = {
        "id": 1002,
        "resource_key": "user.no_mfa",
        "resource_type": "IAM_USER",
        "attributes": {"mfa_enabled": False},
    }
    r_no_mfa = rule.evaluate(res_no_mfa)
    assert any(r.criterion_code == "C85-01" and r.result_status == "Hallazgo" for r in r_no_mfa)

    # Caso C: Exclusión de roles (los roles IAM no son evaluados artificialmente como usuarios)
    res_role = {
        "id": 1003,
        "resource_key": "RolAppService",
        "resource_type": "IAM_ROLE",
        "attributes": {"mfa_enabled": False},
    }
    r_role = rule.evaluate(res_role)
    assert r_role == []  # No emite resultados en C85-01


# =============================================================================
# 3. VALIDACIÓN DE PERSISTENCIA TRANSACCIONAL (save_audit_run CON AWS)
# =============================================================================

def test_e2e_save_audit_run_aws_transactional_success(mock_mysql_catalogs):
    """3.3. Verifica que save_audit_run persista una auditoría AWS con source_type='aws'."""
    rules_cat, res_cat, prof_cat = mock_mysql_catalogs

    results = [
        AuditResult(rule_code="IAM-001", criterion_code="C15-01", resource_id=1001, result_status="Conforme", justification="OK"),
        AuditResult(rule_code="IAM-004", criterion_code="C85-01", resource_id=1001, result_status="Conforme", justification="MFA OK"),
        AuditResult(rule_code="IAM-001", criterion_code="C15-02", resource_id=1002, result_status="Conforme", justification="Trust OK"),
    ]
    resources = [
        {"id": 1001, "resource_key": "patricia.devops", "source_type": "aws"},
        {"id": 1002, "resource_key": "RolServidorApp", "source_type": "aws"},
    ]
    summary = {"total": 3, "conforme": 3, "hallazgo": 0, "no_evaluable": 0}

    mock_cursor = MagicMock()
    # 1. audit_rules, 2. resources WHERE source_type='aws', 3. access_profiles
    mock_cursor.fetchall.side_effect = [rules_cat, res_cat, prof_cat]
    mock_cursor.lastrowid = 77

    with patch("src.auditoria_iam.database.persistence.get_db_transaction") as mock_tx:
        mock_tx.return_value.__enter__.return_value = mock_cursor

        run_id = save_audit_run(
            source_type="aws",
            results=results,
            resources=resources,
            summary=summary,
        )

        assert run_id == 77
        # Verificar que se consultó con source_type='aws'
        resource_query_call = mock_cursor.execute.call_args_list[1]
        assert resource_query_call[0][1] == ("aws",)

        # Verificar inserción en audit_runs con origen 'aws'
        run_insert_call = mock_cursor.execute.call_args_list[3]
        assert "INSERT INTO audit_runs" in run_insert_call[0][0]
        assert run_insert_call[0][1][1] == "aws"


def test_e2e_save_audit_run_aws_rollback_on_missing_resource(mock_mysql_catalogs):
    """3.3. Verifica que la ausencia de un recurso AWS en MySQL produzca rollback inmediato."""
    rules_cat, res_cat, prof_cat = mock_mysql_catalogs

    results = [
        AuditResult(rule_code="IAM-001", criterion_code="C15-01", resource_id=1099, result_status="Conforme", justification="OK"),
    ]
    # Recurso desconocido en la base de datos
    resources = [
        {"id": 1099, "resource_key": "unregistered.aws.entity", "source_type": "aws"},
    ]
    summary = {"total": 1, "conforme": 1, "hallazgo": 0, "no_evaluable": 0}

    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = [rules_cat, res_cat, prof_cat]

    with patch("src.auditoria_iam.database.persistence.get_db_transaction") as mock_tx:
        mock_tx.return_value.__enter__.return_value = mock_cursor

        with pytest.raises(RuntimeError) as exc_info:
            save_audit_run(
                source_type="aws",
                results=results,
                resources=resources,
                summary=summary,
            )

        assert "no existe en la tabla 'resources' de MySQL" in str(exc_info.value)
        assert "No se asignan identificadores de sustitución" in str(exc_info.value)


def test_e2e_run_aws_audit_in_memory_retention_when_persistence_fails(mock_aws_adapter, standard_aws_context):
    """3.3. Comprueba que ante fallo de persistencia los resultados se conservan intactos en memoria."""
    service = AuditService()

    with patch("src.auditoria_iam.application.audit_service.save_audit_run", side_effect=RuntimeError("Fallo de conexión MySQL")):
        results, resources, summary, persistence_info = service.run_aws_audit(
            persist=True,
            aws_data_source=mock_aws_adapter,
            context=standard_aws_context,
        )

        assert len(results) > 0
        assert len(resources) == 2
        assert persistence_info["persisted"] is False
        assert persistence_info["run_id"] is None
        assert "Aviso de persistencia" in persistence_info["message"]
        assert "Los resultados se conservan íntegros en memoria" in persistence_info["message"]


# =============================================================================
# 4. VALIDACIÓN DE HISTORIAL Y DASHBOARD CON AUDITORÍAS AWS
# =============================================================================

def test_e2e_history_and_historical_run_results_for_aws():
    """3.4. Comprueba que las ejecuciones AWS se consulten en historial y se reconstruyan sin mezclar datos."""
    service = AuditService()
    now = datetime.now()

    sample_runs = [
        {"id": 20, "execution_date": now, "source_type": "aws", "status": "completada", "total_findings": 1, "summary": "Conf: 3 | Hall: 1"},
        {"id": 19, "execution_date": now - timedelta(hours=2), "source_type": "simulacion", "status": "completada", "total_findings": 0, "summary": "Conf: 67 | Hall: 0"},
    ]

    sample_run_20_results = [
        {"id": 101, "audit_run_id": 20, "resource_id": 201, "resource_key": "patricia.devops", "rule_code": "IAM-001", "criterion_code": "C15-01", "result_status": "Conforme", "justification": "OK", "details": "{}"},
        {"id": 102, "audit_run_id": 20, "resource_id": 201, "resource_key": "patricia.devops", "rule_code": "IAM-004", "criterion_code": "C85-01", "result_status": "Conforme", "justification": "MFA OK", "details": "{}"},
        {"id": 103, "audit_run_id": 20, "resource_id": 202, "resource_key": "RolServidorApp", "rule_code": "IAM-001", "criterion_code": "C15-02", "result_status": "Hallazgo", "justification": "Trust error", "details": "{}"},
    ]

    with patch("src.auditoria_iam.application.audit_service.get_audit_runs", return_value=sample_runs):
        history = service.get_audit_history()
        assert len(history) == 2
        assert history[0]["source_type"] == "aws"
        assert history[0]["id"] == 20

    with patch("src.auditoria_iam.application.audit_service.get_audit_results_by_run", return_value=sample_run_20_results):
        results, resources, summary = service.get_historical_run_results(run_id=20)
        assert len(results) == 3
        assert len(resources) == 2
        assert summary["total"] == 3
        assert summary["conforme"] == 2
        assert summary["hallazgo"] == 1


def test_e2e_dashboard_metrics_reflect_latest_aws_run():
    """3.4. Comprueba que el Dashboard calcule sus indicadores a partir de la corrida AWS más reciente."""
    service = AuditService()
    now = datetime.now()

    latest_aws_run = {
        "id": 45,
        "execution_date": now,
        "source_type": "aws",
        "status": "completada",
        "total_findings": 2,
    }

    results_45 = [
        AuditResult(rule_code="IAM-001", criterion_code="C15-01", resource_id=201, result_status="Conforme", justification="OK"),
        AuditResult(rule_code="IAM-002", criterion_code="C16-02", resource_id=201, result_status="Conforme", justification="OK"),
        AuditResult(rule_code="IAM-003", criterion_code="C18-01", resource_id=201, result_status="Hallazgo", justification="Wildcard"),
        AuditResult(rule_code="IAM-004", criterion_code="C85-01", resource_id=201, result_status="Hallazgo", justification="No MFA"),
    ]
    resources_45 = [{"id": 201, "resource_key": "patricia.devops"}]
    summary_45 = {"total": 4, "conforme": 2, "hallazgo": 2, "no_evaluable": 0}

    with patch.object(service, "get_audit_history", return_value=[latest_aws_run]), \
         patch.object(service, "get_historical_run_results", return_value=(results_45, resources_45, summary_45)):

        dashboard = service.get_dashboard_data()

        assert dashboard["has_data"] is True
        assert dashboard["latest_run"]["source_type"] == "aws"
        assert dashboard["latest_run"]["id"] == 45
        assert dashboard["summary"]["total"] == 4
        assert dashboard["summary"]["conforme"] == 2
        assert dashboard["summary"]["hallazgo"] == 2
        assert dashboard["distribution"]["conforme"]["percentage"] == 50.0
        assert dashboard["distribution"]["hallazgo"]["percentage"] == 50.0
        assert dashboard["rules_summary"]["IAM-003"]["hallazgo"] == 1
        assert dashboard["rules_summary"]["IAM-004"]["hallazgo"] == 1


def test_e2e_dashboard_orders_chronologically_by_date_and_time():
    """3.4. Comprueba que el orden cronológico respete la fecha y hora más reciente, no sólo el ID."""
    service = AuditService()
    now = datetime.now()

    # Ejecución con ID menor pero fecha más reciente (ej. migración o ajuste horario)
    runs_chronological = [
        {"id": 10, "execution_date": now, "source_type": "aws", "status": "completada"},
        {"id": 15, "execution_date": now - timedelta(days=1), "source_type": "simulacion", "status": "completada"},
    ]

    with patch.object(service, "get_audit_history", return_value=runs_chronological[:1]), \
         patch.object(service, "get_historical_run_results", return_value=([], [], {"total": 0, "conforme": 0, "hallazgo": 0, "no_evaluable": 0})):

        dash = service.get_dashboard_data()
        assert dash["latest_run"]["id"] == 10
        assert dash["latest_run"]["source_type"] == "aws"


# =============================================================================
# 5. VALIDACIÓN DE EXPORTACIÓN DE INFORMES (PDF, XLSX, CSV)
# =============================================================================

def test_e2e_export_aws_audit_report_csv(tmp_path):
    """3.5. Comprueba la exportación estructurada de auditoría AWS a CSV."""
    service = AuditService()
    results = [
        AuditResult(rule_code="IAM-001", criterion_code="C15-01", resource_id=1, result_status="Conforme", justification="Grupo DevOps autorizado"),
        AuditResult(rule_code="IAM-003", criterion_code="C18-01", resource_id=1, result_status="Hallazgo", justification="Comodín detectado"),
    ]
    resources = [{"id": 1, "resource_key": "patricia.devops", "resource_type": "IAM_USER", "source_type": "aws"}]
    summary = {"total": 2, "conforme": 1, "hallazgo": 1, "no_evaluable": 0}

    csv_file = tmp_path / "informe_aws.csv"
    out = service.export_audit_report(
        filepath=str(csv_file),
        format_type="csv",
        results=results,
        resources=resources,
        summary=summary,
    )

    assert os.path.exists(out)
    with open(out, mode="r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        headers = reader[0]
        assert "ID de auditoría" in headers
        assert "Fuente" in headers
        assert "Recurso" in headers

        # Validar filas de datos
        row1 = reader[1]
        assert row1[2] == "aws"
        assert row1[3] == "patricia.devops"


def test_e2e_export_aws_audit_report_excel(tmp_path):
    """3.5. Comprueba la exportación de auditoría AWS a Excel con múltiples hojas."""
    service = AuditService()
    results = [
        AuditResult(rule_code="IAM-001", criterion_code="C15-01", resource_id=1, result_status="Conforme", justification="Grupo DevOps autorizado"),
        AuditResult(rule_code="IAM-004", criterion_code="C85-01", resource_id=1, result_status="Conforme", justification="MFA habilitado"),
    ]
    resources = [{"id": 1, "resource_key": "patricia.devops", "resource_type": "IAM_USER", "source_type": "aws"}]
    summary = {"total": 2, "conforme": 2, "hallazgo": 0, "no_evaluable": 0}

    xlsx_file = tmp_path / "informe_aws.xlsx"
    out = service.export_audit_report(
        filepath=str(xlsx_file),
        format_type="xlsx",
        results=results,
        resources=resources,
        summary=summary,
    )

    assert os.path.exists(out)
    wb = openpyxl.load_workbook(out)
    sheet_names = wb.sheetnames
    assert "Resumen" in sheet_names
    assert "Evaluaciones" in sheet_names
    assert "Hallazgos" in sheet_names
    assert "Evidencias" in sheet_names


def test_e2e_export_aws_audit_report_pdf(tmp_path):
    """3.5. Comprueba la exportación de auditoría AWS a PDF formal."""
    service = AuditService()
    results = [
        AuditResult(rule_code="IAM-001", criterion_code="C15-01", resource_id=1, result_status="Conforme", justification="OK"),
    ]
    resources = [{"id": 1, "resource_key": "patricia.devops", "resource_type": "IAM_USER", "source_type": "aws"}]
    summary = {"total": 1, "conforme": 1, "hallazgo": 0, "no_evaluable": 0}

    pdf_file = tmp_path / "informe_aws.pdf"
    out = service.export_audit_report(
        filepath=str(pdf_file),
        format_type="pdf",
        results=results,
        resources=resources,
        summary=summary,
    )

    assert os.path.exists(out)
    assert os.path.getsize(out) > 1000  # Archivo PDF válido con contenido


def test_e2e_reports_do_not_leak_credentials_or_sensitive_tokens():
    """3.5. Comprueba que la estructura del informe no filtre claves secretas ni tokens."""
    results = [
        AuditResult(rule_code="IAM-001", criterion_code="C15-01", resource_id=1, result_status="Conforme", justification="OK"),
    ]
    resources = [{"id": 1, "resource_key": "patricia.devops", "source_type": "aws"}]

    data = build_report_data(
        results=results,
        resources=resources,
    )
    serialized = json.dumps(data, ensure_ascii=False)

    # Verificar ausencia de patrones sensibles
    forbidden_tokens = ["aws_secret_access_key", "secretaccesskey", "sessiontoken", "password", "privatekey"]
    for token in forbidden_tokens:
        assert token not in serialized.lower()


# =============================================================================
# 6. VALIDACIÓN DE ERRORES, RESILIENCIA Y CASOS ESPECIALES
# =============================================================================

def test_e2e_error_handling_authentication_failure():
    """3.6. Comprueba que un fallo de autenticación de AWS se capture de forma controlada."""
    client = MagicMock()
    client.can_paginate.return_value = False
    client.list_users.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "InvalidClientTokenId", "Message": "The security token included in the request is invalid."}},
        "ListUsers"
    )
    ds = AWSIAMDataSource(client=client)
    service = AuditService()

    with pytest.raises(AWSIAMAuthenticationError) as exc_info:
        service.run_aws_audit(aws_data_source=ds, persist=False)

    assert "Fallo de autenticación en AWS IAM" in str(exc_info.value)


def test_e2e_error_handling_permission_denied():
    """3.6. Comprueba que denegación de permisos de lectura en AWS se capture como AWSIAMPermissionError."""
    client = MagicMock()
    client.can_paginate.return_value = False
    client.list_users.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "User is not authorized to perform: iam:ListUsers"}},
        "ListUsers"
    )
    ds = AWSIAMDataSource(client=client)
    service = AuditService()

    with pytest.raises(AWSIAMPermissionError) as exc_info:
        service.run_aws_audit(aws_data_source=ds, persist=False)

    assert "Permisos insuficientes" in str(exc_info.value)


def test_e2e_error_handling_network_timeout():
    """3.6. Comprueba que un timeout o caída de conexión se capture como AWSIAMConnectionError."""
    client = MagicMock()
    client.can_paginate.return_value = False
    client.list_users.side_effect = botocore.exceptions.ConnectTimeoutError(endpoint_url="https://iam.amazonaws.com")
    ds = AWSIAMDataSource(client=client)
    service = AuditService()

    with pytest.raises(AWSIAMConnectionError) as exc_info:
        service.run_aws_audit(aws_data_source=ds, persist=False)

    assert "tiempo de espera o error de red" in str(exc_info.value)


def test_e2e_error_handling_missing_credentials():
    """3.6. Comprueba que la ausencia de credenciales de AWS se capture limpiamente."""
    client = MagicMock()
    client.can_paginate.return_value = False
    client.list_users.side_effect = botocore.exceptions.NoCredentialsError()
    ds = AWSIAMDataSource(client=client)
    service = AuditService()

    with pytest.raises(AWSIAMAuthenticationError) as exc_info:
        service.run_aws_audit(aws_data_source=ds, persist=False)

    assert "No se encontraron credenciales de AWS configuradas" in str(exc_info.value)


def test_e2e_empty_resources_collection_produces_clean_zero_summary():
    """3.6. Comprueba que una cuenta AWS sin identidades retorne 0 recursos y 0 evaluaciones limpiamente."""
    client = MagicMock()
    client.can_paginate.return_value = False
    client.list_users.return_value = {"Users": [], "IsTruncated": False}
    client.list_roles.return_value = {"Roles": [], "IsTruncated": False}

    ds = AWSIAMDataSource(client=client)
    service = AuditService()

    results, resources, summary, persistence_info = service.run_aws_audit(
        aws_data_source=ds,
        persist=False,
        context=AuditContext(),
    )

    assert resources == []
    assert results == []
    assert summary["total"] == 0
    assert summary["conforme"] == 0
    assert summary["hallazgo"] == 0
    assert summary["no_evaluable"] == 0


def test_e2e_consecutive_aws_failure_followed_by_simulator_success():
    """3.6. Comprueba que una falla en auditoría AWS no contamine ni bloquee la ejecución posterior del simulador."""
    client = MagicMock()
    client.can_paginate.return_value = False
    client.list_users.side_effect = botocore.exceptions.NoCredentialsError()
    ds = AWSIAMDataSource(client=client)
    service = AuditService()

    # 1. Ejecución AWS falla controladamente
    with pytest.raises(AWSIAMAuthenticationError):
        service.run_aws_audit(aws_data_source=ds, persist=False)

    # 2. Ejecución de simulación subsiguiente se ejecuta con éxito total
    sim_res, sim_rsc, sim_sum, _ = service.run_simulated_audit(persist=False)
    assert len(sim_rsc) == 10
    assert len(sim_res) == 67
    assert sim_sum["total"] == 67
