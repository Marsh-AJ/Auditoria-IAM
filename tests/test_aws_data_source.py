"""
Pruebas unitarias para el adaptador de datos AWS IAM (AWSIAMDataSource).
Verifica consultas de solo lectura, paginación, manejo de errores de credenciales/permisos,
normalización, políticas de grupos, compatibilidad con AuditEngine y contexto independiente.
"""
from datetime import datetime, timezone, timedelta
import inspect
from unittest.mock import MagicMock

import botocore.exceptions
import pytest

from src.auditoria_iam.audit.engine import AuditEngine
from src.auditoria_iam.audit.models import AuditContext
from src.auditoria_iam.audit.rules.iam_003_access_rights import RuleIAM003AccessRights
from src.auditoria_iam.data_sources.aws import (
    AWSIAMAuthenticationError,
    AWSIAMConnectionError,
    AWSIAMDataSource,
    AWSIAMDataSourceError,
    AWSIAMPermissionError,
    READ_ONLY_OPERATIONS,
)


@pytest.fixture
def mock_iam_client():
    """Crea un cliente simulado de AWS IAM con métodos estándar de solo lectura configurados."""
    client = MagicMock()
    # Desactivar paginador por defecto para usar fallback determinista
    client.can_paginate.return_value = False
    return client


def test_aws_query_users(mock_iam_client):
    """1. Verifica la consulta y normalización de usuarios IAM."""
    mock_iam_client.list_users.return_value = {
        "Users": [
            {
                "UserName": "mario.lopez",
                "UserId": "AIDAMARIOLOPEZ123",
                "Arn": "arn:aws:iam::123456789012:user/mario.lopez",
                "CreateDate": datetime.now(timezone.utc),
            }
        ],
        "IsTruncated": False
    }
    mock_iam_client.list_groups_for_user.return_value = {"Groups": [{"GroupName": "Operaciones"}]}
    mock_iam_client.list_mfa_devices.return_value = {"MFADevices": [{"SerialNumber": "arn:mfa:123"}]}
    mock_iam_client.list_access_keys.return_value = {"AccessKeyMetadata": []}
    mock_iam_client.list_user_policies.return_value = {"PolicyNames": []}
    mock_iam_client.list_attached_user_policies.return_value = {"AttachedPolicies": []}
    mock_iam_client.list_attached_group_policies.return_value = {"AttachedPolicies": []}
    mock_iam_client.list_group_policies.return_value = {"PolicyNames": []}

    ds = AWSIAMDataSource(client=mock_iam_client)
    users = ds.get_users()

    assert len(users) == 1
    u = users[0]
    assert u["resource_key"] == "mario.lopez"
    assert u["resource_type"] == "IAM_USER"
    assert u["source_type"] == "aws"
    assert u["resource_status"] == "active"
    assert u["attributes"]["groups"] == ["Operaciones"]
    assert u["attributes"]["mfa_enabled"] is True


def test_aws_query_groups_and_membership(mock_iam_client):
    """2. Verifica la consulta de grupos IAM y sus miembros asociados."""
    mock_iam_client.list_groups.return_value = {
        "Groups": [
            {
                "GroupName": "SeguridadTI",
                "Arn": "arn:aws:iam::123456789012:group/SeguridadTI",
                "Path": "/seguridad/"
            }
        ],
        "IsTruncated": False
    }
    mock_iam_client.get_group.return_value = {
        "Group": {"GroupName": "SeguridadTI"},
        "Users": [
            {"UserName": "carlos.soporte"},
            {"UserName": "laura.auditor"}
        ]
    }
    mock_iam_client.list_attached_group_policies.return_value = {"AttachedPolicies": []}
    mock_iam_client.list_group_policies.return_value = {"PolicyNames": []}

    ds = AWSIAMDataSource(client=mock_iam_client)
    groups = ds.get_groups()

    assert len(groups) == 1
    g = groups[0]
    assert g["group_name"] == "SeguridadTI"
    assert g["arn"] == "arn:aws:iam::123456789012:group/SeguridadTI"
    assert "carlos.soporte" in g["members"]
    assert "laura.auditor" in g["members"]


def test_aws_query_roles_and_trust_policies(mock_iam_client):
    """3. Verifica la consulta de roles y normalización de la política de confianza."""
    trust_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    mock_iam_client.list_roles.return_value = {
        "Roles": [
            {
                "RoleName": "RolEC2App",
                "Arn": "arn:aws:iam::123456789012:role/RolEC2App",
                "Path": "/",
                "AssumeRolePolicyDocument": trust_doc,
                "RoleLastUsed": {"LastUsedDate": datetime.now(timezone.utc) - timedelta(days=5)}
            }
        ],
        "IsTruncated": False
    }
    mock_iam_client.list_role_policies.return_value = {"PolicyNames": []}
    mock_iam_client.list_attached_role_policies.return_value = {"AttachedPolicies": []}

    ds = AWSIAMDataSource(client=mock_iam_client)
    roles = ds.get_roles()

    assert len(roles) == 1
    r = roles[0]
    assert r["resource_key"] == "RolEC2App"
    assert r["resource_type"] == "IAM_ROLE"
    assert r["attributes"]["assume_role_policy_document"] == trust_doc
    assert r["attributes"]["last_access_days"] == 5


