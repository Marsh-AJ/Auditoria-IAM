"""
Capa de Persistencia para el Sistema de Auditoría IAM.
Implementa operaciones de escritura transaccionales (INSERT) para el registro atómico
de ejecuciones, resultados granulares, hallazgos y evidencias en MySQL Server,
garantizando estricta integridad referencial mediante claves naturales (resource_key, rule_code, profile_code).
"""
from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional

from src.auditoria_iam.audit.models import AuditContext, AuditResult
from src.auditoria_iam.database.connection import get_db_transaction

logger = logging.getLogger(__name__)

# Severidades por defecto por código de regla técnica ISO/IEC 27001
DEFAULT_SEVERITIES = {
    "IAM-001": "ALTA",
    "IAM-002": "MEDIA",
    "IAM-003": "CRITICA",
    "IAM-004": "ALTA",
}

# Recomendaciones operativas estándar para hallazgos de auditoría
DEFAULT_RECOMMENDATIONS = {
    "IAM-001": "Alinear la membresía de grupos y las entidades de confianza con el perfil de acceso autorizado.",
    "IAM-002": "Desactivar o revocar las credenciales inactivas que excedan el umbral establecido de 90 días.",
    "IAM-003": "Restringir políticas con comodines globales ('*') aplicando el principio de mínimo privilegio.",
    "IAM-004": "Activar obligatoriamente la autenticación multifactor (MFA) para el usuario de la plataforma.",
}


