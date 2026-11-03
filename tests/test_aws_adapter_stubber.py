"""
Validación técnica del adaptador AWS IAM (AWSIAMDataSource) mediante botocore.stub.Stubber.
Fase 7, Entrega 7.2.1.

Verifica:
1. Consultas de solo lectura con respuestas compatibles con botocore (usuarios, grupos, roles, políticas, MFA, actividad).
2. Paginación multi-página sin pérdida ni duplicación de recursos (paginadores Boto3 y fallback con Marker).
3. Manejo controlado de errores (NoCredentialsError, PartialCredentialsError, AccessDenied, InvalidClientTokenId, tiempos de espera, políticas inaccesibles).
4. Seguridad estricta de solo lectura (bloqueo preventivo de operaciones de escritura y verificación de llamadas realizadas).
5. Compatibilidad total de los recursos normalizados con el motor AuditEngine y las 4 reglas ISO/IEC 27001:2022.
"""
from datetime import datetime, timedelta, timezone
import json
from unittest.mock import MagicMock

import boto3
import botocore.exceptions
from botocore.stub import Stubber
import pytest

from src.auditoria_iam.audit.engine import AuditEngine
from src.auditoria_iam.audit.models import AuditContext
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


@pytest.fixture
def iam_stubber():
    """Crea un cliente Boto3 IAM y su correspondiente botocore.stub.Stubber."""
    client = boto3.client(
        "iam",
        region_name="us-east-1",
        aws_access_key_id="test_key_non_sensitive",
        aws_secret_access_key="test_secret_non_sensitive",
    )
    stubber = Stubber(client)
    yield client, stubber
    stubber.deactivate()


# =============================================================================
# 1. PRUEBAS DE CONSULTAS AWS IAM MEDIANTE STUBBER
# =============================================================================

def test_stubber_list_users_and_normalization(iam_stubber):
    """1. Comprueba la consulta y normalización de usuarios IAM mediante Stubber."""
    client, stubber = iam_stubber
    now = datetime.now(timezone.utc)

    stubber.add_response("list_users", {
        "Users": [
            {
                "Path": "/",
                "UserName": "patricia.devops",
                "UserId": "AIDA1234567890123456",
                "Arn": "arn:aws:iam::123456789012:user/patricia.devops",
                "CreateDate": now - timedelta(days=60),
                "PasswordLastUsed": now - timedelta(days=10),
            }
        ],
        "IsTruncated": False,
    })
    stubber.add_response("list_groups_for_user", {
        "Groups": [
            {
                "Path": "/",
                "GroupName": "DevOpsTeam",
                "GroupId": "AGPA1234567890123456",
                "Arn": "arn:aws:iam::123456789012:group/DevOpsTeam",
                "CreateDate": now - timedelta(days=60),
            }
        ],
        "IsTruncated": False,
    }, {"UserName": "patricia.devops"})
    stubber.add_response("list_mfa_devices", {
        "MFADevices": [
            {
                "UserName": "patricia.devops",
                "SerialNumber": "arn:aws:iam::123456789012:mfa/patricia.devops",
                "EnableDate": now - timedelta(days=60),
            }
        ],
        "IsTruncated": False,
    }, {"UserName": "patricia.devops"})
    stubber.add_response("list_access_keys", {"AccessKeyMetadata": [], "IsTruncated": False}, {"UserName": "patricia.devops"})
    stubber.add_response("list_user_policies", {"PolicyNames": [], "IsTruncated": False}, {"UserName": "patricia.devops"})
    stubber.add_response("list_attached_user_policies", {"AttachedPolicies": [], "IsTruncated": False}, {"UserName": "patricia.devops"})
    stubber.add_response("list_attached_group_policies", {"AttachedPolicies": [], "IsTruncated": False}, {"GroupName": "DevOpsTeam"})
    stubber.add_response("list_group_policies", {"PolicyNames": [], "IsTruncated": False}, {"GroupName": "DevOpsTeam"})

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    users = ds.get_users()
    stubber.assert_no_pending_responses()

    assert len(users) == 1
    u = users[0]
    assert u["resource_key"] == "patricia.devops"
    assert u["resource_type"] == "IAM_USER"
    assert u["source_type"] == "aws"
    assert u["resource_status"] == "active"
    assert u["attributes"]["mfa_enabled"] is True
    assert u["attributes"]["groups"] == ["DevOpsTeam"]
    assert u["attributes"]["last_access_days"] == 10


