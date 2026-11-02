"""
Modelos de Datos para el Motor de Auditoría IAM.
Define la estructura uniforme para representar los resultados de evaluación,
validación de estados permitidos y contexto de perfiles de referencia.
"""
from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Optional, Set, Union

# Únicos estados permitidos conforme a la especificación de auditoría ISO/IEC 27001
VALID_STATUSES: Set[str] = {"Conforme", "Hallazgo", "No evaluable"}


@dataclass
class AuditResult:
    """
    Modelo uniforme para representar el resultado de evaluación de un criterio de auditoría.
    Garantiza la consistencia de tipos y estados en todo el motor algorítmico.
    """
    rule_code: str
    criterion_code: str
    resource_id: Optional[int | str]
    result_status: str
    justification: str
    profile_id: Optional[int | str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.rule_code:
            raise ValueError("El campo 'rule_code' es obligatorio.")
        if not self.criterion_code:
            raise ValueError("El campo 'criterion_code' es obligatorio.")
        if self.result_status not in VALID_STATUSES:
            raise ValueError(
                f"Estado de resultado inválido: '{self.result_status}'. "
                f"Los únicos estados permitidos son: {sorted(list(VALID_STATUSES))}."
            )
        if not self.justification or not self.justification.strip():
            raise ValueError("El campo 'justification' no puede estar vacío.")

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a un diccionario serializable."""
        return {
            "rule_code": self.rule_code,
            "criterion_code": self.criterion_code,
            "resource_id": self.resource_id,
            "result_status": self.result_status,
            "justification": self.justification,
            "profile_id": self.profile_id,
            "details": self.details,
            "evidence": self.evidence
        }


@dataclass
class AuditContext:
    """
    Contexto de referencia para la ejecución del motor de auditoría.
    Almacena los perfiles de acceso autorizados y sus configuraciones esperadas.
    Permite la resolución de perfiles tanto por ID numérico como por resource_key.
    """
    profiles: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    expected_groups: Dict[int, List[str]] = field(default_factory=dict)
    expected_trust_principals: Dict[int, List[Dict[str, Any]]] = field(default_factory=dict)
    resource_profiles: Dict[int, int] = field(default_factory=dict)
    resource_key_profiles: Dict[str, int] = field(default_factory=dict)

    def get_profile_for_resource(
        self,
        resource_id: Union[int, str, None] = None,
        resource_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene el perfil de acceso activo asignado a un recurso.
        Soporta resolución por ID numérico (resource_id) y/o por clave textual única (resource_key).
        No asigna perfiles por coincidencias aproximadas; requiere correspondencia unívoca exacta.
        """
        profile_id: Optional[int] = None

        # 1. Intentar resolución por ID numérico si está presente en resource_profiles
        if resource_id is not None:
            try:
                r_id = int(resource_id)
                profile_id = self.resource_profiles.get(r_id)
            except (ValueError, TypeError):
                # Si resource_id no es convertible a entero, se evalúa como posible resource_key si no se indicó otra
                if not resource_key and isinstance(resource_id, str):
                    resource_key = resource_id

        # 2. Si no se resolvió por ID numérico o si se suministró resource_key, buscar por clave textual exacta
        if profile_id is None and resource_key and isinstance(resource_key, str):
            profile_id = self.resource_key_profiles.get(resource_key)

        if profile_id is not None:
            return self.profiles.get(profile_id)
        return None

    def get_expected_groups(self, profile_id: int | str) -> List[str]:
        """Obtiene la lista de nombres de grupos esperados para un perfil de usuario."""
        try:
            p_id = int(profile_id)
        except (ValueError, TypeError):
            return []
        return self.expected_groups.get(p_id, [])

    def get_expected_trust_principals(self, profile_id: int | str) -> List[Dict[str, Any]]:
        """Obtiene los principales de confianza esperados para un perfil de rol."""
        try:
            p_id = int(profile_id)
        except (ValueError, TypeError):
            return []
        return self.expected_trust_principals.get(p_id, [])


def extract_resource_attributes(resource: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae y normaliza los atributos técnicos de un recurso IAM.
    Preserva la diferencia entre atributos ausentes y atributos con formato inválido.
    """
    if "attributes" not in resource or resource.get("attributes") is None:
        return {"_missing_attributes": True}

    raw_attrs = resource.get("attributes")
    if isinstance(raw_attrs, str):
        try:
            parsed = json.loads(raw_attrs)
            if isinstance(parsed, dict):
                return parsed
            return {"_invalid_attributes": True, "_raw_error": "El contenido JSON de attributes no es un objeto"}
        except Exception:
            return {"_invalid_attributes": True, "_raw_error": "Sintaxis JSON malformada en attributes"}
    elif isinstance(raw_attrs, dict):
        return raw_attrs

    return {"_invalid_attributes": True, "_raw_error": "El campo attributes no es un diccionario ni cadena JSON"}