def test_aws_query_managed_policies(mock_iam_client):
    """4. Verifica la consulta de políticas administradas y resolución de versión predeterminada."""
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "s3:GetObject", "Resource": "*"}]
    }
    mock_iam_client.get_policy.return_value = {
        "Policy": {"DefaultVersionId": "v3"}
    }
    mock_iam_client.get_policy_version.return_value = {
        "PolicyVersion": {"Document": policy_doc}
    }

    ds = AWSIAMDataSource(client=mock_iam_client)
    doc = ds._get_managed_policy_document("arn:aws:iam::aws:policy/ReadOnlyAccess")

    assert doc == policy_doc
    # Segunda llamada debe usar la caché sin invocar de nuevo get_policy
    doc_cached = ds._get_managed_policy_document("arn:aws:iam::aws:policy/ReadOnlyAccess")
    assert doc_cached == policy_doc
    assert mock_iam_client.get_policy.call_count == 1


def test_aws_query_inline_policies(mock_iam_client):
    """5. Verifica la consulta de políticas integradas (inline) codificadas en URL o dict."""
    url_encoded_doc = "%7B%22Version%22%3A%222012-10-17%22%2C%22Statement%22%3A%5B%7B%22Effect%22%3A%22Allow%22%2C%22Action%22%3A%22s3%3AListBucket%22%2C%22Resource%22%3A%22%2A%22%7D%5D%7D"
    mock_iam_client.list_user_policies.return_value = {"PolicyNames": ["InlineS3"]}
    mock_iam_client.get_user_policy.return_value = {"PolicyDocument": url_encoded_doc}
    mock_iam_client.list_attached_user_policies.return_value = {"AttachedPolicies": []}

    ds = AWSIAMDataSource(client=mock_iam_client)
    policies = ds._get_user_policies("usuario.test")

    assert len(policies) == 1
    assert policies[0]["Statement"][0]["Action"] == "s3:ListBucket"
    assert policies[0]["_source_type"] == "user_inline"


def test_aws_query_mfa_devices(mock_iam_client):
    """6. Verifica la detección de dispositivos MFA para usuarios."""
    mock_iam_client.list_mfa_devices.side_effect = [
        {"MFADevices": [{"SerialNumber": "arn:aws:iam::123:mfa/user1"}]},
        {"MFADevices": []}
    ]

    ds = AWSIAMDataSource(client=mock_iam_client)
    assert ds._check_user_mfa("user.con_mfa") is True
    assert ds._check_user_mfa("user.sin_mfa") is False


def test_aws_activity_metadata_calculation(mock_iam_client):
    """7. Verifica el cálculo de días de inactividad a partir de consola y access keys."""
    now_utc = datetime.now(timezone.utc)
    user_with_pwd = {"PasswordLastUsed": now_utc - timedelta(days=12)}
    mock_iam_client.list_access_keys.return_value = {
        "AccessKeyMetadata": [{"AccessKeyId": "AKIA123"}]
    }
    mock_iam_client.get_access_key_last_used.return_value = {
        "AccessKeyLastUsed": {"LastUsedDate": now_utc - timedelta(days=4)}
    }

    ds = AWSIAMDataSource(client=mock_iam_client)
    # Debe tomar la más reciente (4 días)
    days = ds._get_user_last_access_days(user_with_pwd, "user1")
    assert days == 4

    # Usuario sin actividad alguna
    mock_iam_client.list_access_keys.return_value = {"AccessKeyMetadata": []}
    days_none = ds._get_user_last_access_days({}, "user_inactivo")
    assert days_none is None


def test_aws_pagination_handling(mock_iam_client):
    """8. Verifica el manejo de paginación para listas que superan el tamaño de página."""
    mock_iam_client.list_users.side_effect = [
        {
            "Users": [{"UserName": "user.p1", "Arn": "arn:aws:iam::123:user/p1"}],
            "IsTruncated": True,
            "Marker": "token_pagina_2"
        },
        {
            "Users": [{"UserName": "user.p2", "Arn": "arn:aws:iam::123:user/p2"}],
            "IsTruncated": False
        }
    ]
    mock_iam_client.list_groups_for_user.return_value = {"Groups": []}
    mock_iam_client.list_mfa_devices.return_value = {"MFADevices": []}
    mock_iam_client.list_access_keys.return_value = {"AccessKeyMetadata": []}
    mock_iam_client.list_user_policies.return_value = {"PolicyNames": []}
    mock_iam_client.list_attached_user_policies.return_value = {"AttachedPolicies": []}

    ds = AWSIAMDataSource(client=mock_iam_client)
    users = ds.get_users()

    assert len(users) == 2
    assert users[0]["resource_key"] == "user.p1"
    assert users[1]["resource_key"] == "user.p2"


def test_aws_credentials_error_handling(mock_iam_client):
    """9. Verifica el manejo controlado de errores de autenticación y credenciales ausentes."""
    mock_iam_client.list_users.side_effect = botocore.exceptions.NoCredentialsError()

    ds = AWSIAMDataSource(client=mock_iam_client)
    with pytest.raises(AWSIAMAuthenticationError) as exc_info:
        ds.get_users()

    assert "No se encontraron credenciales de AWS" in str(exc_info.value)
    # Verificar que no exponga detalles internos
    assert "AKIA" not in str(exc_info.value)


