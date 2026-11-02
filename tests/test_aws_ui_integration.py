"""
Pruebas de integración para la fuente de datos AWS IAM con la interfaz de escritorio (PySide6)
y el servicio de aplicación (AuditService) en la Fase 7, Entrega 7.1.

Verifica:
1. Carga de perfiles mediante la función real del repositorio (get_active_profiles).
2. Asociación de perfiles por resource_key para usuarios y roles AWS.
3. Evaluación correcta de reglas IAM-001, IAM-002, IAM-003 e IAM-004 sobre recursos AWS.
4. Ausencia de falsos conformes cuando falta el perfil de referencia.
5. Persistencia transaccional con source_type='aws' y manejo de recursos no registrados.
6. Preservación y exportación de resultados en memoria ante fallos de persistencia.
7. Manejo defensivo de credenciales ausentes, permisos insuficientes y errores de conexión.
8. Modo estrictamente de solo lectura en AWS IAM sin operaciones de modificación.
"""
from datetime import datetime, timedelta, timezone
import json
import os
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication
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
from src.auditoria_iam.ui.main_window import MainWindow
from src.auditoria_iam.ui.pages.audit_page import AuditPage


@pytest.fixture
def mock_iam_client():
    """Crea un cliente simulado de IAM Boto3 con datos deterministas representativos."""
    client = MagicMock()
    client.can_paginate.return_value = False

    client.get_user.return_value = {
        "User": {
            "UserName": "patricia.devops",
            "Arn": "arn:aws:iam::123456789012:user/patricia.devops",
            "CreateDate": datetime.now(timezone.utc) - timedelta(days=60),
            "PasswordLastUsed": datetime.now(timezone.utc) - timedelta(days=5),
        }
    }
    client.list_users.return_value = {
        "Users": [
            {
                "UserName": "patricia.devops",
                "Arn": "arn:aws:iam::123456789012:user/patricia.devops",
                "CreateDate": datetime.now(timezone.utc) - timedelta(days=60),
                "PasswordLastUsed": datetime.now(timezone.utc) - timedelta(days=5),
            }
        ],
        "IsTruncated": False,
    }
    client.list_access_keys.return_value = {
        "AccessKeyMetadata": [
            {
                "UserName": "patricia.devops",
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "Status": "Active",
                "CreateDate": datetime.now(timezone.utc) - timedelta(days=30),
            }
        ],
        "IsTruncated": False,
    }
    client.get_access_key_last_used.return_value = {
        "UserName": "patricia.devops",
        "AccessKeyLastUsed": {
            "LastUsedDate": datetime.now(timezone.utc) - timedelta(days=5),
            "ServiceName": "s3",
            "Region": "us-east-1",
        },
    }
    client.list_mfa_devices.return_value = {
        "MFADevices": [
            {
                "UserName": "patricia.devops",
                "SerialNumber": "arn:aws:iam::123456789012:mfa/patricia.devops",
                "EnableDate": datetime.now(timezone.utc) - timedelta(days=60),
            }
        ],
        "IsTruncated": False,
    }
    client.list_groups_for_user.return_value = {
        "Groups": [{"GroupName": "DevOpsTeam"}],
        "IsTruncated": False,
    }
    client.list_user_policies.return_value = {"PolicyNames": []}
    client.list_attached_user_policies.return_value = {"AttachedPolicies": []}

    role_trust_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    client.list_roles.return_value = {
        "Roles": [
            {
                "RoleName": "RolServidorApp",
                "Arn": "arn:aws:iam::123456789012:role/RolServidorApp",
                "Path": "/",
                "AssumeRolePolicyDocument": role_trust_doc,
                "RoleLastUsed": {"LastUsedDate": datetime.now(timezone.utc) - timedelta(days=2)},
            }
        ],
        "IsTruncated": False,
    }
    client.list_role_policies.return_value = {"PolicyNames": []}
    client.list_attached_role_policies.return_value = {"AttachedPolicies": []}
    client.list_groups.return_value = {"Groups": [{"GroupName": "DevOpsTeam"}], "IsTruncated": False}
    client.get_group.return_value = {"Group": {"GroupName": "DevOpsTeam"}, "Users": [{"UserName": "patricia.devops"}]}

    return client


