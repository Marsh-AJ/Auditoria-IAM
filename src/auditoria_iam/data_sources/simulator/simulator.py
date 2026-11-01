"""
Simulador de Datos para el Sistema de Auditoría IAM.
Proporciona escenarios representativos para evaluar identidades y recursos frente a los
controles ISO/IEC 27001:2022 sin depender de AWS IAM ni de MySQL Server.
"""
from typing import Any, Dict, List

from src.auditoria_iam.audit.models import AuditContext


def get_simulated_audit_context() -> AuditContext:
    """
    Construye y retorna el contexto de perfiles de acceso de referencia simulados.
    Incluye perfiles para usuarios operativos, administradores y roles de servicio.
    """
    profiles = {
        1: {
            "id": 1,
            "profile_code": "PRF-USR-OPERACIONES",
            "profile_name": "Perfil Estándar de Operaciones",
            "identity_type": "user",
            "version": "1.0",
            "status": "active"
        },
        2: {
            "id": 2,
            "profile_code": "PRF-USR-SOPORTE",
            "profile_name": "Perfil de Soporte Técnico",
            "identity_type": "user",
            "version": "1.0",
            "status": "active"
        },
        3: {
            "id": 3,
            "profile_code": "PRF-ROL-EC2-OPS",
            "profile_name": "Perfil de Confianza Rol EC2 Operaciones",
            "identity_type": "role",
            "version": "1.0",
            "status": "active"
        }
    }

    expected_groups = {
        1: ["Operaciones", "LecturaContratos"],
        2: ["SoporteTI"]
    }

    expected_trust_principals = {
        3: [
            {
                "principal_type": "service",
                "principal_identifier": "ec2.amazonaws.com",
                "trust_action": "sts:AssumeRole"
            }
        ]
    }

    resource_profiles = {
        1: 1,  # ana.operaciones -> PRF-USR-OPERACIONES (user)
        2: 2,  # carlos.soporte -> PRF-USR-SOPORTE (user)
        3: 1,  # usuario.inactivo -> PRF-USR-OPERACIONES (user)
        4: 1,  # cuenta.sin_mfa -> PRF-USR-OPERACIONES (user)
        # 5: Sin perfil asignado (usuario.sin_perfil)
        6: 1,  # usuario.grupos_discrepantes -> PRF-USR-OPERACIONES (user)
        7: 3,  # rol.operaciones_valido -> PRF-ROL-EC2-OPS (role)
        8: 3,  # rol.principal_no_autorizado -> PRF-ROL-EC2-OPS (role)
        9: 3,  # rol.politica_no_soportada -> PRF-ROL-EC2-OPS (role)
        10: 1  # usuario.datos_incompletos -> PRF-USR-OPERACIONES (user)
    }

    return AuditContext(
        profiles=profiles,
        expected_groups=expected_groups,
        expected_trust_principals=expected_trust_principals,
        resource_profiles=resource_profiles
    )