def test_stubber_query_groups_and_membership(iam_stubber):
    """2. Comprueba la consulta de grupos IAM y sus miembros asociados mediante Stubber."""
    client, stubber = iam_stubber
    now = datetime.now(timezone.utc)

    stubber.add_response("list_groups", {
        "Groups": [
            {
                "Path": "/seguridad/",
                "GroupName": "SeguridadTI",
                "GroupId": "AGPA1234567890123456",
                "Arn": "arn:aws:iam::123456789012:group/seguridad/SeguridadTI",
                "CreateDate": now,
            }
        ],
        "IsTruncated": False,
    })
    stubber.add_response("get_group", {
        "Group": {
            "Path": "/seguridad/",
            "GroupName": "SeguridadTI",
            "GroupId": "AGPA1234567890123456",
            "Arn": "arn:aws:iam::123456789012:group/seguridad/SeguridadTI",
            "CreateDate": now,
        },
        "Users": [
            {
                "Path": "/",
                "UserName": "carlos.soporte",
                "UserId": "AIDA1234567890123457",
                "Arn": "arn:aws:iam::123456789012:user/carlos.soporte",
                "CreateDate": now,
            },
            {
                "Path": "/",
                "UserName": "laura.auditor",
                "UserId": "AIDA1234567890123458",
                "Arn": "arn:aws:iam::123456789012:user/laura.auditor",
                "CreateDate": now,
            },
        ],
        "IsTruncated": False,
    }, {"GroupName": "SeguridadTI"})
    stubber.add_response("list_attached_group_policies", {"AttachedPolicies": [], "IsTruncated": False}, {"GroupName": "SeguridadTI"})
    stubber.add_response("list_group_policies", {"PolicyNames": [], "IsTruncated": False}, {"GroupName": "SeguridadTI"})

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    groups = ds.get_groups()
    stubber.assert_no_pending_responses()

    assert len(groups) == 1
    g = groups[0]
    assert g["group_name"] == "SeguridadTI"
    assert "carlos.soporte" in g["members"]
    assert "laura.auditor" in g["members"]


def test_stubber_query_mfa_devices_present_and_absent(iam_stubber):
    """3. Comprueba la detección de presencia y ausencia de dispositivos MFA mediante Stubber."""
    client, stubber = iam_stubber
    now = datetime.now(timezone.utc)

    # Caso A: Usuario con MFA habilitado
    stubber.add_response("list_mfa_devices", {
        "MFADevices": [
            {
                "UserName": "user.with.mfa",
                "SerialNumber": "arn:aws:iam::123456789012:mfa/user.with.mfa",
                "EnableDate": now,
            }
        ],
        "IsTruncated": False,
    }, {"UserName": "user.with.mfa"})

    # Caso B: Usuario sin MFA habilitado
    stubber.add_response("list_mfa_devices", {
        "MFADevices": [],
        "IsTruncated": False,
    }, {"UserName": "user.without.mfa"})

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    assert ds._check_user_mfa("user.with.mfa") is True
    assert ds._check_user_mfa("user.without.mfa") is False
    stubber.assert_no_pending_responses()


def test_stubber_list_roles_and_trust_policies(iam_stubber):
    """4. Comprueba la consulta de roles IAM y sus documentos de política de confianza (AssumeRolePolicyDocument)."""
    client, stubber = iam_stubber
    now = datetime.now(timezone.utc)

    trust_doc = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    })

    stubber.add_response("list_roles", {
        "Roles": [
            {
                "Path": "/",
                "RoleName": "RolServidorApp",
                "RoleId": "AROA1234567890123456",
                "Arn": "arn:aws:iam::123456789012:role/RolServidorApp",
                "CreateDate": now - timedelta(days=90),
                "AssumeRolePolicyDocument": trust_doc,
                "RoleLastUsed": {"LastUsedDate": now - timedelta(days=2)},
            }
        ],
        "IsTruncated": False,
    })
    # get_roles consulta internamente list_users para calcular el desfase de IDs deterministas
    stubber.add_response("list_users", {
        "Users": [
            {
                "Path": "/",
                "UserName": "patricia.devops",
                "UserId": "AIDA1234567890123456",
                "Arn": "arn:aws:iam::123456789012:user/patricia.devops",
                "CreateDate": now - timedelta(days=60),
            }
        ],
        "IsTruncated": False,
    })
    stubber.add_response("list_role_policies", {"PolicyNames": [], "IsTruncated": False}, {"RoleName": "RolServidorApp"})
    stubber.add_response("list_attached_role_policies", {"AttachedPolicies": [], "IsTruncated": False}, {"RoleName": "RolServidorApp"})

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    roles = ds.get_roles()
    stubber.assert_no_pending_responses()

    assert len(roles) == 1
    r = roles[0]
    assert r["resource_key"] == "RolServidorApp"
    assert r["resource_type"] == "IAM_ROLE"
    assert r["attributes"]["last_access_days"] == 2
    assert r["attributes"]["assume_role_policy_document"]["Statement"][0]["Effect"] == "Allow"