# =============================================================================
# 1. CARGA DE PERFILES MEDIANTE LA FUNCIÓN REAL DEL REPOSITORIO
# =============================================================================

def test_load_aws_audit_context_using_real_repository_function():
    """1. Comprueba la carga de perfiles mediante la función real del repositorio (get_active_profiles)."""
    service = AuditService()

    fake_profiles = [
        {
            "id": 1,
            "profile_code": "PRF-DEV-01",
            "profile_name": "Perfil DevOps",
            "identity_type": "user",
            "version": "1.0",
            "description": "Perfil de prueba",
            "status": "active",
        }
    ]
    fake_groups = [{"group_name": "DevOpsTeam"}]
    fake_trust = [{"principal_type": "AWS", "principal_identifier": "arn:aws:iam::123456789012:root", "trust_action": "sts:AssumeRole"}]
    fake_db_resources = [{"id": 10, "resource_key": "patricia.devops", "source_type": "aws"}]
    fake_active_profile = {"profile_id": 1}

    with patch("src.auditoria_iam.database.repository.get_active_profiles", return_value=fake_profiles) as mock_gap, \
         patch("src.auditoria_iam.database.repository.get_profile_expected_groups", return_value=fake_groups), \
         patch("src.auditoria_iam.database.repository.get_profile_expected_trust_principals", return_value=fake_trust), \
         patch("src.auditoria_iam.database.repository.get_resources", return_value=fake_db_resources), \
         patch("src.auditoria_iam.database.repository.get_resource_active_profile", return_value=fake_active_profile):

        context = service._load_aws_audit_context()
        mock_gap.assert_called_once()
        assert 1 in context.profiles
        assert context.profiles[1]["profile_code"] == "PRF-DEV-01"
        assert context.expected_groups[1] == ["DevOpsTeam"]
        assert context.resource_profiles[10] == 1
        assert context.resource_key_profiles["patricia.devops"] == 1