def test_aws_permission_error_handling(mock_iam_client):
    """10. Verifica el manejo controlado de errores de permisos insuficientes (AccessDenied)."""
    error_response = {
        "Error": {
            "Code": "AccessDenied",
            "Message": "User: arn:aws:iam::123:user/audit is not authorized to perform: iam:ListUsers"
        }
    }
    mock_iam_client.list_users.side_effect = botocore.exceptions.ClientError(error_response, "ListUsers")

    ds = AWSIAMDataSource(client=mock_iam_client)
    with pytest.raises(AWSIAMPermissionError) as exc_info:
        ds.get_users()

    assert "Permisos insuficientes" in str(exc_info.value)


def test_aws_incomplete_responses_defensive(mock_iam_client):
    """11. Verifica la resiliencia frente a respuestas parciales o elementos incompletos."""
    mock_iam_client.list_users.return_value = {
        "Users": [
            {},  # Usuario sin UserName
            {"UserName": "user.incompleto"}
        ],
        "IsTruncated": False
    }
    mock_iam_client.list_groups_for_user.return_value = {}
    mock_iam_client.list_mfa_devices.return_value = {}
    mock_iam_client.list_access_keys.return_value = {}
    mock_iam_client.list_user_policies.return_value = {}
    mock_iam_client.list_attached_user_policies.return_value = {}

    ds = AWSIAMDataSource(client=mock_iam_client)
    users = ds.get_users()

    assert len(users) == 1
    assert users[0]["resource_key"] == "user.incompleto"
    assert users[0]["attributes"]["groups"] == []
    assert users[0]["attributes"]["mfa_enabled"] is False
    assert users[0]["attributes"]["last_access_days"] is None


def test_aws_normalization_format(mock_iam_client):
    """12. Verifica que el esquema normalizado contenga todas las claves requeridas por el repositorio."""
    mock_iam_client.list_users.return_value = {
        "Users": [{"UserName": "ana.nube", "Arn": "arn:aws:iam::123:user/ana.nube"}],
        "IsTruncated": False
    }
    mock_iam_client.list_groups_for_user.return_value = {"Groups": []}
    mock_iam_client.list_mfa_devices.return_value = {"MFADevices": []}
    mock_iam_client.list_access_keys.return_value = {"AccessKeyMetadata": []}
    mock_iam_client.list_user_policies.return_value = {"PolicyNames": []}
    mock_iam_client.list_attached_user_policies.return_value = {"AttachedPolicies": []}

    ds = AWSIAMDataSource(client=mock_iam_client)
    users = ds.get_users()
    u = users[0]

    required_keys = {"id", "resource_key", "resource_type", "display_name", "source_type", "resource_status", "attributes"}
    assert required_keys.issubset(u.keys())
    assert {"groups", "last_access_days", "mfa_enabled", "policies"}.issubset(u["attributes"].keys())


def test_aws_engine_compatibility_with_independent_context(mock_iam_client):
    """
    13. Verifica que los recursos normalizados de AWS sean evaluables directamente por AuditEngine
    utilizando un AuditContext de referencia independiente (sin usar el simulador).
    """
    mock_iam_client.list_users.return_value = {
        "Users": [{"UserName": "usuario.aws", "Arn": "arn:aws:iam::123:user/usuario.aws"}],
        "IsTruncated": False
    }
    mock_iam_client.list_groups_for_user.return_value = {"Groups": [{"GroupName": "OperacionesNube"}]}
    mock_iam_client.list_mfa_devices.return_value = {"MFADevices": [{"SerialNumber": "arn:mfa:1"}]}
    mock_iam_client.list_access_keys.return_value = {"AccessKeyMetadata": []}
    mock_iam_client.list_user_policies.return_value = {"PolicyNames": []}
    mock_iam_client.list_attached_user_policies.return_value = {"AttachedPolicies": []}
    mock_iam_client.list_attached_group_policies.return_value = {"AttachedPolicies": []}
    mock_iam_client.list_group_policies.return_value = {"PolicyNames": []}
    mock_iam_client.list_roles.return_value = {"Roles": [], "IsTruncated": False}

    ds = AWSIAMDataSource(client=mock_iam_client, id_offset=1)
    resources = ds.get_resources()

    # Contexto de referencia corporativo independiente del simulador
    independent_context = AuditContext(
        profiles={
            10: {
                "id": 10,
                "profile_code": "PRF-AWS-OPS",
                "profile_name": "Perfil Operaciones Nube",
                "identity_type": "user",
                "version": "1.0",
                "status": "active"
            }
        },
        expected_groups={10: ["OperacionesNube"]},
        expected_trust_principals={},
        resource_profiles={2: 10}  # id_offset(1) + 1 = ID 2
    )

    engine = AuditEngine()
    results = engine.evaluate_all(resources=resources, context=independent_context)
    assert len(results) > 0

    valid_statuses = {"Conforme", "Hallazgo", "No evaluable"}
    for res in results:
        assert res.result_status in valid_statuses