def get_simulated_resources() -> List[Dict[str, Any]]:
    """
    Retorna la colección de diez identidades y recursos simulados para pruebas técnicas.
    Cubre escenarios conformes, con discrepancias (hallazgos) y no evaluables.
    """
    return [
        # 1. ana.operaciones: Conforme en C15-01, C15-03, C16-01, C16-02, C18-01 y C85-01. C18-02 es No evaluable.
        {
            "id": 1,
            "resource_key": "ana.operaciones",
            "resource_type": "IAM_USER",
            "display_name": "Ana Morales (Operaciones)",
            "source_type": "simulacion",
            "resource_status": "active",
            "attributes": {
                "groups": ["Operaciones", "LecturaContratos"],
                "last_access_days": 2,
                "mfa_enabled": True,
                "policies": [
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": ["s3:GetObject", "s3:ListBucket"],
                                "Resource": "arn:aws:s3:::upharven-operaciones/*"
                            }
                        ]
                    }
                ]
            }
        },

        # 2. carlos.soporte: Hallazgo en IAM-001 (grupo adicional SeguridadTI) e IAM-003 (permisos irrestrictos */*)
        {
            "id": 2,
            "resource_key": "carlos.soporte",
            "resource_type": "IAM_USER",
            "display_name": "Carlos Rodríguez (Soporte Técnico)",
            "source_type": "simulacion",
            "resource_status": "active",
            "attributes": {
                "groups": ["SoporteTI", "SeguridadTI"],
                "last_access_days": 1,
                "mfa_enabled": True,
                "policies": [
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": "*",
                                "Resource": "*"
                            }
                        ]
                    }
                ]
            }
        },

        # 3. usuario.inactivo: No evaluable en C16-01 (estado inactivo sin metadatos de ciclo de vida) y Hallazgo en C16-02 (>90 días de inactividad)
        {
            "id": 3,
            "resource_key": "usuario.inactivo",
            "resource_type": "IAM_USER",
            "display_name": "Cuenta Inactiva Temporal",
            "source_type": "simulacion",
            "resource_status": "inactive",
            "attributes": {
                "groups": ["Operaciones", "LecturaContratos"],
                "last_access_days": 120,
                "mfa_enabled": True,
                "policies": []
            }
        },

        # 4. cuenta.sin_mfa: Hallazgo en IAM-004 (MFA deshabilitado)
        {
            "id": 4,
            "resource_key": "cuenta.sin_mfa",
            "resource_type": "IAM_USER",
            "display_name": "Usuario Operativo Sin MFA",
            "source_type": "simulacion",
            "resource_status": "active",
            "attributes": {
                "groups": ["Operaciones", "LecturaContratos"],
                "last_access_days": 5,
                "mfa_enabled": False,
                "policies": []
            }
        },

        # 5. usuario.sin_perfil: No evaluable en criterios que dependen de perfil de referencia (C15-01, C15-03, C18-02)
        {
            "id": 5,
            "resource_key": "usuario.sin_perfil",
            "resource_type": "IAM_USER",
            "display_name": "Usuario Externo Sin Perfil Asignado",
            "source_type": "simulacion",
            "resource_status": "active",
            "attributes": {
                "groups": ["Operaciones"],
                "last_access_days": 15,
                "mfa_enabled": True,
                "policies": []
            }
        },

        # 6. usuario.grupos_discrepantes: Hallazgo en IAM-001 (grupos faltantes y grupos adicionales)
        {
            "id": 6,
            "resource_key": "usuario.grupos_discrepantes",
            "resource_type": "IAM_USER",
            "display_name": "Usuario con Asignación Errónea",
            "source_type": "simulacion",
            "resource_status": "active",
            "attributes": {
                "groups": ["Finanzas", "AuditoriaInterna"],
                "last_access_days": 10,
                "mfa_enabled": True,
                "policies": []
            }
        },

        # 7. rol.operaciones_valido: Rol IAM Conforme en IAM-001 (principal ec2.amazonaws.com y acción sts:AssumeRole)
        {
            "id": 7,
            "resource_key": "rol.operaciones_valido",
            "resource_type": "IAM_ROLE",
            "display_name": "Rol de Aplicación EC2 Operaciones",
            "source_type": "simulacion",
            "resource_status": "active",
            "attributes": {
                "assume_role_policy_document": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "ec2.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                },
                "last_access_days": 3,
                "policies": [
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": ["s3:GetObject"],
                                "Resource": "arn:aws:s3:::upharven-datos/*"
                            }
                        ]
                    }
                ]
            }
        },

        # 8. rol.principal_no_autorizado: Hallazgo en IAM-001 (entidad lambda.amazonaws.com no autorizada en perfil)
        {
            "id": 8,
            "resource_key": "rol.principal_no_autorizado",
            "resource_type": "IAM_ROLE",
            "display_name": "Rol con Confianza No Autorizada",
            "source_type": "simulacion",
            "resource_status": "active",
            "attributes": {
                "assume_role_policy_document": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                },
                "last_access_days": 10,
                "policies": []
            }
        },

        # 9. rol.politica_no_soportada: No evaluable en IAM-001 (C15-02) por condición de autorización compleja
        {
            "id": 9,
            "resource_key": "rol.politica_no_soportada",
            "resource_type": "IAM_ROLE",
            "display_name": "Rol con Política Compleja No Determinista",
            "source_type": "simulacion",
            "resource_status": "active",
            "attributes": {
                "assume_role_policy_document": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "ec2.amazonaws.com"},
                            "Action": "sts:AssumeRole",
                            "Condition": {
                                "StringLike": {"aws:PrincipalTag/Department": "Fin*"}
                            }
                        }
                    ]
                },
                "last_access_days": 20,
                "policies": []
            }
        },

        # 10. usuario.datos_incompletos: No evaluable en criterios que requieren metadatos técnicos
        {
            "id": 10,
            "resource_key": "usuario.datos_incompletos",
            "resource_type": "IAM_USER",
            "display_name": "Usuario con Metadatos Parciales",
            "source_type": "simulacion",
            "resource_status": "",
            "attributes": {}
        }
    ]


def get_simulated_users() -> List[Dict[str, Any]]:
    """
    Retorna exclusivamente los recursos simulados de tipo usuario IAM (IAM_USER).
    """
    return [r for r in get_simulated_resources() if r.get("resource_type") == "IAM_USER"]


def get_simulated_roles() -> List[Dict[str, Any]]:
    """
    Retorna exclusivamente los recursos simulados de tipo rol IAM (IAM_ROLE).
    """
    return [r for r in get_simulated_resources() if r.get("resource_type") == "IAM_ROLE"]