def test_load_aws_audit_context_database_error_raises_runtime_error():
    """Comprueba que errores de conexión/consulta en MySQL no se conviertan silenciosamente en contexto vacío."""
    service = AuditService()
    with patch(
        "src.auditoria_iam.database.repository.get_active_profiles",
        side_effect=RuntimeError("Error al conectar con la base de datos MySQL."),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            service._load_aws_audit_context()
        assert "No se pudo cargar la configuración de perfiles" in str(exc_info.value)


# =============================================================================
# 2. ASOCIACIÓN DE PERFIL POR resource_key PARA USUARIOS AWS
# =============================================================================

def test_aws_user_profile_association_via_resource_key():
    """2. Comprueba la asociación de un usuario AWS con su perfil mediante resource_key."""
    context = AuditContext(
        profiles={1: {"id": 1, "profile_code": "PRF-DEV-01", "status": "active", "identity_type": "user"}},
        resource_key_profiles={"patricia.devops": 1},
    )

    # Resolución directa por clave textual
    profile_by_key = context.get_profile_for_resource("patricia.devops")
    assert profile_by_key is not None
    assert profile_by_key["profile_code"] == "PRF-DEV-01"

    # Resolución con ID numérico en memoria y resource_key
    profile_with_id = context.get_profile_for_resource(1001, resource_key="patricia.devops")
    assert profile_with_id is not None
    assert profile_with_id["profile_code"] == "PRF-DEV-01"


# =============================================================================
# 3. ASOCIACIÓN DE PERFIL POR resource_key PARA ROLES AWS
# =============================================================================

def test_aws_role_profile_association_via_resource_key():
    """3. Comprueba la asociación de un rol AWS con su perfil mediante resource_key."""
    context = AuditContext(
        profiles={2: {"id": 2, "profile_code": "PRF-ROL-01", "status": "active", "identity_type": "role"}},
        resource_key_profiles={"RolServidorApp": 2},
    )

    # Resolución directa por clave textual
    profile_by_key = context.get_profile_for_resource("RolServidorApp")
    assert profile_by_key is not None
    assert profile_by_key["profile_code"] == "PRF-ROL-01"

    # Resolución con ID en memoria y resource_key
    profile_with_id = context.get_profile_for_resource(1002, resource_key="RolServidorApp")
    assert profile_with_id is not None
    assert profile_with_id["profile_code"] == "PRF-ROL-01"


# =============================================================================
# 4. AUSENCIA DE PERFIL PRODUCE No evaluable SIN FALSOS CONFORMES
# =============================================================================

def test_missing_profile_produces_no_evaluable_without_false_conforme():
    """4. Comprueba que identidades AWS sin perfil asignado produzcan estrictamente 'No evaluable'."""
    context = AuditContext(
        profiles={},
        resource_profiles={},
        resource_key_profiles={},
    )
    rule = RuleIAM001AccessControl()

    user_without_profile = {
        "id": 1001,
        "resource_key": "user.unassigned",
        "resource_type": "IAM_USER",
        "attributes": {"groups": ["DevOpsTeam"]},
    }
    results = rule.evaluate(user_without_profile, context)

    assert len(results) == 2
    # Criterios C15-03 y C15-01 deben ser 'No evaluable'
    assert all(r.result_status == "No evaluable" for r in results)
    assert not any(r.result_status == "Conforme" for r in results)
    assert not any(r.result_status == "Hallazgo" for r in results)


# =============================================================================
# 5. IAM-001 EVALÚA GRUPOS Y PRINCIPALES DE CONFIANZA CON PERFIL VÁLIDO
# =============================================================================

def test_iam_001_evaluates_groups_and_trust_when_valid_profile_exists():
    """5. Comprueba que IAM-001 evalúe grupos y confianza cuando existe un perfil válido asociado."""
    rule = RuleIAM001AccessControl()
    context = AuditContext(
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
            "unauthorized.dev": 1,
            "RolServidorApp": 2,
        },
    )

    # 1. Usuario con grupos conformes
    conforme_user = {
        "id": 1001,
        "resource_key": "patricia.devops",
        "resource_type": "IAM_USER",
        "attributes": {"groups": ["DevOpsTeam"]},
    }
    res_user = rule.evaluate(conforme_user, context)
    c15_01 = next(r for r in res_user if r.criterion_code == "C15-01")
    assert c15_01.result_status == "Conforme"

    # 2. Usuario con grupos no autorizados (Hallazgo)
    hallazgo_user = {
        "id": 1002,
        "resource_key": "unauthorized.dev",
        "resource_type": "IAM_USER",
        "attributes": {"groups": ["DevOpsTeam", "UnauthorizedGroup"]},
    }
    res_user_h = rule.evaluate(hallazgo_user, context)
    c15_01_h = next(r for r in res_user_h if r.criterion_code == "C15-01")
    assert c15_01_h.result_status == "Hallazgo"

    # 3. Rol con entidad de confianza conforme
    conforme_role = {
        "id": 1003,
        "resource_key": "RolServidorApp",
        "resource_type": "IAM_ROLE",
        "attributes": {
            "assume_role_policy_document": {
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
                        "Action": "sts:AssumeRole",
                    }
                ]
            }
        },
    }
    res_role = rule.evaluate(conforme_role, context)
    c15_02 = next(r for r in res_role if r.criterion_code == "C15-02")
    assert c15_02.result_status == "Conforme"


# =============================================================================
# 6. IAM-002 EVALÚA ACTIVIDAD MEDIANTE last_access_days
# =============================================================================

def test_iam_002_evaluates_activity_via_last_access_days():
    """6. Comprueba que IAM-002 continúe evaluando la actividad frente al umbral de inactividad."""
    rule = RuleIAM002IdentityManagement(inactivity_threshold_days=90)

    # Actividad reciente dentro de umbral (Conforme)
    u_active = {"id": 1, "resource_status": "active", "attributes": {"last_access_days": 10}}
    res_a = rule.evaluate(u_active)
    c16_02_a = next(r for r in res_a if r.criterion_code == "C16-02")
    assert c16_02_a.result_status == "Conforme"

    # Inactividad excesiva que supera umbral (Hallazgo)
    u_inactive = {"id": 2, "resource_status": "active", "attributes": {"last_access_days": 150}}
    res_i = rule.evaluate(u_inactive)
    c16_02_i = next(r for r in res_i if r.criterion_code == "C16-02")
    assert c16_02_i.result_status == "Hallazgo"

    # Sin metadatos de actividad (No evaluable)
    u_none = {"id": 3, "resource_status": "active", "attributes": {"last_access_days": None}}
    res_n = rule.evaluate(u_none)
    c16_02_n = next(r for r in res_n if r.criterion_code == "C16-02")
    assert c16_02_n.result_status == "No evaluable"