def test_aws_strictly_read_only_no_write_operations(mock_iam_client):
    """
    14. Verificación exhaustiva de que el adaptador opera exclusivamente en modo lectura
    y rechaza categóricamente cualquier operación de escritura, modificación o remediación.
    """
    ds = AWSIAMDataSource(client=mock_iam_client)

    # 1. Verificar catálogo estricto de operaciones de lectura
    for op in READ_ONLY_OPERATIONS:
        assert op.startswith("get_") or op.startswith("list_"), f"Operación sospechosa: {op}"

    # 2. Intentar operaciones de modificación explícitas debe lanzar excepción
    forbidden_calls = [
        "create_user",
        "update_user",
        "delete_user",
        "put_user_policy",
        "attach_user_policy",
        "detach_user_policy",
        "create_access_key",
        "delete_access_key",
        "enable_mfa_device",
        "deactivate_mfa_device",
        "add_user_to_group",
        "remove_user_from_group",
    ]

    for forbidden in forbidden_calls:
        with pytest.raises(AWSIAMDataSourceError) as exc_info:
            ds._validate_safe_operation(forbidden)
        err_msg = str(exc_info.value).lower()
        assert "escritura rechazada" in err_msg or "no autorizada" in err_msg or "no permitida" in err_msg

    # 3. Comprobar que ningún método público del adaptador implemente escritura
    adapter_methods = [name for name, _ in inspect.getmembers(AWSIAMDataSource, predicate=inspect.isfunction)]
    for m in adapter_methods:
        for prefix in ("create", "update", "delete", "put", "attach", "detach", "enable", "disable", "remove", "add"):
            assert not m.startswith(prefix), f"Método con prefijo de escritura encontrado: {m}"


# =========================================================================
# PRUEBAS ESPECÍFICAS — OBSERVACIÓN 1: POLÍTICAS ASOCIADAS A GRUPOS IAM
# =========================================================================

