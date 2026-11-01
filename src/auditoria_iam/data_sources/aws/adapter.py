"""
Adaptador de Datos AWS IAM mediante Boto3.
Permite consultar identidades, grupos, roles, políticas, confianza y MFA en AWS IAM
utilizando exclusivamente operaciones de lectura y normalizando la información
al formato requerido por el motor de auditoría ISO/IEC 27001.
"""
from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional, Set
import urllib.parse

import boto3
import botocore.exceptions

from src.auditoria_iam.data_sources.aws.exceptions import (
    AWSIAMAuthenticationError,
    AWSIAMConnectionError,
    AWSIAMDataSourceError,
    AWSIAMPermissionError,
)

logger = logging.getLogger(__name__)

# Catálogo estricto de operaciones de lectura permitidas (Principio de mínimo privilegio y solo lectura)
READ_ONLY_OPERATIONS: Set[str] = {
    "list_users",
    "get_user",
    "list_groups",
    "get_group",
    "list_groups_for_user",
    "list_roles",
    "get_role",
    "list_mfa_devices",
    "list_access_keys",
    "get_access_key_last_used",
    "list_attached_user_policies",
    "list_user_policies",
    "get_user_policy",
    "list_attached_group_policies",
    "list_group_policies",
    "get_group_policy",
    "list_attached_role_policies",
    "list_role_policies",
    "get_role_policy",
    "get_policy",
    "get_policy_version",
}

FORBIDDEN_OPERATION_PREFIXES = (
    "create",
    "update",
    "delete",
    "put",
    "attach",
    "detach",
    "enable",
    "disable",
    "deactivate",
    "generate",
    "remove",
    "add",
    "tag",
    "untag",
)