def get_simulated_groups() -> List[Dict[str, Any]]:
    """
    Retorna el catálogo consolidado de grupos IAM simulados, sus identificadores,
    descripciones funcionales y usuarios miembros asignados en el dataset de simulación.
    """
    resources = get_simulated_resources()
    group_definitions = [
        {
            "group_name": "Operaciones",
            "arn": "arn:aws:iam::123456789012:group/Operaciones",
            "description": "Personal operativo de gestión de contratos y operaciones generales"
        },
        {
            "group_name": "LecturaContratos",
            "arn": "arn:aws:iam::123456789012:group/LecturaContratos",
            "description": "Acceso de lectura a documentación operativa y contratos"
        },
        {
            "group_name": "SoporteTI",
            "arn": "arn:aws:iam::123456789012:group/SoporteTI",
            "description": "Personal técnico encargado del soporte de infraestructura"
        },
        {
            "group_name": "SeguridadTI",
            "arn": "arn:aws:iam::123456789012:group/SeguridadTI",
            "description": "Equipo de seguridad de la información y monitoreo"
        },
        {
            "group_name": "Finanzas",
            "arn": "arn:aws:iam::123456789012:group/Finanzas",
            "description": "Personal del departamento financiero y facturación"
        },
        {
            "group_name": "AuditoriaInterna",
            "arn": "arn:aws:iam::123456789012:group/AuditoriaInterna",
            "description": "Equipo de auditoría interna y verificación de cumplimiento"
        }
    ]

    # Calcular membresías de forma determinista desde los recursos
    groups_catalog = []
    for gdef in group_definitions:
        gname = gdef["group_name"]
        members = [
            r["resource_key"]
            for r in resources
            if r.get("resource_type") == "IAM_USER"
            and isinstance(r.get("attributes"), dict)
            and gname in r["attributes"].get("groups", [])
        ]
        groups_catalog.append({
            "group_name": gname,
            "arn": gdef["arn"],
            "description": gdef["description"],
            "members": members
        })

    return groups_catalog


def get_simulated_policies() -> List[Dict[str, Any]]:
    """
    Retorna el catálogo consolidado de políticas IAM definidas en el conjunto simulado,
    incluyendo políticas en línea de identidades y roles de servicio.
    """
    return [
        {
            "policy_name": "UpharvenOperacionesS3Policy",
            "policy_type": "inline",
            "attached_to": "ana.operaciones",
            "policy_document": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["s3:GetObject", "s3:ListBucket"],
                        "Resource": "arn:aws:s3:::upharven-operaciones/*"
                    }
                ]
            }
        },
        {
            "policy_name": "AdministratorAccessSimulated",
            "policy_type": "inline",
            "attached_to": "carlos.soporte",
            "policy_document": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": "*",
                        "Resource": "*"
                    }
                ]
            }
        },
        {
            "policy_name": "UpharvenEC2S3ReadPolicy",
            "policy_type": "inline",
            "attached_to": "rol.operaciones_valido",
            "policy_document": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["s3:GetObject"],
                        "Resource": "arn:aws:s3:::upharven-datos/*"
                    }
                ]
            }
        }
    ]


def get_simulated_profiles() -> Dict[int, Dict[str, Any]]:
    """
    Retorna el catálogo de perfiles de acceso autorizados de referencia,
    enriquecido con sus grupos esperados y relaciones de confianza correspondientes.
    """
    context = get_simulated_audit_context()
    profiles_catalog = {}

    for pid, profile in context.profiles.items():
        enriched = dict(profile)
        enriched["expected_groups"] = list(context.expected_groups.get(pid, []))
        enriched["expected_trust_principals"] = list(context.expected_trust_principals.get(pid, []))
        profiles_catalog[pid] = enriched

    return profiles_catalog