def test_stubber_query_inline_policies_user_and_role(iam_stubber):
    """5. Comprueba la recuperación de políticas integradas (inline) para usuarios y roles."""
    client, stubber = iam_stubber

    policy_doc = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "s3:ListBucket", "Resource": "arn:aws:s3:::upharven-bucket"}],
    })

    stubber.add_response("list_user_policies", {"PolicyNames": ["UserInlinePolicy"], "IsTruncated": False}, {"UserName": "user.inline"})
    stubber.add_response("get_user_policy", {
        "UserName": "user.inline",
        "PolicyName": "UserInlinePolicy",
        "PolicyDocument": policy_doc,
    }, {"UserName": "user.inline", "PolicyName": "UserInlinePolicy"})

    stubber.add_response("list_attached_user_policies", {"AttachedPolicies": [], "IsTruncated": False}, {"UserName": "user.inline"})

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    policies = ds._get_user_policies("user.inline")
    stubber.assert_no_pending_responses()

    assert len(policies) == 1
    p = policies[0]
    assert p["_source_type"] == "user_inline"
    assert p["_source_name"] == "UserInlinePolicy"
    assert p["Statement"][0]["Action"] == "s3:ListBucket"


def test_stubber_query_managed_policies_and_default_version(iam_stubber):
    """6. Comprueba la recuperación de políticas administradas adjuntas y su versión por defecto."""
    client, stubber = iam_stubber
    now = datetime.now(timezone.utc)

    policy_arn = "arn:aws:iam::123456789012:policy/CustomSecurityAudit"
    policy_doc = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": ["iam:Get*", "iam:List*"], "Resource": "*"}],
    })

    stubber.add_response("list_user_policies", {"PolicyNames": [], "IsTruncated": False}, {"UserName": "user.managed"})
    stubber.add_response("list_attached_user_policies", {
        "AttachedPolicies": [{"PolicyName": "CustomSecurityAudit", "PolicyArn": policy_arn}],
        "IsTruncated": False,
    }, {"UserName": "user.managed"})
    stubber.add_response("get_policy", {
        "Policy": {
            "PolicyName": "CustomSecurityAudit",
            "PolicyId": "ANPA1234567890123456",
            "Arn": policy_arn,
            "Path": "/",
            "DefaultVersionId": "v2",
            "AttachmentCount": 1,
            "IsAttachable": True,
            "CreateDate": now,
            "UpdateDate": now,
        }
    }, {"PolicyArn": policy_arn})
    stubber.add_response("get_policy_version", {
        "PolicyVersion": {
            "Document": policy_doc,
            "VersionId": "v2",
            "IsDefaultVersion": True,
            "CreateDate": now,
        }
    }, {"PolicyArn": policy_arn, "VersionId": "v2"})

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    policies = ds._get_user_policies("user.managed")
    stubber.assert_no_pending_responses()

    assert len(policies) == 1
    p = policies[0]
    assert p["_source_type"] == "user_managed"
    assert p["_source_name"] == "CustomSecurityAudit"
    assert p["_source_arn"] == policy_arn
    assert p["Statement"][0]["Effect"] == "Allow"


def test_stubber_query_group_inherited_policies(iam_stubber):
    """7. Comprueba la herencia y procedencia de políticas asociadas a través de grupos IAM."""
    client, stubber = iam_stubber

    group_inline_doc = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "ec2:DescribeInstances", "Resource": "*"}],
    })

    stubber.add_response("list_user_policies", {"PolicyNames": [], "IsTruncated": False}, {"UserName": "member.user"})
    stubber.add_response("list_attached_user_policies", {"AttachedPolicies": [], "IsTruncated": False}, {"UserName": "member.user"})
    stubber.add_response("list_attached_group_policies", {"AttachedPolicies": [], "IsTruncated": False}, {"GroupName": "DevOpsTeam"})
    stubber.add_response("list_group_policies", {"PolicyNames": ["DevOpsInline"], "IsTruncated": False}, {"GroupName": "DevOpsTeam"})
    stubber.add_response("get_group_policy", {
        "GroupName": "DevOpsTeam",
        "PolicyName": "DevOpsInline",
        "PolicyDocument": group_inline_doc,
    }, {"GroupName": "DevOpsTeam", "PolicyName": "DevOpsInline"})

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    policies = ds._get_user_policies("member.user", user_groups=["DevOpsTeam"])
    stubber.assert_no_pending_responses()

    assert len(policies) == 1
    p = policies[0]
    assert p["_source_type"] == "group_inline"
    assert p["_group_name"] == "DevOpsTeam"
    assert p["_source_name"] == "DevOpsInline"