def test_aws_group_managed_policies_query(mock_iam_client):
    """15. Verifica la consulta de políticas administradas asociadas a grupos IAM."""
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::corp-data/*"}]
    }
    mock_iam_client.list_attached_group_policies.return_value = {
        "AttachedPolicies": [
            {"PolicyName": "CorpS3Read", "PolicyArn": "arn:aws:iam::123:policy/CorpS3Read"}
        ]
    }
    mock_iam_client.list_group_policies.return_value = {"PolicyNames": []}
    mock_iam_client.get_policy.return_value = {"Policy": {"DefaultVersionId": "v1"}}
    mock_iam_client.get_policy_version.return_value = {"PolicyVersion": {"Document": policy_doc}}

    ds = AWSIAMDataSource(client=mock_iam_client)
    group_policies = ds._get_group_policies("DevOps")

    assert len(group_policies) == 1
    gp = group_policies[0]
    assert gp["_source_type"] == "group_managed"
    assert gp["_source_name"] == "CorpS3Read"
    assert gp["_group_name"] == "DevOps"
    assert gp["Statement"][0]["Action"] == "s3:GetObject"


def test_aws_group_inline_policies_query(mock_iam_client):
    """16. Verifica la consulta de políticas integradas (inline) asociadas a grupos IAM."""
    inline_doc = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "ec2:DescribeInstances", "Resource": "*"}]
    }
    mock_iam_client.list_attached_group_policies.return_value = {"AttachedPolicies": []}
    mock_iam_client.list_group_policies.return_value = {"PolicyNames": ["DevOpsInlineEC2"]}
    mock_iam_client.get_group_policy.return_value = {"PolicyDocument": inline_doc}

    ds = AWSIAMDataSource(client=mock_iam_client)
    group_policies = ds._get_group_policies("DevOps")

    assert len(group_policies) == 1
    gp = group_policies[0]
    assert gp["_source_type"] == "group_inline"
    assert gp["_source_name"] == "DevOpsInlineEC2"
    assert gp["_group_name"] == "DevOps"
    assert gp["Statement"][0]["Action"] == "ec2:DescribeInstances"


def test_aws_group_managed_policy_default_version(mock_iam_client):
    """17. Verifica la obtención y resolución de la versión predeterminada en políticas de grupo."""
    mock_iam_client.list_attached_group_policies.return_value = {
        "AttachedPolicies": [{"PolicyName": "PolCustom", "PolicyArn": "arn:aws:iam::123:policy/PolCustom"}]
    }
    mock_iam_client.list_group_policies.return_value = {"PolicyNames": []}
    mock_iam_client.get_policy.return_value = {"Policy": {"DefaultVersionId": "v5"}}
    mock_iam_client.get_policy_version.return_value = {
        "PolicyVersion": {
            "Document": {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "sqs:ReceiveMessage", "Resource": "*"}]}
        }
    }

    ds = AWSIAMDataSource(client=mock_iam_client)
    policies = ds._get_group_policies("Mensajeria")

    mock_iam_client.get_policy.assert_called_once_with(PolicyArn="arn:aws:iam::123:policy/PolCustom")
    mock_iam_client.get_policy_version.assert_called_once_with(
        PolicyArn="arn:aws:iam::123:policy/PolCustom",
        VersionId="v5"
    )
    assert policies[0]["Statement"][0]["Action"] == "sqs:ReceiveMessage"


def test_aws_group_policy_json_normalization(mock_iam_client):
    """18. Verifica la normalización de políticas de grupo expresadas como cadenas o URL-encoded."""
    raw_url_json = "%7B%22Version%22%3A%222012-10-17%22%2C%22Statement%22%3A%5B%7B%22Effect%22%3A%22Allow%22%2C%22Action%22%3A%22dynamodb%3AGetItem%22%2C%22Resource%22%3A%22%2A%22%7D%5D%7D"
    mock_iam_client.list_attached_group_policies.return_value = {"AttachedPolicies": []}
    mock_iam_client.list_group_policies.return_value = {"PolicyNames": ["DynamoInline"]}
    mock_iam_client.get_group_policy.return_value = {"PolicyDocument": raw_url_json}

    ds = AWSIAMDataSource(client=mock_iam_client)
    policies = ds._get_group_policies("BaseDatos")

    assert len(policies) == 1
    assert isinstance(policies[0]["Statement"], list)
    assert policies[0]["Statement"][0]["Action"] == "dynamodb:GetItem"


def test_aws_user_group_policy_association_and_provenance(mock_iam_client):
    """19. Verifica la relación de políticas entre grupos y usuarios, evitando duplicaciones y conservando procedencia."""
    # Política directa inline
    mock_iam_client.list_user_policies.return_value = {"PolicyNames": ["UserInlineDirect"]}
    mock_iam_client.get_user_policy.return_value = {
        "PolicyDocument": {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:ListBucket", "Resource": "*"}]}
    }
    # Política directa managed
    mock_iam_client.list_attached_user_policies.return_value = {
        "AttachedPolicies": [{"PolicyName": "SharedManaged", "PolicyArn": "arn:aws:iam::123:policy/SharedManaged"}]
    }

    # Políticas de grupo (incluye una política administrada idéntica a la directa para comprobar deduplicación)
    mock_iam_client.list_attached_group_policies.return_value = {
        "AttachedPolicies": [
            {"PolicyName": "SharedManaged", "PolicyArn": "arn:aws:iam::123:policy/SharedManaged"},
            {"PolicyName": "UniqueGroupManaged", "PolicyArn": "arn:aws:iam::123:policy/UniqueGroupManaged"}
        ]
    }
    mock_iam_client.list_group_policies.return_value = {"PolicyNames": ["GroupInlineOnly"]}
    mock_iam_client.get_group_policy.return_value = {
        "PolicyDocument": {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "ec2:Describe*", "Resource": "*"}]}
    }

    mock_iam_client.get_policy.side_effect = lambda PolicyArn: {"Policy": {"DefaultVersionId": "v1"}}
    mock_iam_client.get_policy_version.side_effect = lambda PolicyArn, VersionId: {
        "PolicyVersion": {"Document": {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:GetObject", "Resource": "*"}]}}
    }

    ds = AWSIAMDataSource(client=mock_iam_client)
    policies = ds._get_user_policies("usuario.mixto", user_groups=["GrupoDevOps"])

    # 1 direct inline + 1 direct managed + 1 unique group managed + 1 group inline = 4 políticas (SharedManaged no duplicada)
    assert len(policies) == 4

    source_types = [p["_source_type"] for p in policies]
    assert "user_inline" in source_types
    assert "user_managed" in source_types
    assert "group_managed" in source_types
    assert "group_inline" in source_types


def test_aws_group_policy_wildcard_detection_in_iam_003(mock_iam_client):
    """20. Verifica que IAM-003 detecte patrones de permisos excesivamente amplios (*/*) heredados de un grupo."""
    # Usuario sin políticas directas
    mock_iam_client.list_user_policies.return_value = {"PolicyNames": []}
    mock_iam_client.list_attached_user_policies.return_value = {"AttachedPolicies": []}

    # Grupo con política excesivamente amplia (* / *)
    wildcard_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "*"
            }
        ]
    }
    mock_iam_client.list_attached_group_policies.return_value = {
        "AttachedPolicies": [{"PolicyName": "AdminWildcardGroup", "PolicyArn": "arn:aws:iam::123:policy/AdminWildcardGroup"}]
    }
    mock_iam_client.list_group_policies.return_value = {"PolicyNames": []}
    mock_iam_client.get_policy.return_value = {"Policy": {"DefaultVersionId": "v1"}}
    mock_iam_client.get_policy_version.return_value = {"PolicyVersion": {"Document": wildcard_doc}}

    ds = AWSIAMDataSource(client=mock_iam_client)
    policies = ds._get_user_policies("empleado.admin", user_groups=["Administradores"])

    user_resource = {
        "id": 1005,
        "resource_key": "empleado.admin",
        "resource_type": "IAM_USER",
        "display_name": "empleado.admin",
        "source_type": "aws",
        "resource_status": "active",
        "attributes": {
            "groups": ["Administradores"],
            "policies": policies
        }
    }

    rule = RuleIAM003AccessRights()
    results = rule.evaluate(user_resource, context=None)

    c18_01 = next(r for r in results if r.criterion_code == "C18-01")
    assert c18_01.result_status == "Hallazgo"
    assert "full_wildcard" in c18_01.details.get("patterns_detected", [])
    assert c18_01.evidence.get("findings_count") == 1


def test_aws_group_policy_error_and_permission_handling(mock_iam_client):
    """21. Verifica el manejo controlado de errores y permisos insuficientes al consultar políticas de grupo."""
    error_response = {
        "Error": {
            "Code": "AccessDenied",
            "Message": "User is not authorized to perform iam:ListAttachedGroupPolicies"
        }
    }
    mock_iam_client.list_attached_group_policies.side_effect = botocore.exceptions.ClientError(
        error_response, "ListAttachedGroupPolicies"
    )

    ds = AWSIAMDataSource(client=mock_iam_client)

    # Invocación con raise_on_error=True debe propagar AWSIAMPermissionError
    with pytest.raises(AWSIAMPermissionError) as exc_info:
        ds._get_group_policies("GrupoRestringido", raise_on_error=True)
    assert "Permisos insuficientes" in str(exc_info.value)

    # Invocación en flujo de usuario (raise_on_error=False) debe registrar política incompleta
    # para que IAM-003 emita 'No evaluable' en lugar de falsear 'Conforme'
    mock_iam_client.list_user_policies.return_value = {"PolicyNames": []}
    mock_iam_client.list_attached_user_policies.return_value = {"AttachedPolicies": []}

    policies = ds._get_user_policies("usuario.restringido", user_groups=["GrupoRestringido"])
    assert len(policies) == 1
    assert policies[0]["_incomplete_policy"] is True

    user_resource = {
        "id": 1006,
        "resource_key": "usuario.restringido",
        "resource_type": "IAM_USER",
        "display_name": "usuario.restringido",
        "source_type": "aws",
        "resource_status": "active",
        "attributes": {
            "groups": ["GrupoRestringido"],
            "policies": policies
        }
    }

    rule = RuleIAM003AccessRights()
    results = rule.evaluate(user_resource, context=None)
    c18_01 = next(r for r in results if r.criterion_code == "C18-01")
    assert c18_01.result_status == "No evaluable"


# =========================================================================
# PRUEBAS ESPECÍFICAS — OBSERVACIÓN 2: CONTEXTO DE AUDITORÍA INDEPENDIENTE
# =========================================================================

def test_aws_engine_integration_with_independent_reference_context(mock_iam_client):
    """
    22. Verifica la evaluación completa de recursos AWS utilizando un AuditContext de referencia
    corporativo totalmente independiente del simulador.
    """
    # 1. Configurar usuario AWS
    mock_iam_client.list_users.return_value = {
        "Users": [
            {
                "UserName": "patricia.devops",
                "UserId": "AIDAPATRICIA123",
                "Arn": "arn:aws:iam::123:user/patricia.devops"
            }
        ],
        "IsTruncated": False
    }
    mock_iam_client.list_groups_for_user.return_value = {"Groups": [{"GroupName": "DevOpsTeam"}]}
    mock_iam_client.list_mfa_devices.return_value = {"MFADevices": [{"SerialNumber": "arn:mfa:patricia"}]}
    mock_iam_client.list_access_keys.return_value = {
        "AccessKeyMetadata": [{"AccessKeyId": "AKIAUSERPATRICIA"}]
    }
    mock_iam_client.get_access_key_last_used.return_value = {
        "AccessKeyLastUsed": {"LastUsedDate": datetime.now(timezone.utc) - timedelta(days=7)}
    }
    mock_iam_client.list_user_policies.return_value = {"PolicyNames": []}
    mock_iam_client.list_attached_user_policies.return_value = {"AttachedPolicies": []}
    mock_iam_client.list_attached_group_policies.return_value = {"AttachedPolicies": []}
    mock_iam_client.list_group_policies.return_value = {"PolicyNames": []}

    # 2. Configurar rol AWS
    role_trust_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    mock_iam_client.list_roles.return_value = {
        "Roles": [
            {
                "RoleName": "RolBackendWorker",
                "Arn": "arn:aws:iam::123:role/RolBackendWorker",
                "Path": "/",
                "AssumeRolePolicyDocument": role_trust_doc
            }
        ],
        "IsTruncated": False
    }
    mock_iam_client.list_role_policies.return_value = {"PolicyNames": []}
    mock_iam_client.list_attached_role_policies.return_value = {"AttachedPolicies": []}

    ds = AWSIAMDataSource(client=mock_iam_client, id_offset=2000)
    resources = ds.get_resources()

    user_id = resources[0]["id"]  # 2001
    role_id = resources[1]["id"]  # 2003

    # Contexto de referencia corporativo independiente (definido ad-hoc sin simulador)
    independent_corp_context = AuditContext(
        profiles={
            101: {
                "id": 101,
                "profile_code": "PRF-CORP-DEVOPS",
                "profile_name": "Perfil Corporativo DevOps",
                "identity_type": "user",
                "version": "1.0",
                "status": "active"
            },
            201: {
                "id": 201,
                "profile_code": "PRF-CORP-BACKEND-ROLE",
                "profile_name": "Perfil Rol Backend EC2",
                "identity_type": "role",
                "version": "1.0",
                "status": "active"
            }
        },
        expected_groups={101: ["DevOpsTeam"]},
        expected_trust_principals={
            201: [
                {
                    "principal_type": "service",
                    "principal_identifier": "ec2.amazonaws.com",
                    "trust_action": "sts:AssumeRole"
                }
            ]
        },
        resource_profiles={
            user_id: 101,
            role_id: 201
        }
    )

    engine = AuditEngine()
    results = engine.evaluate_all(resources=resources, context=independent_corp_context)

    # Validar resultados del usuario
    user_results = [r for r in results if r.resource_id == user_id]
    user_c15_01 = next(r for r in user_results if r.criterion_code == "C15-01")
    assert user_c15_01.result_status == "Conforme"  # Coincide con 'DevOpsTeam'

    user_c16_01 = next(r for r in user_results if r.criterion_code == "C16-01")
    assert user_c16_01.result_status == "Conforme"  # Activo

    user_c16_02 = next(r for r in user_results if r.criterion_code == "C16-02")
    assert user_c16_02.result_status == "Conforme"  # 7 días < 90

    user_c85_01 = next(r for r in user_results if r.criterion_code == "C85-01")
    assert user_c85_01.result_status == "Conforme"  # MFA activo

    # Validar resultados del rol
    role_results = [r for r in results if r.resource_id == role_id]
    role_c15_02 = next(r for r in role_results if r.criterion_code == "C15-02")
    assert role_c15_02.result_status == "Conforme"  # Confianza ec2.amazonaws.com autorizada


def test_aws_engine_no_evaluable_when_missing_reference_profiles(mock_iam_client):
    """
    23. Verifica que cuando un recurso AWS no cuenta con perfil o referencia de auditoría
    asignada en el contexto, el motor genera estrictamente 'No evaluable' sin inventar perfiles.
    """
    mock_iam_client.list_users.return_value = {
        "Users": [{"UserName": "usuario.externo", "Arn": "arn:aws:iam::123:user/usuario.externo"}],
        "IsTruncated": False
    }
    mock_iam_client.list_groups_for_user.return_value = {"Groups": [{"GroupName": "GrupoExterno"}]}
    mock_iam_client.list_mfa_devices.return_value = {"MFADevices": []}
    mock_iam_client.list_access_keys.return_value = {"AccessKeyMetadata": []}
    mock_iam_client.list_user_policies.return_value = {"PolicyNames": []}
    mock_iam_client.list_attached_user_policies.return_value = {"AttachedPolicies": []}
    mock_iam_client.list_attached_group_policies.return_value = {"AttachedPolicies": []}
    mock_iam_client.list_group_policies.return_value = {"PolicyNames": []}

    ds = AWSIAMDataSource(client=mock_iam_client, id_offset=3000)
    users = ds.get_users()
    u_id = users[0]["id"]

    # Contexto vacío sin perfil asignado para este recurso
    empty_context = AuditContext(
        profiles={},
        expected_groups={},
        expected_trust_principals={},
        resource_profiles={}  # No existe mapeo para u_id
    )

    engine = AuditEngine()
    results = engine.evaluate_all(resources=users, context=empty_context)

    # Criterios dependientes de perfil autorizado deben ser estrictamente 'No evaluable'
    c15_01 = next(r for r in results if r.criterion_code == "C15-01")
    assert c15_01.result_status == "No evaluable"
    assert "perfil de referencia" in c15_01.justification.lower()
    assert c15_01.evidence.get("missing_profile") is True

    c15_03 = next(r for r in results if r.criterion_code == "C15-03")
    assert c15_03.result_status == "No evaluable"

    c18_02 = next(r for r in results if r.criterion_code == "C18-02")
    assert c18_02.result_status == "No evaluable"


# =========================================================================
# PRUEBAS ESPECÍFICAS — PREVENCIÓN DE OMISIONES Y MARCADOR INCOMPLETO
# =========================================================================

def test_aws_group_managed_policy_unretrievable_marker_no_evaluable(mock_iam_client):
    """
    24. Verifica que si una política administrada de grupo no puede recuperarse (get_policy retorna None),
    se registre una política incompleta y IAM-003 emita 'No evaluable' evitando un falso 'Conforme'.
    """
    mock_iam_client.list_attached_group_policies.return_value = {
        "AttachedPolicies": [{"PolicyName": "PoliticaInaccesible", "PolicyArn": "arn:aws:iam::123:policy/Inaccesible"}]
    }
    mock_iam_client.list_group_policies.return_value = {"PolicyNames": []}
    mock_iam_client.get_policy.return_value = {}  # No retorna DefaultVersionId

    ds = AWSIAMDataSource(client=mock_iam_client)
    group_policies = ds._get_group_policies("GrupoOps")

    assert len(group_policies) == 1
    assert group_policies[0]["_incomplete_policy"] is True
    assert group_policies[0]["_source_type"] == "group_managed"
    assert group_policies[0]["Statement"] is None

    user_resource = {
        "id": 1010,
        "resource_key": "usuario.grupo_incompleto",
        "resource_type": "IAM_USER",
        "display_name": "usuario.grupo_incompleto",
        "source_type": "aws",
        "resource_status": "active",
        "attributes": {
            "groups": ["GrupoOps"],
            "policies": group_policies
        }
    }

    rule = RuleIAM003AccessRights()
    results = rule.evaluate(user_resource, context=None)
    c18_01 = next(r for r in results if r.criterion_code == "C18-01")

    assert c18_01.result_status == "No evaluable"
    assert c18_01.result_status != "Conforme"
    assert c18_01.evidence.get("missing_statement") is True


def test_aws_group_inline_policy_invalid_doc_marker_no_evaluable(mock_iam_client):
    """
    25. Verifica que si una política integrada de grupo contiene un documento JSON inválido,
    se registre el marcador incompleto y IAM-003 emita 'No evaluable'.
    """
    mock_iam_client.list_attached_group_policies.return_value = {"AttachedPolicies": []}
    mock_iam_client.list_group_policies.return_value = {"PolicyNames": ["InlineDanada"]}
    mock_iam_client.get_group_policy.return_value = {"PolicyDocument": "{esto no es json valido"}

    ds = AWSIAMDataSource(client=mock_iam_client)
    group_policies = ds._get_group_policies("GrupoDanado")

    assert len(group_policies) == 1
    assert group_policies[0]["_incomplete_policy"] is True
    assert group_policies[0]["_source_type"] == "group_inline"
    assert group_policies[0]["Statement"] is None

    user_resource = {
        "id": 1011,
        "resource_key": "usuario.inline_invalido",
        "resource_type": "IAM_USER",
        "display_name": "usuario.inline_invalido",
        "source_type": "aws",
        "resource_status": "active",
        "attributes": {
            "groups": ["GrupoDanado"],
            "policies": group_policies
        }
    }

    rule = RuleIAM003AccessRights()
    results = rule.evaluate(user_resource, context=None)
    c18_01 = next(r for r in results if r.criterion_code == "C18-01")

    assert c18_01.result_status == "No evaluable"
    assert c18_01.result_status != "Conforme"


def test_aws_user_direct_policy_unretrievable_marker_no_evaluable(mock_iam_client):
    """
    26. Verifica que si una política directa (inline o managed) de un usuario no puede recuperarse,
    no se omita silenciosamente y provoque 'No evaluable' en IAM-003.
    """
    # Inline dañada y managed no recuperable
    mock_iam_client.list_user_policies.return_value = {"PolicyNames": ["UserInlineRota"]}
    mock_iam_client.get_user_policy.return_value = {"PolicyDocument": "invalido"}
    mock_iam_client.list_attached_user_policies.return_value = {
        "AttachedPolicies": [{"PolicyName": "ManagedRota", "PolicyArn": "arn:aws:iam::123:policy/ManagedRota"}]
    }
    mock_iam_client.get_policy.return_value = None

    ds = AWSIAMDataSource(client=mock_iam_client)
    policies = ds._get_user_policies("usuario.politica_rota")

    assert len(policies) == 2
    for p in policies:
        assert p["_incomplete_policy"] is True
        assert p["Statement"] is None

    user_resource = {
        "id": 1012,
        "resource_key": "usuario.politica_rota",
        "resource_type": "IAM_USER",
        "display_name": "usuario.politica_rota",
        "source_type": "aws",
        "resource_status": "active",
        "attributes": {
            "groups": [],
            "policies": policies
        }
    }

    rule = RuleIAM003AccessRights()
    results = rule.evaluate(user_resource, context=None)
    c18_01 = next(r for r in results if r.criterion_code == "C18-01")

    assert c18_01.result_status == "No evaluable"
    assert c18_01.result_status != "Conforme"


def test_aws_role_policy_unretrievable_marker_no_evaluable(mock_iam_client):
    """
    27. Verifica que si una política asignada a un rol no puede recuperarse,
    no se omita silenciosamente y provoque 'No evaluable' en IAM-003 para ese rol.
    """
    mock_iam_client.list_role_policies.return_value = {"PolicyNames": ["RoleInlineRota"]}
    mock_iam_client.get_role_policy.return_value = {"PolicyDocument": None}
    mock_iam_client.list_attached_role_policies.return_value = {"AttachedPolicies": []}

    ds = AWSIAMDataSource(client=mock_iam_client)
    role_policies = ds._get_role_policies("RolConPoliticaRota")

    assert len(role_policies) == 1
    assert role_policies[0]["_incomplete_policy"] is True
    assert role_policies[0]["Statement"] is None

    role_resource = {
        "id": 2012,
        "resource_key": "RolConPoliticaRota",
        "resource_type": "IAM_ROLE",
        "display_name": "RolConPoliticaRota",
        "source_type": "aws",
        "resource_status": "active",
        "attributes": {
            "assume_role_policy_document": {
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}]
            },
            "policies": role_policies
        }
    }

    rule = RuleIAM003AccessRights()
    results = rule.evaluate(role_resource, context=None)
    c18_01 = next(r for r in results if r.criterion_code == "C18-01")

    assert c18_01.result_status == "No evaluable"
    assert c18_01.result_status != "Conforme"


def test_aws_valid_policies_still_detect_wildcard_patterns(mock_iam_client):
    """
    28. Verifica que cuando todas las políticas son válidas, las políticas con patrones excesivamente
    amplios (* y *) continúen detectándose con estado 'Hallazgo'.
    """
    scoped_doc = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::bucket/*"}]
    }
    wildcard_doc = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]
    }

    mock_iam_client.list_user_policies.return_value = {"PolicyNames": ["ScopedUserInline"]}
    mock_iam_client.get_user_policy.return_value = {"PolicyDocument": scoped_doc}
    mock_iam_client.list_attached_user_policies.return_value = {
        "AttachedPolicies": [{"PolicyName": "WildcardManaged", "PolicyArn": "arn:aws:iam::123:policy/WildcardManaged"}]
    }
    mock_iam_client.get_policy.return_value = {"Policy": {"DefaultVersionId": "v1"}}
    mock_iam_client.get_policy_version.return_value = {"PolicyVersion": {"Document": wildcard_doc}}

    ds = AWSIAMDataSource(client=mock_iam_client)
    policies = ds._get_user_policies("usuario.con_wildcard")

    assert len(policies) == 2

    user_resource = {
        "id": 1013,
        "resource_key": "usuario.con_wildcard",
        "resource_type": "IAM_USER",
        "display_name": "usuario.con_wildcard",
        "source_type": "aws",
        "resource_status": "active",
        "attributes": {
            "groups": [],
            "policies": policies
        }
    }

    rule = RuleIAM003AccessRights()
    results = rule.evaluate(user_resource, context=None)
    c18_01 = next(r for r in results if r.criterion_code == "C18-01")

    assert c18_01.result_status == "Hallazgo"
    assert "full_wildcard" in c18_01.details.get("patterns_detected", [])