class AWSIAMDataSource:
    """
    Fuente de datos de nube para auditoría IAM.
    Consulta identidades y configuraciones de AWS IAM mediante operaciones seguras de solo lectura
    y las normaliza al esquema de evaluación compatible con AuditEngine.
    """

    def __init__(
        self,
        session: Optional[boto3.Session] = None,
        client: Optional[Any] = None,
        id_offset: int = 1000,
        include_service_linked_roles: bool = False,
    ) -> None:
        """
        Inicializa el adaptador. Permite inyección de cliente (para mocks/pruebas)
        o sesión personalizada. Por defecto usa la cadena estándar de credenciales de AWS.
        """
        self.id_offset = id_offset
        self.include_service_linked_roles = include_service_linked_roles
        self._policy_doc_cache: Dict[str, Dict[str, Any]] = {}
        self._group_members_cache: Dict[str, List[str]] = {}
        self._group_policies_cache: Dict[str, List[Dict[str, Any]]] = {}

        if client is not None:
            self._client = client
        elif session is not None:
            self._client = session.client("iam")
        else:
            try:
                self._client = boto3.client("iam")
            except Exception as e:
                self._handle_exception(e, "inicialización del cliente AWS IAM")

    @property
    def client(self) -> Any:
        return self._client

    def _validate_safe_operation(self, operation_name: str) -> None:
        """Verifica que la operación solicitada sea estrictamente de solo lectura."""
        op_lower = operation_name.lower()
        for prefix in FORBIDDEN_OPERATION_PREFIXES:
            if op_lower.startswith(prefix):
                raise AWSIAMDataSourceError(
                    f"Operación de escritura rechazada por seguridad: '{operation_name}'."
                )

        if op_lower not in READ_ONLY_OPERATIONS:
            raise AWSIAMDataSourceError(
                f"Operación no autorizada: '{operation_name}'. Solo se permiten operaciones de consulta."
            )

    def _handle_exception(self, exc: Exception, context_action: str) -> None:
        """
        Traduce excepciones de botocore/boto3 a excepciones controladas del dominio,
        asegurando que no se expongan credenciales, tokens ni datos sensibles.
        """
        if isinstance(exc, (AWSIAMAuthenticationError, AWSIAMPermissionError, AWSIAMConnectionError, AWSIAMDataSourceError)):
            raise exc

        if isinstance(exc, botocore.exceptions.NoCredentialsError):
            raise AWSIAMAuthenticationError(
                "No se encontraron credenciales de AWS configuradas en el entorno."
            ) from None

        if isinstance(exc, botocore.exceptions.PartialCredentialsError):
            raise AWSIAMAuthenticationError(
                "Configuración de credenciales de AWS incompleta."
            ) from None

        if isinstance(exc, botocore.exceptions.EndpointConnectionError):
            raise AWSIAMConnectionError(
                "No fue posible establecer conexión con el endpoint de AWS IAM."
            ) from None

        if isinstance(exc, botocore.exceptions.ClientError):
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in ("AuthFailure", "InvalidClientTokenId", "SignatureDoesNotMatch", "ExpiredToken"):
                raise AWSIAMAuthenticationError(
                    "Fallo de autenticación en AWS IAM: credenciales o token inválidos."
                ) from None
            if error_code in ("AccessDenied", "AccessDeniedException", "UnauthorizedOperation"):
                raise AWSIAMPermissionError(
                    f"Permisos insuficientes para ejecutar la consulta de lectura en AWS IAM ({context_action})."
                ) from None
            if error_code == "NoSuchEntity":
                logger.debug("Entidad no encontrada durante consulta (%s): %s", context_action, error_code)
                return

            raise AWSIAMDataSourceError(
                f"Error al consultar AWS IAM ({context_action}): código de servicio '{error_code}'."
            ) from None

        # Excepción genérica no controlada
        raise AWSIAMDataSourceError(
            f"Error inesperado al consultar AWS IAM durante '{context_action}'."
        ) from None

    def _call_iam_operation(self, operation_name: str, **kwargs) -> Any:
        """Ejecuta una operación sobre el cliente IAM con validación de solo lectura y control de errores."""
        self._validate_safe_operation(operation_name)
        try:
            method = getattr(self._client, operation_name)
            return method(**kwargs)
        except Exception as exc:
            self._handle_exception(exc, operation_name)
            return {}

    def _paginate_or_call(self, operation_name: str, result_key: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Consulta elementos aplicando paginación Boto3 si está disponible,
        o iteración manual por Marker/NextToken en su defecto.
        """
        self._validate_safe_operation(operation_name)
        items: List[Dict[str, Any]] = []

        # Intentar paginador oficial si el cliente lo implementa
        has_paginator = hasattr(self._client, "get_paginator") and hasattr(self._client, "can_paginate")
        if has_paginator and self._client.can_paginate(operation_name):
            try:
                paginator = self._client.get_paginator(operation_name)
                for page in paginator.paginate(**kwargs):
                    page_items = page.get(result_key, [])
                    if isinstance(page_items, list):
                        items.extend(page_items)
                return items
            except Exception as exc:
                self._handle_exception(exc, f"paginación de {operation_name}")
                return []

        # Fallback a llamada directa con control de truncamiento
        current_kwargs = dict(kwargs)
        while True:
            response = self._call_iam_operation(operation_name, **current_kwargs)
            if not response or not isinstance(response, dict):
                break

            page_items = response.get(result_key, [])
            if isinstance(page_items, list):
                items.extend(page_items)

            is_truncated = response.get("IsTruncated", False)
            marker = response.get("Marker")
            if is_truncated and marker:
                current_kwargs["Marker"] = marker
            else:
                break

        return items

    def _normalize_policy_document(self, raw_document: Any) -> Optional[Dict[str, Any]]:
        """
        Normaliza el documento de política a un diccionario Python con sintaxis JSON válida.
        Maneja documentos ya parseados, cadenas JSON y cadenas con codificación URL.
        """
        if isinstance(raw_document, dict):
            return raw_document

        if isinstance(raw_document, str):
            doc_str = raw_document.strip()
            # Si contiene codificación URL (común en respuestas de IAM get_user_policy/get_role_policy)
            if "%" in doc_str:
                try:
                    unquoted = urllib.parse.unquote(doc_str)
                    parsed = json.loads(unquoted)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    pass

            try:
                parsed = json.loads(doc_str)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass

        return None

    def _get_managed_policy_document(self, policy_arn: str) -> Optional[Dict[str, Any]]:
        """Obtiene y normaliza el documento de versión predeterminada de una política administrada."""
        if policy_arn in self._policy_doc_cache:
            return self._policy_doc_cache[policy_arn]

        policy_meta = self._call_iam_operation("get_policy", PolicyArn=policy_arn)
        if not policy_meta or not isinstance(policy_meta, dict):
            return None

        default_version = policy_meta.get("Policy", {}).get("DefaultVersionId")
        if not default_version:
            return None

        version_data = self._call_iam_operation(
            "get_policy_version",
            PolicyArn=policy_arn,
            VersionId=default_version
        )
        if not version_data or not isinstance(version_data, dict):
            return None

        raw_doc = version_data.get("PolicyVersion", {}).get("Document")
        normalized = self._normalize_policy_document(raw_doc)
        if normalized:
            self._policy_doc_cache[policy_arn] = normalized
        return normalized

    def _create_incomplete_policy_marker(
        self,
        source_type: str,
        source_name: Optional[str] = None,
        source_arn: Optional[str] = None,
        group_name: Optional[str] = None,
        error_reason: str = "Documento de política no disponible o no normalizable",
    ) -> Dict[str, Any]:
        """
        Crea un marcador de política incompleta compatible con el analizador de IAM-003.
        Contiene 'Statement': None para inducir un resultado 'No evaluable' en C18-01,
        impidiendo omitir silenciosamente políticas asignadas o falsear resultados Conforme.
        """
        marker: Dict[str, Any] = {
            "_source_type": source_type,
            "_incomplete_policy": True,
            "_error": error_reason,
            "Statement": None
        }
        if source_name:
            marker["_source_name"] = source_name
        if source_arn:
            marker["_source_arn"] = source_arn
        if group_name:
            marker["_group_name"] = group_name
        return marker

    def _get_group_policies(self, group_name: str, raise_on_error: bool = False) -> List[Dict[str, Any]]:
        """
        Obtiene todas las políticas en línea y administradas asociadas a un grupo IAM.
        Preserva la trazabilidad de la procedencia (grupo y nombre/ARN de política) y normaliza
        los documentos JSON para su evaluación en IAM-003. Si un documento no es recuperable,
        registra un marcador incompleto para evitar omisiones silenciosas.
        """
        if group_name in self._group_policies_cache:
            return self._group_policies_cache[group_name]

        group_policies: List[Dict[str, Any]] = []

        try:
            # 1. Políticas administradas adjuntas al grupo
            attached = self._paginate_or_call(
                "list_attached_group_policies",
                "AttachedPolicies",
                GroupName=group_name
            )
            for att in attached:
                arn = att.get("PolicyArn")
                p_name = att.get("PolicyName", arn.split("/")[-1] if arn else "Desconocida")
                if arn:
                    doc = self._get_managed_policy_document(arn)
                    if doc:
                        policy_copy = dict(doc)
                        policy_copy["_source_type"] = "group_managed"
                        policy_copy["_source_name"] = p_name
                        policy_copy["_source_arn"] = arn
                        policy_copy["_group_name"] = group_name
                        group_policies.append(policy_copy)
                    else:
                        incomplete_marker = self._create_incomplete_policy_marker(
                            source_type="group_managed",
                            source_name=p_name,
                            source_arn=arn,
                            group_name=group_name,
                            error_reason="Documento de política administrada de grupo no recuperable"
                        )
                        group_policies.append(incomplete_marker)

            # 2. Políticas integradas (inline) del grupo
            inline_names = self._paginate_or_call(
                "list_group_policies",
                "PolicyNames",
                GroupName=group_name
            )
            for p_name in inline_names:
                if isinstance(p_name, str):
                    p_resp = self._call_iam_operation("get_group_policy", GroupName=group_name, PolicyName=p_name)
                    doc = self._normalize_policy_document(p_resp.get("PolicyDocument"))
                    if doc:
                        policy_copy = dict(doc)
                        policy_copy["_source_type"] = "group_inline"
                        policy_copy["_source_name"] = p_name
                        policy_copy["_group_name"] = group_name
                        group_policies.append(policy_copy)
                    else:
                        incomplete_marker = self._create_incomplete_policy_marker(
                            source_type="group_inline",
                            source_name=p_name,
                            group_name=group_name,
                            error_reason="Documento de política integrada de grupo no recuperable o inválido"
                        )
                        group_policies.append(incomplete_marker)

            self._group_policies_cache[group_name] = group_policies
            return group_policies

        except (AWSIAMPermissionError, AWSIAMDataSourceError) as exc:
            if raise_on_error:
                raise
            logger.warning(
                "No fue posible consultar las políticas del grupo '%s' debido a limitaciones o permisos: %s",
                group_name,
                exc
            )
            incomplete_marker = self._create_incomplete_policy_marker(
                source_type="group",
                group_name=group_name,
                error_reason=str(exc)
            )
            group_policies.append(incomplete_marker)
            return group_policies

    def _get_user_policies(self, username: str, user_groups: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todas las políticas en línea y administradas adjuntas directamente a un usuario,
        así como las políticas heredadas a través de los grupos IAM a los que pertenece,
        preservando la trazabilidad de su procedencia y evitando duplicaciones. Si una política no
        puede recuperarse o normalizarse, genera un marcador incompleto.
        """
        policies: List[Dict[str, Any]] = []
        seen_managed_arns: Set[str] = set()

        # 1. Políticas integradas (inline) directas del usuario
        inline_policy_names = self._paginate_or_call(
            "list_user_policies",
            "PolicyNames",
            UserName=username
        )
        for p_name in inline_policy_names:
            if isinstance(p_name, str):
                p_resp = self._call_iam_operation("get_user_policy", UserName=username, PolicyName=p_name)
                doc = self._normalize_policy_document(p_resp.get("PolicyDocument"))
                if doc:
                    policy_copy = dict(doc)
                    policy_copy["_source_type"] = "user_inline"
                    policy_copy["_source_name"] = p_name
                    policies.append(policy_copy)
                else:
                    incomplete_marker = self._create_incomplete_policy_marker(
                        source_type="user_inline",
                        source_name=p_name,
                        error_reason="Documento de política integrada de usuario no recuperable o inválido"
                    )
                    policies.append(incomplete_marker)

        # 2. Políticas administradas adjuntas directamente al usuario
        attached = self._paginate_or_call(
            "list_attached_user_policies",
            "AttachedPolicies",
            UserName=username
        )
        for att in attached:
            arn = att.get("PolicyArn")
            p_name = att.get("PolicyName", arn.split("/")[-1] if arn else "Desconocida")
            if arn:
                doc = self._get_managed_policy_document(arn)
                if doc:
                    policy_copy = dict(doc)
                    policy_copy["_source_type"] = "user_managed"
                    policy_copy["_source_name"] = p_name
                    policy_copy["_source_arn"] = arn
                    policies.append(policy_copy)
                    seen_managed_arns.add(arn)
                else:
                    incomplete_marker = self._create_incomplete_policy_marker(
                        source_type="user_managed",
                        source_name=p_name,
                        source_arn=arn,
                        error_reason="Documento de política administrada de usuario no recuperable"
                    )
                    policies.append(incomplete_marker)

        # 3. Políticas heredadas a través de grupos IAM
        if user_groups:
            for g_name in user_groups:
                g_policies = self._get_group_policies(g_name)
                for gp in g_policies:
                    # Evitar duplicar políticas administradas idénticas ya evaluadas
                    g_arn = gp.get("_source_arn")
                    if g_arn:
                        if g_arn in seen_managed_arns:
                            continue
                        seen_managed_arns.add(g_arn)
                    policies.append(gp)

        return policies

    def _get_role_policies(self, role_name: str) -> List[Dict[str, Any]]:
        """
        Obtiene todas las políticas en línea y administradas adjuntas a un rol.
        Si un documento no es recuperable o normalizable, genera un marcador incompleto.
        """
        policies: List[Dict[str, Any]] = []

        # 1. Políticas integradas (inline)
        inline_names = self._paginate_or_call(
            "list_role_policies",
            "PolicyNames",
            RoleName=role_name
        )
        for p_name in inline_names:
            if isinstance(p_name, str):
                p_resp = self._call_iam_operation("get_role_policy", RoleName=role_name, PolicyName=p_name)
                doc = self._normalize_policy_document(p_resp.get("PolicyDocument"))
                if doc:
                    policy_copy = dict(doc)
                    policy_copy["_source_type"] = "role_inline"
                    policy_copy["_source_name"] = p_name
                    policies.append(policy_copy)
                else:
                    incomplete_marker = self._create_incomplete_policy_marker(
                        source_type="role_inline",
                        source_name=p_name,
                        error_reason="Documento de política integrada de rol no recuperable o inválido"
                    )
                    policies.append(incomplete_marker)

        # 2. Políticas administradas adjuntas
        attached = self._paginate_or_call(
            "list_attached_role_policies",
            "AttachedPolicies",
            RoleName=role_name
        )
        for att in attached:
            arn = att.get("PolicyArn")
            p_name = att.get("PolicyName", arn.split("/")[-1] if arn else "Desconocida")
            if arn:
                doc = self._get_managed_policy_document(arn)
                if doc:
                    policy_copy = dict(doc)
                    policy_copy["_source_type"] = "role_managed"
                    policy_copy["_source_name"] = p_name
                    policy_copy["_source_arn"] = arn
                    policies.append(policy_copy)
                else:
                    incomplete_marker = self._create_incomplete_policy_marker(
                        source_type="role_managed",
                        source_name=p_name,
                        source_arn=arn,
                        error_reason="Documento de política administrada de rol no recuperable"
                    )
                    policies.append(incomplete_marker)

        return policies

    def _get_user_last_access_days(self, user_dict: Dict[str, Any], username: str) -> Optional[int]:
        """
        Determina los días de inactividad más recientes a partir de PasswordLastUsed
        o de la última utilización de cualquier Access Key activa.
        Retorna None si AWS no registra actividad alguna.
        """
        activity_dates: List[datetime] = []

        # 1. Último uso de contraseña de consola
        pwd_used = user_dict.get("PasswordLastUsed")
        if isinstance(pwd_used, datetime):
            activity_dates.append(pwd_used)

        # 2. Último uso de claves de acceso
        access_keys = self._paginate_or_call("list_access_keys", "AccessKeyMetadata", UserName=username)
        for key in access_keys:
            key_id = key.get("AccessKeyId")
            if key_id:
                usage_resp = self._call_iam_operation("get_access_key_last_used", AccessKeyId=key_id)
                last_used = usage_resp.get("AccessKeyLastUsed", {}).get("LastUsedDate")
                if isinstance(last_used, datetime):
                    activity_dates.append(last_used)

        if not activity_dates:
            return None

        # Encontrar la fecha más reciente
        most_recent = max(activity_dates)
        if most_recent.tzinfo is None:
            most_recent = most_recent.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        delta_days = (now - most_recent).total_seconds() / 86400.0
        return max(0, int(delta_days))

    def _check_user_mfa(self, username: str) -> bool:
        """Verifica si el usuario posee al menos un dispositivo MFA habilitado."""
        devices = self._paginate_or_call("list_mfa_devices", "MFADevices", UserName=username)
        return len(devices) > 0

    def _get_user_groups(self, username: str) -> List[str]:
        """Obtiene los nombres de grupos a los que pertenece el usuario."""
        groups = self._paginate_or_call("list_groups_for_user", "Groups", UserName=username)
        group_names = []
        for g in groups:
            name = g.get("GroupName")
            if name and isinstance(name, str):
                group_names.append(name)
        return group_names

    def get_users(self) -> List[Dict[str, Any]]:
        """
        Consulta todos los usuarios IAM de AWS y los normaliza al esquema uniforme
        requerido por el motor de auditoría.
        """
        raw_users = self._paginate_or_call("list_users", "Users")
        normalized_users: List[Dict[str, Any]] = []

        for idx, user in enumerate(raw_users, start=1):
            username = user.get("UserName", "")
            if not username:
                continue

            groups = self._get_user_groups(username)
            mfa_enabled = self._check_user_mfa(username)
            last_access_days = self._get_user_last_access_days(user, username)
            policies = self._get_user_policies(username, user_groups=groups)

            # Normalización uniforme
            normalized_users.append({
                "id": self.id_offset + idx,
                "resource_key": username,
                "resource_type": "IAM_USER",
                "display_name": username,
                "source_type": "aws",
                "resource_status": "active",
                "arn": user.get("Arn"),
                "attributes": {
                    "groups": groups,
                    "last_access_days": last_access_days,
                    "mfa_enabled": mfa_enabled,
                    "policies": policies
                }
            })

        return normalized_users

    def get_roles(self) -> List[Dict[str, Any]]:
        """
        Consulta los roles IAM de AWS y los normaliza al esquema uniforme
        requerido por el motor de auditoría.
        """
        raw_roles = self._paginate_or_call("list_roles", "Roles")
        normalized_roles: List[Dict[str, Any]] = []

        user_count = len(self._paginate_or_call("list_users", "Users"))
        role_start_idx = self.id_offset + user_count + 1

        for idx, role in enumerate(raw_roles, start=role_start_idx):
            role_name = role.get("RoleName", "")
            path = role.get("Path", "")

            # Excluir service-linked roles si no están expresamente solicitados
            if not self.include_service_linked_roles and "/aws-service-role/" in path:
                continue

            trust_doc = self._normalize_policy_document(role.get("AssumeRolePolicyDocument"))
            policies = self._get_role_policies(role_name)

            # Último uso del rol si está disponible en AWS
            last_used_dt = role.get("RoleLastUsed", {}).get("LastUsedDate")
            last_access_days: Optional[int] = None
            if isinstance(last_used_dt, datetime):
                if last_used_dt.tzinfo is None:
                    last_used_dt = last_used_dt.replace(tzinfo=timezone.utc)
                delta_days = (datetime.now(timezone.utc) - last_used_dt).total_seconds() / 86400.0
                last_access_days = max(0, int(delta_days))

            normalized_roles.append({
                "id": idx,
                "resource_key": role_name,
                "resource_type": "IAM_ROLE",
                "display_name": role_name,
                "source_type": "aws",
                "resource_status": "active",
                "arn": role.get("Arn"),
                "attributes": {
                    "assume_role_policy_document": trust_doc,
                    "last_access_days": last_access_days,
                    "policies": policies
                }
            })

        return normalized_roles

    def get_resources(self) -> List[Dict[str, Any]]:
        """
        Retorna la colección completa y normalizada de usuarios y roles obtenidos de AWS IAM,
        listos para ser evaluados de forma transparente por el AuditEngine.
        """
        users = self.get_users()
        roles = self.get_roles()
        return users + roles

    def get_groups(self) -> List[Dict[str, Any]]:
        """
        Consulta y retorna el catálogo de grupos IAM en AWS con sus miembros asociados.
        """
        raw_groups = self._paginate_or_call("list_groups", "Groups")
        groups_catalog: List[Dict[str, Any]] = []

        for group in raw_groups:
            g_name = group.get("GroupName", "")
            if not g_name:
                continue

            # Obtener miembros del grupo
            group_detail = self._call_iam_operation("get_group", GroupName=g_name)
            members = [
                u.get("UserName")
                for u in group_detail.get("Users", [])
                if u.get("UserName")
            ]

            groups_catalog.append({
                "group_name": g_name,
                "arn": group.get("Arn"),
                "description": group.get("Path", ""),
                "members": members,
                "policies": self._get_group_policies(g_name)
            })

        return groups_catalog

    def get_policies(self) -> List[Dict[str, Any]]:
        """
        Retorna la lista de políticas técnicas cacheadas o consultadas durante la inspección.
        """
        policies_list = []
        for arn, doc in self._policy_doc_cache.items():
            policies_list.append({
                "policy_arn": arn,
                "policy_name": arn.split("/")[-1],
                "policy_type": "managed",
                "policy_document": doc
            })
        return policies_list