def test_stubber_query_last_access_information_dates(iam_stubber):
    """8. Comprueba el cálculo de días de inactividad entre PasswordLastUsed y claves de acceso."""
    client, stubber = iam_stubber
    now = datetime.now(timezone.utc)

    user_meta = {
        "PasswordLastUsed": now - timedelta(days=40),
    }

    stubber.add_response("list_access_keys", {
        "AccessKeyMetadata": [
            {
                "UserName": "dual.user",
                "AccessKeyId": "AKIA1234567890123456",
                "Status": "Active",
                "CreateDate": now - timedelta(days=60),
            }
        ],
        "IsTruncated": False,
    }, {"UserName": "dual.user"})
    # La clave de acceso fue usada hace 15 días (más reciente que la contraseña de hace 40 días)
    stubber.add_response("get_access_key_last_used", {
        "UserName": "dual.user",
        "AccessKeyLastUsed": {
            "LastUsedDate": now - timedelta(days=15),
            "ServiceName": "s3",
            "Region": "us-east-1",
        },
    }, {"AccessKeyId": "AKIA1234567890123456"})

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    days = ds._get_user_last_access_days(user_meta, "dual.user")
    stubber.assert_no_pending_responses()

    # Debe tomar la fecha más reciente (hace 15 días)
    assert days == 15


# =============================================================================
# 2. PRUEBAS DE PAGINACIÓN MULTI-PÁGINA MEDIANTE STUBBER
# =============================================================================

def test_stubber_pagination_multi_page_users(iam_stubber):
    """9. Comprueba la recuperación de todas las páginas sin duplicados ni pérdida de recursos."""
    client, stubber = iam_stubber
    now = datetime.now(timezone.utc)

    # Página 1
    stubber.add_response("list_users", {
        "Users": [
            {
                "Path": "/",
                "UserName": "user.page1",
                "UserId": "AIDA1234567890123451",
                "Arn": "arn:aws:iam::123456789012:user/user.page1",
                "CreateDate": now,
            }
        ],
        "IsTruncated": True,
        "Marker": "next_page_token_123",
    })
    # Página 2
    stubber.add_response("list_users", {
        "Users": [
            {
                "Path": "/",
                "UserName": "user.page2",
                "UserId": "AIDA1234567890123452",
                "Arn": "arn:aws:iam::123456789012:user/user.page2",
                "CreateDate": now,
            }
        ],
        "IsTruncated": False,
    }, {"Marker": "next_page_token_123"})

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    raw_users = ds._paginate_or_call("list_users", "Users")
    stubber.assert_no_pending_responses()

    assert len(raw_users) == 2
    names = [u["UserName"] for u in raw_users]
    assert "user.page1" in names
    assert "user.page2" in names
    assert len(set(names)) == 2  # Sin duplicados


def test_stubber_pagination_multi_page_roles(iam_stubber):
    """10. Comprueba la paginación multi-página de roles IAM."""
    client, stubber = iam_stubber
    now = datetime.now(timezone.utc)
    trust_doc = json.dumps({"Version": "2012-10-17", "Statement": []})

    stubber.add_response("list_roles", {
        "Roles": [
            {
                "Path": "/",
                "RoleName": "RolePage1",
                "RoleId": "AROA1234567890123451",
                "Arn": "arn:aws:iam::123456789012:role/RolePage1",
                "CreateDate": now,
                "AssumeRolePolicyDocument": trust_doc,
            }
        ],
        "IsTruncated": True,
        "Marker": "role_marker_token",
    })
    stubber.add_response("list_roles", {
        "Roles": [
            {
                "Path": "/",
                "RoleName": "RolePage2",
                "RoleId": "AROA1234567890123452",
                "Arn": "arn:aws:iam::123456789012:role/RolePage2",
                "CreateDate": now,
                "AssumeRolePolicyDocument": trust_doc,
            }
        ],
        "IsTruncated": False,
    }, {"Marker": "role_marker_token"})

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    raw_roles = ds._paginate_or_call("list_roles", "Roles")
    stubber.assert_no_pending_responses()

    assert len(raw_roles) == 2
    r_names = [r["RoleName"] for r in raw_roles]
    assert "RolePage1" in r_names
    assert "RolePage2" in r_names


