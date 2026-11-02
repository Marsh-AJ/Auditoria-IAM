"""
Capa de Acceso a Datos (Repositorio) para el Sistema de Auditoría IAM.
Implementa operaciones de consulta de solo lectura, parametrizadas y protegidas contra inyecciones SQL.
"""
from typing import Any, Dict, List, Optional

from src.auditoria_iam.database.connection import get_connection, get_db_cursor


# =============================================================================
# 1. CONSULTAS DE RECURSOS (IDENTIDADES)
# =============================================================================

def get_resources(
    user: Optional[str] = None,
    password: Optional[str] = None,
    source_type: str = "simulacion",
    db_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene la lista de identidades y recursos registrados según su tipo de origen.
    Mantiene compatibilidad con llamadas interactivas (user, password) y centralizadas.
    """
    # Manejo flexible de argumentos posicionales
    if user is not None and password is None and user in ("simulacion", "aws"):
        source_type = user
        user = None

    query = """
        SELECT
            id,
            resource_key,
            resource_type,
            display_name,
            source_type,
            resource_status,
            attributes,
            created_at,
            updated_at
        FROM resources
        WHERE source_type = %s
        ORDER BY display_name
    """

    if user is not None and password is not None:
        conn = get_connection(user=user, password=password, db_name=db_name)
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, (source_type,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (source_type,))
        return cursor.fetchall()


def get_resource_by_id(resource_id: int, db_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Consulta la información detallada de un recurso por su ID único."""
    query = """
        SELECT
            id,
            resource_key,
            resource_type,
            display_name,
            source_type,
            resource_status,
            attributes,
            created_at,
            updated_at
        FROM resources
        WHERE id = %s
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (resource_id,))
        return cursor.fetchone()


def get_resource_by_key(
    resource_key: str,
    source_type: str = "simulacion",
    db_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Consulta un recurso por su clave única y tipo de fuente."""
    query = """
        SELECT
            id,
            resource_key,
            resource_type,
            display_name,
            source_type,
            resource_status,
            attributes,
            created_at,
            updated_at
        FROM resources
        WHERE resource_key = %s AND source_type = %s
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (resource_key, source_type))
        return cursor.fetchone()


# =============================================================================
# 2. CONSULTAS DE REGLAS DE AUDITORÍA
# =============================================================================

def get_active_rules(db_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene el catálogo de reglas de auditoría actualmente activas."""
    query = """
        SELECT
            id,
            rule_code,
            rule_name,
            description,
            iso_control,
            default_severity,
            is_active,
            created_at
        FROM audit_rules
        WHERE is_active = 1
        ORDER BY rule_code
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def get_rule_by_code(rule_code: str, db_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Consulta una regla de auditoría por su código formal (ej. 'IAM-001')."""
    query = """
        SELECT
            id,
            rule_code,
            rule_name,
            description,
            iso_control,
            default_severity,
            is_active,
            created_at
        FROM audit_rules
        WHERE rule_code = %s
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (rule_code,))
        return cursor.fetchone()


def get_rule_by_id(rule_id: int, db_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Consulta una regla de auditoría por su ID numérico."""
    query = """
        SELECT
            id,
            rule_code,
            rule_name,
            description,
            iso_control,
            default_severity,
            is_active,
            created_at
        FROM audit_rules
        WHERE id = %s
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (rule_id,))
        return cursor.fetchone()


# =============================================================================
# 3. CONSULTAS DE PERFILES DE ACCESO DE REFERENCIA
# =============================================================================

def get_active_profiles(
    identity_type: Optional[str] = None,
    db_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Consulta los perfiles de acceso activos, opcionalmente filtrados por tipo ('user' o 'role').
    """
    if identity_type is not None:
        query = """
            SELECT
                id,
                profile_code,
                profile_name,
                identity_type,
                version,
                description,
                status,
                created_at,
                updated_at
            FROM access_profiles
            WHERE status = 'active' AND identity_type = %s
            ORDER BY profile_code
        """
        params = (identity_type,)
    else:
        query = """
            SELECT
                id,
                profile_code,
                profile_name,
                identity_type,
                version,
                description,
                status,
                created_at,
                updated_at
            FROM access_profiles
            WHERE status = 'active'
            ORDER BY profile_code
        """
        params = ()

    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def get_profile_by_code(profile_code: str, db_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Consulta un perfil de acceso por su código nemotécnico."""
    query = """
        SELECT
            id,
            profile_code,
            profile_name,
            identity_type,
            version,
            description,
            status,
            created_at,
            updated_at
        FROM access_profiles
        WHERE profile_code = %s
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (profile_code,))
        return cursor.fetchone()


def get_profile_by_id(profile_id: int, db_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Consulta un perfil de acceso por su clave primaria."""
    query = """
        SELECT
            id,
            profile_code,
            profile_name,
            identity_type,
            version,
            description,
            status,
            created_at,
            updated_at
        FROM access_profiles
        WHERE id = %s
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (profile_id,))
        return cursor.fetchone()


def get_resource_active_profile(
    resource_id: int,
    db_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Consulta el perfil de acceso de referencia actualmente vigente para un recurso.
    Un recurso tiene a lo sumo una asignación activa (valid_to IS NULL).
    """
    query = """
        SELECT
            rap.id AS assignment_id,
            rap.resource_id,
            rap.profile_id,
            rap.valid_from,
            rap.valid_to,
            ap.profile_code,
            ap.profile_name,
            ap.identity_type,
            ap.version,
            ap.description,
            ap.status AS profile_status
        FROM resource_access_profiles rap
        JOIN access_profiles ap ON rap.profile_id = ap.id
        WHERE rap.resource_id = %s
          AND rap.valid_to IS NULL
        ORDER BY rap.valid_from DESC
        LIMIT 1
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (resource_id,))
        return cursor.fetchone()


def get_profile_expected_groups(
    profile_id: int,
    db_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Consulta los grupos IAM esperados asociados a un perfil de tipo usuario."""
    query = """
        SELECT
            id,
            profile_id,
            group_name,
            created_at
        FROM profile_expected_groups
        WHERE profile_id = %s
        ORDER BY group_name
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (profile_id,))
        return cursor.fetchall()


def get_profile_expected_trust_principals(
    profile_id: int,
    db_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Consulta las entidades y acciones de confianza autorizadas para un perfil de rol."""
    query = """
        SELECT
            id,
            profile_id,
            principal_type,
            principal_identifier,
            trust_action,
            created_at
        FROM profile_expected_trust_principals
        WHERE profile_id = %s
        ORDER BY principal_type, principal_identifier
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (profile_id,))
        return cursor.fetchall()


# =============================================================================
# 4. CONSULTAS DE EJECUCIONES, RESULTADOS Y HALLAZGOS
# =============================================================================

def get_audit_runs(limit: int = 50, db_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Consulta las ejecuciones de auditoría más recientes."""
    query = """
        SELECT
            id,
            execution_date,
            source_type,
            status,
            total_findings,
            summary,
            created_at
        FROM audit_runs
        ORDER BY id DESC
        LIMIT %s
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (limit,))
        return cursor.fetchall()


def get_audit_run_by_id(run_id: int, db_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Consulta una ejecución de auditoría por su ID."""
    query = """
        SELECT
            id,
            execution_date,
            source_type,
            status,
            total_findings,
            summary,
            created_at
        FROM audit_runs
        WHERE id = %s
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (run_id,))
        return cursor.fetchone()


def get_audit_results_by_run(
    audit_run_id: int,
    result_status: Optional[str] = None,
    db_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Consulta los resultados detallados de una ejecución de auditoría,
    opcionalmente filtrados por estado ('Conforme', 'Hallazgo', 'No evaluable').
    """
    if result_status is not None:
        query = """
            SELECT
                ar.id,
                ar.audit_run_id,
                ar.resource_id,
                ar.audit_rule_id,
                ar.criterion_code,
                ar.result_status,
                ar.justification,
                ar.profile_id,
                ar.details,
                ar.evaluated_at,
                r.resource_key,
                r.display_name,
                rule.rule_code,
                rule.iso_control
            FROM audit_results ar
            JOIN resources r ON ar.resource_id = r.id
            JOIN audit_rules rule ON ar.audit_rule_id = rule.id
            WHERE ar.audit_run_id = %s AND ar.result_status = %s
            ORDER BY ar.id
        """
        params = (audit_run_id, result_status)
    else:
        query = """
            SELECT
                ar.id,
                ar.audit_run_id,
                ar.resource_id,
                ar.audit_rule_id,
                ar.criterion_code,
                ar.result_status,
                ar.justification,
                ar.profile_id,
                ar.details,
                ar.evaluated_at,
                r.resource_key,
                r.display_name,
                rule.rule_code,
                rule.iso_control
            FROM audit_results ar
            JOIN resources r ON ar.resource_id = r.id
            JOIN audit_rules rule ON ar.audit_rule_id = rule.id
            WHERE ar.audit_run_id = %s
            ORDER BY ar.id
        """
        params = (audit_run_id,)

    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def get_findings_by_run(
    audit_run_id: int,
    db_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Consulta todos los hallazgos registrados en una ejecución de auditoría."""
    query = """
        SELECT
            f.id,
            f.audit_run_id,
            f.resource_id,
            f.audit_rule_id,
            f.audit_result_id,
            f.result_status,
            f.severity,
            f.finding_title,
            f.description,
            f.recommendation,
            f.observed_value,
            f.detected_at,
            r.resource_key,
            r.display_name,
            rule.rule_code,
            rule.iso_control
        FROM findings f
        JOIN resources r ON f.resource_id = r.id
        JOIN audit_rules rule ON f.audit_rule_id = rule.id
        WHERE f.audit_run_id = %s
        ORDER BY f.id
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (audit_run_id,))
        return cursor.fetchall()


def get_evidence_by_finding(
    finding_id: int,
    db_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Consulta las evidencias técnicas vinculadas a un hallazgo específico."""
    query = """
        SELECT
            id,
            finding_id,
            audit_result_id,
            evidence_type,
            evidence_detail,
            evidence_reference,
            captured_at
        FROM audit_evidence
        WHERE finding_id = %s
        ORDER BY id
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (finding_id,))
        return cursor.fetchall()


def get_evidence_by_audit_result(
    audit_result_id: int,
    db_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Consulta las evidencias técnicas vinculadas a un resultado de auditoría."""
    query = """
        SELECT
            id,
            finding_id,
            audit_result_id,
            evidence_type,
            evidence_detail,
            evidence_reference,
            captured_at
        FROM audit_evidence
        WHERE audit_result_id = %s
        ORDER BY id
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (audit_result_id,))
        return cursor.fetchall()


def get_evidence_by_run(
    audit_run_id: int,
    db_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Consulta todas las evidencias técnicas registradas en una ejecución de auditoría."""
    query = """
        SELECT
            ae.id,
            ae.finding_id,
            ae.audit_result_id,
            ae.evidence_type,
            ae.evidence_detail,
            ae.evidence_reference,
            ae.captured_at,
            COALESCE(rf.resource_key, rr.resource_key) AS resource_key,
            COALESCE(rf.display_name, rr.display_name) AS display_name,
            COALESCE(rulef.rule_code, ruler.rule_code) AS rule_code,
            COALESCE(rulef.iso_control, ruler.iso_control) AS iso_control
        FROM audit_evidence ae
        LEFT JOIN findings f ON ae.finding_id = f.id
        LEFT JOIN resources rf ON f.resource_id = rf.id
        LEFT JOIN audit_rules rulef ON f.audit_rule_id = rulef.id
        LEFT JOIN audit_results ar ON ae.audit_result_id = ar.id
        LEFT JOIN resources rr ON ar.resource_id = rr.id
        LEFT JOIN audit_rules ruler ON ar.audit_rule_id = ruler.id
        WHERE f.audit_run_id = %s OR ar.audit_run_id = %s
        ORDER BY ae.id
    """
    with get_db_cursor(db_name=db_name) as cursor:
        cursor.execute(query, (audit_run_id, audit_run_id))
        return cursor.fetchall()