# =============================================================================
# 7. IAM-003 ANALIZA POLÍTICAS IAM NORMALIZADAS
# =============================================================================

def test_iam_003_analyzes_normalized_policies():
    """7. Comprueba que IAM-003 continúe analizando las políticas técnicas JSON en busca de comodines."""
    rule = RuleIAM003AccessRights()

    # Política restringida sin comodines excesivos (Conforme)
    u_restricted = {
        "id": 1,
        "attributes": {
            "policies": [
                {
                    "Statement": [
                        {"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "arn:aws:s3:::mybucket/*"}
                    ]
                }
            ]
        },
    }
    res_r = rule.evaluate(u_restricted)
    c18_01_r = next(r for r in res_r if r.criterion_code == "C18-01")
    assert c18_01_r.result_status == "Conforme"

    # Política con comodines globales Action:* y Resource:* (Hallazgo)
    u_wildcard = {
        "id": 2,
        "attributes": {
            "policies": [
                {
                    "Statement": [
                        {"Effect": "Allow", "Action": "*", "Resource": "*"}
                    ]
                }
            ]
        },
    }
    res_w = rule.evaluate(u_wildcard)
    c18_01_w = next(r for r in res_w if r.criterion_code == "C18-01")
    assert c18_01_w.result_status == "Hallazgo"

    # Marcador de política incompleta / inalcanzable (No evaluable)
    u_marker = {
        "id": 3,
        "attributes": {
            "policies": [
                {"_incomplete_policy": True, "Statement": None}
            ]
        },
    }
    res_m = rule.evaluate(u_marker)
    c18_01_m = next(r for r in res_m if r.criterion_code == "C18-01")
    assert c18_01_m.result_status == "No evaluable"


# =============================================================================
# 8. IAM-004 EVALÚA MFA ÚNICAMENTE PARA USUARIOS
# =============================================================================

def test_iam_004_evaluates_mfa_only_for_users():
    """8. Comprueba que IAM-004 evalúe MFA únicamente para usuarios y excluya roles."""
    rule = RuleIAM004SecureAuthentication()

    # Usuario con MFA habilitado (Conforme)
    u_mfa = {"id": 1, "resource_type": "IAM_USER", "attributes": {"mfa_enabled": True}}
    res_u = rule.evaluate(u_mfa)
    assert len(res_u) == 1
    assert res_u[0].result_status == "Conforme"

    # Usuario sin MFA (Hallazgo)
    u_no_mfa = {"id": 2, "resource_type": "IAM_USER", "attributes": {"mfa_enabled": False}}
    res_no = rule.evaluate(u_no_mfa)
    assert len(res_no) == 1
    assert res_no[0].result_status == "Hallazgo"

    # Rol queda excluido de la evaluación de MFA interactivo (lista vacía)
    role = {"id": 3, "resource_type": "IAM_ROLE", "attributes": {"mfa_enabled": False}}
    res_role = rule.evaluate(role)
    assert res_role == []


# =============================================================================
# 9. PERSISTENCIA CON ROLLBACK CONTROLADO CUANDO FALTA UN RECURSO
# =============================================================================

def test_persistence_fails_with_controlled_rollback_when_resource_unregistered(mock_iam_client):
    """9. Comprueba que cuando un recurso AWS no existe en MySQL, la persistencia aborte con aviso claro y rollback."""
    ds = AWSIAMDataSource(client=mock_iam_client)
    service = AuditService()
    custom_context = AuditContext()

    with patch(
        "src.auditoria_iam.application.audit_service.save_audit_run",
        side_effect=RuntimeError(
            "El recurso con clave 'patricia.devops' y origen 'aws' no existe en la tabla 'resources' de MySQL. "
            "Falta registrar el recurso correspondiente. No se asignan identificadores de sustitución."
        ),
    ):
        results, resources, summary, p_info = service.run_aws_audit(
            persist=True,
            aws_data_source=ds,
            context=custom_context,
        )

        assert p_info["persisted"] is False
        assert p_info["run_id"] is None
        assert "no existe en la tabla 'resources'" in p_info["message"] or "faltan recursos" in p_info["message"]
        # Los resultados permanecen en memoria
        assert len(results) > 0
        assert len(resources) == 2


# =============================================================================
# 10. RESULTADOS DISPONIBLES EN MEMORIA Y EXPORTABLES AUNQUE PERSISTENCIA FALLE
# =============================================================================

def test_results_remain_in_memory_and_exportable_when_persistence_fails(qapp, mock_iam_client, tmp_path):
    """10. Comprueba que ante fallo de persistencia, los resultados permanezcan en memoria y sean exportables."""
    ds = AWSIAMDataSource(client=mock_iam_client)
    window = MainWindow()
    try:
        window.audit_service.aws_data_source = ds
        # Simular que el contexto se resuelve y que save_audit_run falla por recurso no registrado
        with patch.object(window.audit_service, "_load_aws_audit_context", return_value=AuditContext()), \
             patch(
                 "src.auditoria_iam.application.audit_service.save_audit_run",
                 side_effect=RuntimeError(
                     "El recurso con clave 'patricia.devops' y origen 'aws' no existe en la tabla 'resources' de MySQL."
                 ),
             ):

            audit_page = window.audit_page
            for i in range(audit_page.source_selector.count()):
                if audit_page.source_selector.itemData(i) == "aws":
                    audit_page.source_selector.setCurrentIndex(i)
                    break

            audit_page._on_execute_clicked()

            # El banner de aviso se despliega
            assert "Aviso de persistencia" in audit_page.status_message.text()
            assert not audit_page.view_results_button.isHidden()

            # Los resultados llegaron intactos a ResultsPage
            assert window.results_page.results_table.rowCount() > 0
            assert int(window.results_page.lbl_total.text()) > 0

            # Los resultados en memoria pueden exportarse sin dependencia de la base de datos
            csv_path = str(tmp_path / "test_export_aws.csv")
            gen_path = window.audit_service.export_audit_report(
                filepath=csv_path,
                format_type="csv",
                results=window.results_page._current_results,
                resources=window.results_page._current_resources,
                summary=window.results_page._current_summary,
            )
            assert os.path.exists(gen_path)
            assert os.path.getsize(gen_path) > 0
    finally:
        window.close()
        window.deleteLater()


# =============================================================================
# PRUEBAS COMPLEMENTARIAS DE INTEGRACIÓN UI Y ADAPTADOR
# =============================================================================

def test_aws_source_selection_enables_execution(qapp):
    """Verifica que la fuente AWS IAM pueda seleccionarse y habilite el botón de ejecución."""
    page = AuditPage()
    try:
        combo = page.source_selector
        aws_index = -1
        for i in range(combo.count()):
            if combo.itemData(i) == "aws":
                aws_index = i
                break

        assert aws_index >= 0, "No se encontró la opción 'aws' en el selector de fuentes."
        combo.setCurrentIndex(aws_index)

        assert page.execute_button.isEnabled() is True
        msg = page.status_message.text()
        assert "AWS IAM" in msg or "Boto3" in msg
        assert "solo lectura" in msg
    finally:
        page.close()
        page.deleteLater()


def test_audit_service_run_aws_audit_invokes_adapter(mock_iam_client):
    """Verifica que AuditService.run_aws_audit() invoque los métodos del adaptador AWSIAMDataSource."""
    ds = AWSIAMDataSource(client=mock_iam_client)
    service = AuditService()
    custom_context = AuditContext()

    with patch.object(ds, "get_resources", wraps=ds.get_resources) as spy_get_resources:
        results, resources, summary, p_info = service.run_aws_audit(
            persist=False,
            aws_data_source=ds,
            context=custom_context,
        )
        spy_get_resources.assert_called_once()
        assert len(resources) == 2
        assert summary["total"] == len(results)


def test_aws_resource_normalization_compatibility(mock_iam_client):
    """Comprueba que los recursos devueltos por el adaptador cumplan el esquema requerido por AuditEngine."""
    ds = AWSIAMDataSource(client=mock_iam_client)
    resources = ds.get_resources()

    assert len(resources) >= 2
    user_res = next(r for r in resources if r["resource_type"] == "IAM_USER")
    role_res = next(r for r in resources if r["resource_type"] == "IAM_ROLE")

    assert user_res["resource_key"] == "patricia.devops"
    assert user_res["source_type"] == "aws"
    assert user_res["resource_status"] == "active"
    assert user_res["attributes"]["groups"] == ["DevOpsTeam"]
    assert user_res["attributes"]["mfa_enabled"] is True
    assert user_res["attributes"]["last_access_days"] == 5

    assert role_res["resource_key"] == "RolServidorApp"
    assert role_res["source_type"] == "aws"
    assert role_res["resource_status"] == "active"
    assert role_res["attributes"]["assume_role_policy_document"] is not None


def test_delivery_of_resources_and_context_to_engine(mock_iam_client):
    """Verifica que el AuditService entregue fielmente la lista de recursos y el contexto al motor."""
    ds = AWSIAMDataSource(client=mock_iam_client)
    custom_context = AuditContext(profiles={})
    service = AuditService()

    with patch.object(service.engine, "evaluate_all", return_value=[]) as mock_eval:
        service.run_aws_audit(
            persist=False,
            aws_data_source=ds,
            context=custom_context,
        )
        mock_eval.assert_called_once()
        called_resources = mock_eval.call_args[1]["resources"]
        called_context = mock_eval.call_args[1]["context"]

        assert len(called_resources) == 2
        assert called_context is custom_context


def test_execution_of_all_four_rules_on_aws_resources(mock_iam_client):
    """Comprueba que las cuatro reglas (IAM-001 a IAM-004) se ejecuten sobre los recursos AWS."""
    ds = AWSIAMDataSource(client=mock_iam_client)
    service = AuditService()
    custom_context = AuditContext()

    results, resources, summary, _ = service.run_aws_audit(
        persist=False,
        aws_data_source=ds,
        context=custom_context,
    )

    rule_codes_evaluated = {r.rule_code for r in results}
    assert "IAM-001" in rule_codes_evaluated
    assert "IAM-002" in rule_codes_evaluated
    assert "IAM-003" in rule_codes_evaluated
    assert "IAM-004" in rule_codes_evaluated

    assert summary["total"] == len(results)
    assert summary["conforme"] + summary["hallazgo"] + summary["no_evaluable"] == summary["total"]


def test_aws_audit_persistence_identifies_source_type_aws(mock_iam_client):
    """Verifica que la persistencia en MySQL se invoque con source_type='aws'."""
    ds = AWSIAMDataSource(client=mock_iam_client)
    service = AuditService()
    custom_context = AuditContext()

    with patch("src.auditoria_iam.application.audit_service.save_audit_run", return_value=123) as mock_save:
        results, resources, summary, p_info = service.run_aws_audit(
            persist=True,
            aws_data_source=ds,
            context=custom_context,
        )
        mock_save.assert_called_once()
        assert mock_save.call_args[1]["source_type"] == "aws"
        assert p_info["persisted"] is True
        assert p_info["run_id"] == 123


def test_aws_results_presentation_in_ui(qapp, mock_iam_client):
    """Verifica que los resultados de una auditoría AWS se reflejen en la UI y habiliten 'Ver resultados'."""
    ds = AWSIAMDataSource(client=mock_iam_client)
    window = MainWindow()
    try:
        window.audit_service.aws_data_source = ds

        with patch.object(window.audit_service, "_load_aws_audit_context", return_value=AuditContext()), \
             patch("src.auditoria_iam.application.audit_service.save_audit_run", return_value=123):

            audit_page = window.audit_page
            for i in range(audit_page.source_selector.count()):
                if audit_page.source_selector.itemData(i) == "aws":
                    audit_page.source_selector.setCurrentIndex(i)
                    break

            audit_page._on_execute_clicked()

            assert not audit_page.view_results_button.isHidden()
            assert "✓ Auditoría finalizada correctamente (AWS IAM (Nube))" in audit_page.status_message.text()
            assert window.results_page.results_table.rowCount() > 0
            assert int(window.results_page.lbl_total.text()) > 0
    finally:
        window.close()
        window.deleteLater()


def test_missing_aws_credentials_handling(qapp):
    """Comprueba que la ausencia de credenciales AWS se maneje sin excepciones no controladas ni colapsos."""
    page = AuditPage()
    try:
        with patch.object(
            page._audit_service,
            "run_aws_audit",
            side_effect=AWSIAMAuthenticationError("No se encontraron credenciales de AWS configuradas en el entorno."),
        ):
            for i in range(page.source_selector.count()):
                if page.source_selector.itemData(i) == "aws":
                    page.source_selector.setCurrentIndex(i)
                    break

            page._on_execute_clicked()

            msg = page.status_message.text()
            assert "Error de autenticación en AWS" in msg
            assert "AWS_ACCESS_KEY_ID" in msg
            assert page.execute_button.isEnabled() is True
    finally:
        page.close()
        page.deleteLater()


def test_aws_permission_and_connection_errors_handling(qapp):
    """Comprueba que errores de permisos insuficientes y de conexión con el endpoint sean controlados."""
    page = AuditPage()
    try:
        for i in range(page.source_selector.count()):
            if page.source_selector.itemData(i) == "aws":
                page.source_selector.setCurrentIndex(i)
                break

        # Permisos insuficientes
        with patch.object(
            page._audit_service,
            "run_aws_audit",
            side_effect=AWSIAMPermissionError("Permisos insuficientes para ejecutar list_users en AWS IAM."),
        ):
            page._on_execute_clicked()
            assert "Permisos insuficientes en AWS IAM" in page.status_message.text()
            assert page.execute_button.isEnabled() is True

        # Error de conexión
        with patch.object(
            page._audit_service,
            "run_aws_audit",
            side_effect=AWSIAMConnectionError("No fue posible establecer conexión con el endpoint de AWS IAM."),
        ):
            page._on_execute_clicked()
            assert "Error de conexión con AWS IAM" in page.status_message.text()
            assert page.execute_button.isEnabled() is True
    finally:
        page.close()
        page.deleteLater()


def test_strict_no_write_operations_to_aws(mock_iam_client):
    """Verifica mediante inspección de llamadas que el adaptador nunca ejecuta operaciones de escritura en AWS."""
    ds = AWSIAMDataSource(client=mock_iam_client)
    ds.get_resources()

    called_methods = [call[0] for call in mock_iam_client.method_calls]
    for method_name in called_methods:
        if method_name in ("can_paginate", "get_paginator"):
            continue
        method_lower = method_name.lower()
        for prefix in FORBIDDEN_OPERATION_PREFIXES:
            assert not method_lower.startswith(prefix), f"Operación de escritura detectada: '{method_name}'"
        assert method_lower in READ_ONLY_OPERATIONS, f"Operación no autorizada de consulta: '{method_name}'"


def test_simulator_functionality_preserved():
    """Verifica que el flujo del simulador local permanezca plenamente operativo tras la integración."""
    service = AuditService()
    results, resources, summary, _ = service.run_simulated_audit(persist=False)
    assert len(resources) == 10
    assert len(results) == 67
    assert summary["total"] == 67
    assert summary["conforme"] > 0
    assert summary["hallazgo"] > 0
    assert summary["no_evaluable"] > 0


def test_existing_rules_unmodified_contract():
    """Verifica que las cuatro reglas de auditoría mantengan sus códigos, controles ISO y contratos intactos."""
    r1 = RuleIAM001AccessControl()
    r2 = RuleIAM002IdentityManagement()
    r3 = RuleIAM003AccessRights()
    r4 = RuleIAM004SecureAuthentication()

    assert r1.rule_code == "IAM-001" and r1.iso_control == "5.15"
    assert r2.rule_code == "IAM-002" and r2.iso_control == "5.16"
    assert r3.rule_code == "IAM-003" and r3.iso_control == "5.18"
    assert r4.rule_code == "IAM-004" and r4.iso_control == "8.5"