def test_stubber_pagination_empty_responses(iam_stubber):
    """11. Comprueba el manejo correcto de respuestas con colecciones vacías."""
    client, stubber = iam_stubber

    stubber.add_response("list_users", {
        "Users": [],
        "IsTruncated": False,
    })

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    users = ds.get_users()
    stubber.assert_no_pending_responses()

    assert users == []


# =============================================================================
# 3. PRUEBAS DE MANEJO DE ERRORES MEDIANTE STUBBER Y BOTOCORE
# =============================================================================

def test_stubber_error_access_denied_permission_error(iam_stubber):
    """12. Comprueba que ClientError con código AccessDenied se traduzca a AWSIAMPermissionError."""
    client, stubber = iam_stubber

    stubber.add_client_error(
        "list_users",
        service_error_code="AccessDenied",
        service_message="User is not authorized to perform: iam:ListUsers on resource: *",
    )

    stubber.activate()
    ds = AWSIAMDataSource(client=client)

    with pytest.raises(AWSIAMPermissionError) as exc_info:
        ds.get_users()

    assert "Permisos insuficientes" in str(exc_info.value)
    # Verificar que no expone datos sensibles ni tokens
    assert "SECRET" not in str(exc_info.value)
    assert "TOKEN" not in str(exc_info.value)


def test_stubber_error_invalid_client_token_id(iam_stubber):
    """13. Comprueba que ClientError con InvalidClientTokenId se traduzca a AWSIAMAuthenticationError."""
    client, stubber = iam_stubber

    stubber.add_client_error(
        "list_users",
        service_error_code="InvalidClientTokenId",
        service_message="The security token included in the request is invalid.",
    )

    stubber.activate()
    ds = AWSIAMDataSource(client=client)

    with pytest.raises(AWSIAMAuthenticationError) as exc_info:
        ds.get_users()

    assert "Fallo de autenticación" in str(exc_info.value)


def test_stubber_error_no_credentials_handling():
    """14. Comprueba la captura controlada de botocore.exceptions.NoCredentialsError."""
    mock_client = MagicMock()
    mock_client.can_paginate.return_value = False
    mock_client.list_users.side_effect = botocore.exceptions.NoCredentialsError()

    ds = AWSIAMDataSource(client=mock_client)
    with pytest.raises(AWSIAMAuthenticationError) as exc_info:
        ds.get_users()

    assert "No se encontraron credenciales de AWS" in str(exc_info.value)


def test_stubber_error_partial_credentials_handling():
    """15. Comprueba la captura controlada de botocore.exceptions.PartialCredentialsError."""
    mock_client = MagicMock()
    mock_client.can_paginate.return_value = False
    mock_client.list_users.side_effect = botocore.exceptions.PartialCredentialsError(
        provider="env", cred_var="AWS_SECRET_ACCESS_KEY"
    )

    ds = AWSIAMDataSource(client=mock_client)
    with pytest.raises(AWSIAMAuthenticationError) as exc_info:
        ds.get_users()

    assert "credenciales de AWS incompleta" in str(exc_info.value)


def test_stubber_error_endpoint_connection_and_timeouts():
    """16. Comprueba la captura controlada de fallos de red y tiempos de espera agotados."""
    mock_client = MagicMock()
    mock_client.can_paginate.return_value = False

    ds = AWSIAMDataSource(client=mock_client)

    # Caso A: EndpointConnectionError
    mock_client.list_users.side_effect = botocore.exceptions.EndpointConnectionError(endpoint_url="https://iam.amazonaws.com")
    with pytest.raises(AWSIAMConnectionError) as exc_info_a:
        ds.get_users()
    assert "No fue posible establecer conexión" in str(exc_info_a.value)

    # Caso B: ReadTimeoutError
    mock_client.list_users.side_effect = botocore.exceptions.ReadTimeoutError(endpoint_url="https://iam.amazonaws.com")
    with pytest.raises(AWSIAMConnectionError) as exc_info_b:
        ds.get_users()
    assert "tiempo de espera o error de red" in str(exc_info_b.value)

    # Caso C: ConnectTimeoutError
    mock_client.list_users.side_effect = botocore.exceptions.ConnectTimeoutError(endpoint_url="https://iam.amazonaws.com")
    with pytest.raises(AWSIAMConnectionError) as exc_info_c:
        ds.get_users()
    assert "tiempo de espera o error de red" in str(exc_info_c.value)