def validate_simulated_data_integrity() -> Dict[str, Any]:
    """
    Ejecuta una validación integral de integridad técnica y referencial sobre el dataset simulado:
    - Verifica esquema estructural y obligatoriedad de campos.
    - Comprueba consistencia referencial de grupos asignados vs. catálogo de grupos.
    - Comprueba consistencia referencial de perfiles asociados vs. catálogo de perfiles.
    - Identifica y clasifica identidades válidas y recursos intencionalmente degradados (casos negativos).

    Retorna un reporte estructurado con el estado de validación y métricas de consistencia.
    """
    resources = get_simulated_resources()
    context = get_simulated_audit_context()
    groups_catalog = get_simulated_groups()
    known_group_names = {g["group_name"] for g in groups_catalog}

    issues: List[str] = []
    seen_keys = set()
    users_count = 0
    roles_count = 0
    degraded_resources: List[Dict[str, str]] = []

    required_keys = {"id", "resource_key", "resource_type", "display_name", "source_type", "resource_status", "attributes"}

    for res in resources:
        # Validación de claves del diccionario base
        missing = required_keys - set(res.keys())
        if missing:
            issues.append(f"Recurso ID {res.get('id')} carece de claves obligatorias: {missing}")

        rkey = res.get("resource_key")
        if not rkey:
            issues.append(f"Recurso ID {res.get('id')} no posee resource_key válido.")
        elif rkey in seen_keys:
            issues.append(f"resource_key duplicado detectado: {rkey}")
        else:
            seen_keys.add(rkey)

        rtype = res.get("resource_type")
        if rtype == "IAM_USER":
            users_count += 1
            # Validar consistencia de grupos asignados
            attrs = res.get("attributes", {})
            if isinstance(attrs, dict):
                user_groups = attrs.get("groups", [])
                if isinstance(user_groups, list):
                    for g in user_groups:
                        if g not in known_group_names:
                            issues.append(f"Usuario {rkey} referencia grupo desconocido: '{g}'")
        elif rtype == "IAM_ROLE":
            roles_count += 1
        else:
            issues.append(f"Recurso {rkey} tiene resource_type no reconocido: {rtype}")

        # Identificar casos intencionalmente diseñados para pruebas de frontera / casos negativos
        rid = res.get("id")
        if rid == 5:
            degraded_resources.append({"resource_key": rkey, "reason": "Sin perfil de referencia asignado en contexto"})
        elif rid == 10:
            degraded_resources.append({"resource_key": rkey, "reason": "Atributos y estado vacíos (metadatos parciales)"})
        elif rid == 9:
            degraded_resources.append({"resource_key": rkey, "reason": "Política de confianza con condición no determinista"})
        elif rid == 3:
            degraded_resources.append({"resource_key": rkey, "reason": "Estado inactivo con inactividad superior a 90 días"})
        elif rid == 4:
            degraded_resources.append({"resource_key": rkey, "reason": "MFA deshabilitado"})
        elif rid == 2:
            degraded_resources.append({"resource_key": rkey, "reason": "Permisos irrestrictos (*/*) y grupo fuera de perfil"})
        elif rid == 6:
            degraded_resources.append({"resource_key": rkey, "reason": "Grupos asignados discrepantes con perfil de referencia"})
        elif rid == 8:
            degraded_resources.append({"resource_key": rkey, "reason": "Rol con entidad de confianza no autorizada"})

    # Validar consistencia referencial de perfiles en el contexto
    for rid, pid in context.resource_profiles.items():
        if pid not in context.profiles:
            issues.append(f"Contexto referencia perfil inexistente ID {pid} para el recurso {rid}")

    is_valid = len(issues) == 0

    return {
        "valid": is_valid,
        "total_resources": len(resources),
        "users_count": users_count,
        "roles_count": roles_count,
        "groups_count": len(groups_catalog),
        "profiles_count": len(context.profiles),
        "policies_count": len(get_simulated_policies()),
        "degraded_resources_count": len(degraded_resources),
        "degraded_resources": degraded_resources,
        "issues": issues
    }


class IAMSimulatorDataSource:
    """
    Fuente de datos simulada para auditoría IAM ISO/IEC 27001:2022.
    Encapsula el acceso desacoplado al catálogo simulado de identidades,
    roles, grupos, políticas, perfiles de referencia y verificación de integridad.
    """

    @staticmethod
    def get_resources() -> List[Dict[str, Any]]:
        """Retorna todos los recursos simulados normalizados."""
        return get_simulated_resources()

    @staticmethod
    def get_audit_context() -> AuditContext:
        """Retorna el contexto de perfiles y reglas de referencia."""
        return get_simulated_audit_context()

    @staticmethod
    def get_users() -> List[Dict[str, Any]]:
        """Retorna exclusivamente los usuarios IAM simulados."""
        return get_simulated_users()

    @staticmethod
    def get_roles() -> List[Dict[str, Any]]:
        """Retorna exclusivamente los roles IAM simulados."""
        return get_simulated_roles()

    @staticmethod
    def get_groups() -> List[Dict[str, Any]]:
        """Retorna el catálogo consolidado de grupos IAM simulados y membresías."""
        return get_simulated_groups()

    @staticmethod
    def get_policies() -> List[Dict[str, Any]]:
        """Retorna las políticas técnicas simuladas."""
        return get_simulated_policies()

    @staticmethod
    def get_profiles() -> Dict[int, Dict[str, Any]]:
        """Retorna los perfiles autorizados de referencia enriquecidos."""
        return get_simulated_profiles()

    @staticmethod
    def validate_integrity() -> Dict[str, Any]:
        """Ejecuta la validación de integridad referencial y de esquema del dataset."""
        return validate_simulated_data_integrity()