def save_audit_run(
    source_type: str,
    results: List[AuditResult],
    resources: List[Dict[str, Any]],
    summary: Dict[str, int],
    context: Optional[AuditContext] = None,
    db_name: Optional[str] = None,
) -> int:
    """
    Persiste de forma atómica una ejecución de auditoría en MySQL Server.

    Inserta en una única transacción:
    1. Registro maestro en `audit_runs`.
    2. Resultados individuales en `audit_results` resolviendo IDs reales de `resources`, `audit_rules` y `access_profiles`.
    3. Hallazgos en `findings` vinculados al resultado correspondiente.
    4. Evidencias técnicas en `audit_evidence` respetando la restricción chk_evidence_target.

    Ante cualquier fallo o inconsistencia referencial, la transacción efectúa rollback completo.

    Args:
        source_type: Identificador del origen de datos ('simulacion' o 'aws').
        results: Lista de instancias AuditResult generadas por el motor.
        resources: Lista de recursos evaluados con sus metadatos.
        summary: Diccionario con los totales (total, conforme, hallazgo, no_evaluable).
        context: Contexto de auditoría con perfiles autorizados (para correspondencia inequívoca).
        db_name: Sobreescritura opcional del nombre de base de datos para pruebas.

    Returns:
        int: ID generado de la ejecución en `audit_runs`.

    Raises:
        RuntimeError: Si faltan reglas, recursos o existen inconsistencias en la base de datos.
    """
    with get_db_transaction(db_name=db_name) as cursor:
        # =====================================================================
        # 1. RESOLUCIÓN ESTRICTA DE REGLAS (audit_rules) POR CÓDIGO FORMAL
        # =====================================================================
        cursor.execute("SELECT id, rule_code, default_severity FROM audit_rules")
        rule_rows = cursor.fetchall()
        rule_id_map: Dict[str, int] = {}
        rule_sev_map: Dict[str, str] = {}
        for r in rule_rows:
            rule_id_map[r["rule_code"]] = r["id"]
            if "default_severity" in r and r["default_severity"]:
                rule_sev_map[r["rule_code"]] = str(r["default_severity"]).upper()

        # Validar que todas las reglas requeridas existan en la tabla audit_rules
        required_rules = {res.rule_code for res in results}
        missing_rules = required_rules - set(rule_id_map.keys())
        if missing_rules:
            raise RuntimeError(
                f"Las siguientes reglas técnicas requeridas no existen en la tabla 'audit_rules' de MySQL: "
                f"{sorted(list(missing_rules))}. Operación cancelada; no se permite asociar IDs de respaldo."
            )

        # =====================================================================
        # 2. RESOLUCIÓN SEGURA DE RECURSOS (resources) POR resource_key Y source_type
        # =====================================================================
        # Mapa de ID simulado a resource_key
        sim_id_to_key: Dict[Any, str] = {}
        for r in resources:
            if r.get("id") is not None and r.get("resource_key"):
                sim_id_to_key[r["id"]] = r["resource_key"]

        # Consultar recursos existentes en MySQL para este source_type
        cursor.execute(
            "SELECT id, resource_key FROM resources WHERE source_type = %s",
            (source_type,)
        )
        db_resource_rows = cursor.fetchall()
        key_to_db_id: Dict[str, int] = {}
        for r in db_resource_rows:
            k = r["resource_key"]
            if k in key_to_db_id:
                raise RuntimeError(
                    f"Correspondencia ambigua en la tabla 'resources': la clave '{k}' "
                    f"aparece duplicada para el origen '{source_type}'."
                )
            key_to_db_id[k] = r["id"]

        # Validar la correspondencia de todos los recursos antes de insertar
        resolved_resource_ids: Dict[Any, int] = {}
        resolved_resource_keys: Dict[Any, str] = {}
        for res in results:
            res_key = sim_id_to_key.get(res.resource_id)
            if not res_key and isinstance(res.resource_id, str):
                res_key = res.resource_id

            if not res_key:
                raise RuntimeError(
                    f"No se pudo determinar la clave única (resource_key) para el recurso con ID '{res.resource_id}'. "
                    "Falta registrar el recurso correspondiente en la base de datos."
                )

            db_id = key_to_db_id.get(res_key)
            if db_id is None:
                raise RuntimeError(
                    f"El recurso con clave '{res_key}' y origen '{source_type}' no existe en la tabla 'resources' de MySQL. "
                    "Falta registrar el recurso correspondiente. No se asignan identificadores de sustitución."
                )
            resolved_resource_ids[res.resource_id] = db_id
            resolved_resource_keys[res.resource_id] = res_key

        # =====================================================================
        # 3. RESOLUCIÓN INEQUÍVOCA DE PERFILES DE ACCESO (access_profiles)
        # =====================================================================
        cursor.execute("SELECT id, profile_code FROM access_profiles")
        db_profile_rows = cursor.fetchall()
        db_profile_code_map: Dict[str, int] = {
            row["profile_code"]: row["id"] for row in db_profile_rows if "profile_code" in row
        }

        # Catálogo de perfiles del contexto si estuviera disponible
        sim_profiles = {}
        if context is not None and hasattr(context, "profiles") and isinstance(context.profiles, dict):
            sim_profiles = context.profiles

        # =====================================================================
        # 4. INSERCIÓN MAESTRA EN audit_runs
        # =====================================================================
        execution_date = datetime.now()
        total_findings = summary.get("hallazgo", 0)
        summary_text = (
            f"Total: {summary.get('total', len(results))} | "
            f"Conforme: {summary.get('conforme', 0)} | "
            f"Hallazgo: {total_findings} | "
            f"No evaluable: {summary.get('no_evaluable', 0)}"
        )

        query_run = """
            INSERT INTO audit_runs (execution_date, source_type, status, total_findings, summary)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query_run, (
            execution_date,
            source_type,
            "completada",
            total_findings,
            summary_text,
        ))
        audit_run_id = cursor.lastrowid

        # =====================================================================
        # 5. INSERCIÓN DE RESULTADOS INDIVIDUALES (audit_results)
        # =====================================================================
        for res in results:
            rule_id = rule_id_map[res.rule_code]
            db_res_id = resolved_resource_ids[res.resource_id]
            res_key = resolved_resource_keys[res.resource_id]

            # Determinar profile_id únicamente ante correspondencia inequívoca por código
            prof_id = None
            if res.profile_id is not None:
                target_code = None
                if isinstance(res.details, dict) and res.details.get("profile_code"):
                    target_code = res.details["profile_code"]
                elif res.profile_id in sim_profiles:
                    p_info = sim_profiles[res.profile_id]
                    if isinstance(p_info, dict):
                        target_code = p_info.get("profile_code")

                # Si el código de perfil existe inequívocamente en MySQL, asignar su ID real
                if target_code and target_code in db_profile_code_map:
                    prof_id = db_profile_code_map[target_code]
                else:
                    # Si no puede demostrarse correspondencia inequívoca, asignar NULL
                    prof_id = None

            details_json = json.dumps(res.details, ensure_ascii=False) if res.details else None

            query_result = """
                INSERT INTO audit_results (
                    audit_run_id, resource_id, audit_rule_id, criterion_code,
                    result_status, justification, profile_id, details
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_result, (
                audit_run_id,
                db_res_id,
                rule_id,
                res.criterion_code,
                res.result_status,
                res.justification,
                prof_id,
                details_json,
            ))
            audit_result_id = cursor.lastrowid

            # =================================================================
            # 6. REGISTRO DE HALLAZGOS (findings) PARA RESULTADOS 'Hallazgo'
            # =================================================================
            if res.result_status == "Hallazgo":
                severity = (
                    res.details.get("severity")
                    or rule_sev_map.get(res.rule_code)
                    or DEFAULT_SEVERITIES.get(res.rule_code, "ALTA")
                )
                finding_title = f"Hallazgo en {res.rule_code}: {res.criterion_code}"
                description = res.justification
                recommendation = (
                    res.details.get("recommendation")
                    or DEFAULT_RECOMMENDATIONS.get(res.rule_code, "Revisar y corregir la configuración técnica.")
                )
                observed_value = json.dumps(res.evidence, ensure_ascii=False) if res.evidence else None

                query_finding = """
                    INSERT INTO findings (
                        audit_run_id, resource_id, audit_rule_id, audit_result_id,
                        result_status, severity, finding_title, description,
                        recommendation, observed_value
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query_finding, (
                    audit_run_id,
                    db_res_id,
                    rule_id,
                    audit_result_id,
                    "Hallazgo",
                    str(severity).upper(),
                    finding_title,
                    description,
                    recommendation,
                    observed_value,
                ))
                finding_id = cursor.lastrowid

                # =============================================================
                # 7. REGISTRO DE EVIDENCIA TÉCNICA ASOCIADA AL HALLAZGO
                # =============================================================
                if res.evidence:
                    evidence_type = res.evidence.get("evidence_type", "hallazgo_ciberseguridad")
                    evidence_detail = json.dumps(res.evidence, ensure_ascii=False)
                    evidence_reference = f"resource:{res_key}:{res.criterion_code}"

                    # Cumple con restricción chk_evidence_target: finding_id IS NOT NULL y audit_result_id IS NULL
                    query_evidence = """
                        INSERT INTO audit_evidence (
                            finding_id, audit_result_id, evidence_type, evidence_detail, evidence_reference
                        ) VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(query_evidence, (
                        finding_id,
                        None,
                        evidence_type,
                        evidence_detail,
                        evidence_reference,
                    ))

            # =================================================================
            # 8. REGISTRO DE EVIDENCIA TÉCNICA PARA OTROS RESULTADOS CON EVIDENCIA
            # =================================================================
            elif res.evidence:
                evidence_type = res.evidence.get("evidence_type", "metadatos_evaluacion")
                evidence_detail = json.dumps(res.evidence, ensure_ascii=False)
                evidence_reference = f"resource:{res_key}:{res.criterion_code}"

                # Cumple con restricción chk_evidence_target: finding_id IS NULL y audit_result_id IS NOT NULL
                query_evidence = """
                    INSERT INTO audit_evidence (
                        finding_id, audit_result_id, evidence_type, evidence_detail, evidence_reference
                    ) VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(query_evidence, (
                    None,
                    audit_result_id,
                    evidence_type,
                    evidence_detail,
                    evidence_reference,
                ))

        return audit_run_id