def test_stubber_unretrievable_policy_generates_incomplete_marker_and_no_evaluable(iam_stubber):
    """17. Comprueba que políticas que no pueden recuperarse generen marcador incompleto y 'No evaluable' en IAM-003."""
    client, stubber = iam_stubber

    # El listado de políticas indica que tiene una política adjunta
    stubber.add_response("list_user_policies", {"PolicyNames": ["UnreachablePolicy"], "IsTruncated": False}, {"UserName": "blocked.user"})
    # Al intentar consultar el documento, AWS deniega el permiso
    stubber.add_client_error(
        "get_user_policy",
        service_error_code="AccessDenied",
        service_message="Access denied to get policy document",
        expected_params={"UserName": "blocked.user", "PolicyName": "UnreachablePolicy"},
    )
    stubber.add_response("list_attached_user_policies", {"AttachedPolicies": [], "IsTruncated": False}, {"UserName": "blocked.user"})

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    policies = ds._get_user_policies("blocked.user")
    stubber.assert_no_pending_responses()

    # Debe contener un marcador de política incompleta
    assert len(policies) == 1
    marker = policies[0]
    assert marker["_incomplete_policy"] is True
    assert marker["Statement"] is None

    # Al evaluar con la regla IAM-003, debe resultar estrictamente 'No evaluable'
    rule = RuleIAM003AccessRights()
    resource = {
        "id": 1001,
        "resource_key": "blocked.user",
        "resource_type": "IAM_USER",
        "attributes": {"policies": policies},
    }
    results = rule.evaluate(resource)
    c18_01 = next(r for r in results if r.criterion_code == "C18-01")
    assert c18_01.result_status == "No evaluable"
    assert "missing_statement" in c18_01.evidence or "missing" in str(c18_01.evidence)


def test_stubber_malformed_policy_document_handling(iam_stubber):
    """18. Comprueba que documentos con sintaxis JSON malformada generen marcador incompleto."""
    client, stubber = iam_stubber

    stubber.add_response("list_user_policies", {"PolicyNames": ["MalformedPolicy"], "IsTruncated": False}, {"UserName": "corrupt.user"})
    stubber.add_response("get_user_policy", {
        "UserName": "corrupt.user",
        "PolicyName": "MalformedPolicy",
        "PolicyDocument": "{not valid json syntax",
    }, {"UserName": "corrupt.user", "PolicyName": "MalformedPolicy"})
    stubber.add_response("list_attached_user_policies", {"AttachedPolicies": [], "IsTruncated": False}, {"UserName": "corrupt.user"})

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    policies = ds._get_user_policies("corrupt.user")
    stubber.assert_no_pending_responses()

    assert len(policies) == 1
    assert policies[0]["_incomplete_policy"] is True
    assert policies[0]["Statement"] is None


# =============================================================================
# 4. SEGURIDAD ESTRICTA DE SOLO LECTURA
# =============================================================================

@pytest.mark.parametrize("forbidden_op", [
    "create_user",
    "delete_user",
    "update_user",
    "put_user_policy",
    "attach_user_policy",
    "detach_user_policy",
    "create_role",
    "delete_role",
    "update_role",
    "put_role_policy",
    "attach_role_policy",
    "detach_role_policy",
    "add_user_to_group",
    "remove_user_from_group",
    "create_group",
    "delete_group",
    "enable_mfa_device",
    "deactivate_mfa_device",
    "create_access_key",
    "delete_access_key",
    "update_access_key",
    "tag_user",
    "untag_user",
])
def test_stubber_strict_read_only_blocks_forbidden_operations(forbidden_op):
    """19. Verifica que cualquier método con prefijo de escritura sea rechazado antes de comunicarse con AWS."""
    client = MagicMock()
    ds = AWSIAMDataSource(client=client)

    with pytest.raises(AWSIAMDataSourceError) as exc_info:
        ds._validate_safe_operation(forbidden_op)

    assert "escritura rechazada por seguridad" in str(exc_info.value)
    # Ninguna llamada debe haber alcanzado al cliente
    client.assert_not_called()


def test_stubber_actual_dispatched_calls_strictly_read_only(iam_stubber):
    """20. Verifica que en una recolección completa real todas las operaciones ejecutadas pertenezcan a READ_ONLY_OPERATIONS."""
    client, stubber = iam_stubber
    now = datetime.now(timezone.utc)

    # Configurar usuario y rol
    stubber.add_response("list_users", {
        "Users": [
            {
                "Path": "/",
                "UserName": "audit.user",
                "UserId": "AIDA1234567890123459",
                "Arn": "arn:aws:iam::123456789012:user/audit.user",
                "CreateDate": now,
            }
        ],
        "IsTruncated": False,
    })
    stubber.add_response("list_groups_for_user", {"Groups": [], "IsTruncated": False}, {"UserName": "audit.user"})
    stubber.add_response("list_mfa_devices", {"MFADevices": [], "IsTruncated": False}, {"UserName": "audit.user"})
    stubber.add_response("list_access_keys", {"AccessKeyMetadata": [], "IsTruncated": False}, {"UserName": "audit.user"})
    stubber.add_response("list_user_policies", {"PolicyNames": [], "IsTruncated": False}, {"UserName": "audit.user"})
    stubber.add_response("list_attached_user_policies", {"AttachedPolicies": [], "IsTruncated": False}, {"UserName": "audit.user"})

    stubber.add_response("list_roles", {
        "Roles": [
            {
                "Path": "/",
                "RoleName": "AuditRole",
                "RoleId": "AROA1234567890123459",
                "Arn": "arn:aws:iam::123456789012:role/AuditRole",
                "CreateDate": now,
                "AssumeRolePolicyDocument": json.dumps({"Version": "2012-10-17", "Statement": []}),
            }
        ],
        "IsTruncated": False,
    })
    # get_roles consulta internamente list_users para calcular el desfase de IDs deterministas
    stubber.add_response("list_users", {
        "Users": [
            {
                "Path": "/",
                "UserName": "patricia.devops",
                "UserId": "AIDA1234567890123456",
                "Arn": "arn:aws:iam::123456789012:user/patricia.devops",
                "CreateDate": now - timedelta(days=60),
            }
        ],
        "IsTruncated": False,
    })
    stubber.add_response("list_role_policies", {"PolicyNames": [], "IsTruncated": False}, {"RoleName": "AuditRole"})
    stubber.add_response("list_attached_role_policies", {"AttachedPolicies": [], "IsTruncated": False}, {"RoleName": "AuditRole"})

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    resources = ds.get_resources()
    stubber.assert_no_pending_responses()

    assert len(resources) == 2


# =============================================================================
# 5. COMPATIBILIDAD INTEGRAL CON EL MOTOR Y LAS CUATRO REGLAS ISO/IEC 27001
# =============================================================================

def test_stubber_resources_evaluated_by_all_four_rules(iam_stubber):
    """21. Comprueba que los recursos recolectados vía Stubber se evalúen con las cuatro reglas de auditoría."""
    client, stubber = iam_stubber
    now = datetime.now(timezone.utc)

    user_policy_doc = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::audit-bucket/*"}],
    })
    role_trust_doc = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::123456789012:root"}, "Action": "sts:AssumeRole"}],
    })

    # Usuario con actividad reciente, MFA y política restringida
    stubber.add_response("list_users", {
        "Users": [
            {
                "Path": "/",
                "UserName": "patricia.devops",
                "UserId": "AIDA1234567890123456",
                "Arn": "arn:aws:iam::123456789012:user/patricia.devops",
                "CreateDate": now - timedelta(days=60),
                "PasswordLastUsed": now - timedelta(days=5),
            }
        ],
        "IsTruncated": False,
    })
    stubber.add_response("list_groups_for_user", {"Groups": [{"Path": "/", "GroupName": "DevOpsTeam", "GroupId": "AGPA1234567890123456", "Arn": "arn:aws:iam::123456789012:group/DevOpsTeam", "CreateDate": now}], "IsTruncated": False}, {"UserName": "patricia.devops"})
    stubber.add_response("list_mfa_devices", {"MFADevices": [{"UserName": "patricia.devops", "SerialNumber": "arn:aws:iam::123456789012:mfa/patricia.devops", "EnableDate": now}], "IsTruncated": False}, {"UserName": "patricia.devops"})
    stubber.add_response("list_access_keys", {"AccessKeyMetadata": [], "IsTruncated": False}, {"UserName": "patricia.devops"})
    stubber.add_response("list_user_policies", {"PolicyNames": ["DirectInline"], "IsTruncated": False}, {"UserName": "patricia.devops"})
    stubber.add_response("get_user_policy", {"UserName": "patricia.devops", "PolicyName": "DirectInline", "PolicyDocument": user_policy_doc}, {"UserName": "patricia.devops", "PolicyName": "DirectInline"})
    stubber.add_response("list_attached_user_policies", {"AttachedPolicies": [], "IsTruncated": False}, {"UserName": "patricia.devops"})
    stubber.add_response("list_attached_group_policies", {"AttachedPolicies": [], "IsTruncated": False}, {"GroupName": "DevOpsTeam"})
    stubber.add_response("list_group_policies", {"PolicyNames": [], "IsTruncated": False}, {"GroupName": "DevOpsTeam"})

    # Rol
    stubber.add_response("list_roles", {
        "Roles": [
            {
                "Path": "/",
                "RoleName": "RolServidorApp",
                "RoleId": "AROA1234567890123456",
                "Arn": "arn:aws:iam::123456789012:role/RolServidorApp",
                "CreateDate": now - timedelta(days=30),
                "AssumeRolePolicyDocument": role_trust_doc,
                "RoleLastUsed": {"LastUsedDate": now - timedelta(days=1)},
            }
        ],
        "IsTruncated": False,
    })
    # get_roles consulta internamente list_users para calcular el desfase de IDs deterministas
    stubber.add_response("list_users", {
        "Users": [
            {
                "Path": "/",
                "UserName": "patricia.devops",
                "UserId": "AIDA1234567890123456",
                "Arn": "arn:aws:iam::123456789012:user/patricia.devops",
                "CreateDate": now - timedelta(days=60),
            }
        ],
        "IsTruncated": False,
    })
    stubber.add_response("list_role_policies", {"PolicyNames": [], "IsTruncated": False}, {"RoleName": "RolServidorApp"})
    stubber.add_response("list_attached_role_policies", {"AttachedPolicies": [], "IsTruncated": False}, {"RoleName": "RolServidorApp"})

    stubber.activate()
    ds = AWSIAMDataSource(client=client)
    resources = ds.get_resources()
    stubber.assert_no_pending_responses()

    # Contexto de referencia con perfiles autorizados asociados por resource_key
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
            "RolServidorApp": 2,
        },
    )

    engine = AuditEngine()
    results = engine.evaluate_all(resources=resources, context=context)

    rules_present = {r.rule_code for r in results}
    assert "IAM-001" in rules_present
    assert "IAM-002" in rules_present
    assert "IAM-003" in rules_present
    assert "IAM-004" in rules_present

    # IAM-001: Usuario conforme con su perfil y rol conforme con su confianza
    user_c15_01 = next(r for r in results if r.resource_id == resources[0]["id"] and r.criterion_code == "C15-01")
    assert user_c15_01.result_status == "Conforme"

    role_c15_02 = next(r for r in results if r.resource_id == resources[1]["id"] and r.criterion_code == "C15-02")
    assert role_c15_02.result_status == "Conforme"

    # IAM-002: Actividad reciente (5 días <= 90 días) -> Conforme
    user_c16_02 = next(r for r in results if r.resource_id == resources[0]["id"] and r.criterion_code == "C16-02")
    assert user_c16_02.result_status == "Conforme"

    # IAM-003: Sin comodines -> Conforme
    user_c18_01 = next(r for r in results if r.resource_id == resources[0]["id"] and r.criterion_code == "C18-01")
    assert user_c18_01.result_status == "Conforme"

    # IAM-004: MFA activo en usuario -> Conforme; Rol excluido
    user_c85_01 = next(r for r in results if r.resource_id == resources[0]["id"] and r.criterion_code == "C85-01")
    assert user_c85_01.result_status == "Conforme"
    assert not any(r.resource_id == resources[1]["id"] and r.rule_code == "IAM-004" for r in results)


def test_stubber_preserves_simulator_integrity():
    """22. Comprueba que la integración del adaptador AWS no altere en absoluto el dataset determinista del simulador."""
    resources = IAMSimulatorDataSource.get_resources()
    context = IAMSimulatorDataSource.get_audit_context()
    engine = AuditEngine()

    results = engine.evaluate_all(resources=resources, context=context)
    assert len(resources) == 10
    assert len(results) == 67

    statuses = {r.result_status for r in results}
    assert "Conforme" in statuses
    assert "Hallazgo" in statuses
    assert "No evaluable" in statuses
