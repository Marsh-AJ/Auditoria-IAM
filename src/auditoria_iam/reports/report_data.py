"""
Módulo de Normalización y Construcción de Datos para Informes de Auditoría IAM.
Unifica las estructuras de datos provenientes tanto de MySQL como de memoria
en un esquema estándar y enriquecido para los generadores PDF, XLSX y CSV.
"""
from datetime import datetime
import json
from typing import Any, Dict, List, Optional

from src.auditoria_iam.audit.models import AuditResult

# Metadatos del sistema y del estándar
PROJECT_TITLE = "Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A."
ORGANIZATION_NAME = "UPHARVEN C.A."
STANDARD_NAME = "ISO/IEC 27001:2022"
TECHNICAL_DISCLAIMER = (
    "El presente informe refleja exclusivamente una evaluación técnica automatizada "
    "de la configuración lógica de identidades y accesos (IAM) de acuerdo con los "
    "criterios de control del estándar ISO/IEC 27001:2022. No constituye una certificación "
    "formal de cumplimiento organizacional ni sustituye una auditoría integral de tercera parte."
)

RULE_METADATA = {
    "IAM-001": {
        "rule_code": "IAM-001",
        "iso_control": "5.15",
        "control_name": "Gestión de derechos de acceso",
        "default_severity": "ALTA",
        "default_recommendation": (
            "Alinear la asignación de grupos y membresías IAM con el perfil autorizado "
            "en la matriz de accesos y revocar permisos no autorizados."
        ),
    },
    "IAM-002": {
        "rule_code": "IAM-002",
        "iso_control": "5.16",
        "control_name": "Gestión de identidades",
        "default_severity": "MEDIA",
        "default_recommendation": (
            "Deshabilitar o dar de baja las identidades inactivas que superen el umbral "
            "definido de 90 días y depurar el repositorio de usuarios."
        ),
    },
    "IAM-003": {
        "rule_code": "IAM-003",
        "iso_control": "5.18",
        "control_name": "Derechos de acceso privilegiados",
        "default_severity": "CRÍTICA",
        "default_recommendation": (
            "Restringir políticas administradas excesivas (*:*) y limitar las relaciones de "
            "confianza en roles IAM a entidades verificadas y requeridas por el negocio."
        ),
    },
    "IAM-004": {
        "rule_code": "IAM-004",
        "iso_control": "8.5",
        "control_name": "Autenticación segura",
        "default_severity": "ALTA",
        "default_recommendation": (
            "Exigir la habilitación obligatoria de autenticación multifactor (MFA) para todas "
            "las identidades con acceso a consolas o servicios de administración."
        ),
    },
}


def _safe_json_dumps(val: Any) -> str:
    """Convierte un objeto a JSON formateado seguro para cadenas de texto."""
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    try:
        return json.dumps(val, ensure_ascii=False)
    except Exception:
        return str(val)


def build_report_data(
    run_id: Optional[int] = None,
    audit_run: Optional[Dict[str, Any]] = None,
    results: Optional[List[AuditResult]] = None,
    resources: Optional[List[Dict[str, Any]]] = None,
    summary: Optional[Dict[str, int]] = None,
    findings: Optional[List[Dict[str, Any]]] = None,
    evidences: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Construye una estructura de datos normalizada para la generación de reportes.
    
    Acepta datos provenientes de la base de datos MySQL (audit_run, findings, evidences)
    o datos en memoria generados por la sesión de auditoría (results, resources, summary).
    """
    # 1. Metadatos de la ejecución
    exec_run_id = "En memoria"
    if run_id is not None:
        exec_run_id = str(run_id)
    elif audit_run and audit_run.get("id") is not None:
        exec_run_id = str(audit_run["id"])

    execution_date_str = ""
    if audit_run and audit_run.get("execution_date"):
        exec_date = audit_run["execution_date"]
        execution_date_str = exec_date.strftime("%Y-%m-%d %H:%M:%S") if hasattr(exec_date, "strftime") else str(exec_date)
    else:
        execution_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    source_type_str = "simulacion"
    if audit_run and audit_run.get("source_type"):
        source_type_str = str(audit_run["source_type"])

    status_str = "completada"
    if audit_run and audit_run.get("status"):
        status_str = str(audit_run["status"])

    # Mapa de recursos para enriquecimiento
    resource_map: Dict[Any, Dict[str, Any]] = {}
    if resources:
        for r in resources:
            r_id = r.get("id")
            if r_id is not None:
                resource_map[r_id] = r
            r_key = r.get("resource_key")
            if r_key:
                resource_map[r_key] = r

    # 2. Normalizar evaluaciones
    evaluations_list: List[Dict[str, Any]] = []
    
    if results is not None:
        for idx, r in enumerate(results, start=1):
            res_meta = resource_map.get(r.resource_id, {})
            resource_key = res_meta.get("resource_key") or str(r.resource_id)
            display_name = res_meta.get("display_name") or resource_key
            resource_type = res_meta.get("resource_type", "IAM_RESOURCE")
            
            rule_info = RULE_METADATA.get(r.rule_code, {})
            iso_control = rule_info.get("iso_control", "N/A")

            evaluations_list.append({
                "id": idx,
                "resource_id": r.resource_id,
                "resource_key": resource_key,
                "display_name": display_name,
                "resource_type": resource_type,
                "rule_code": r.rule_code,
                "iso_control": iso_control,
                "criterion_code": r.criterion_code,
                "result_status": r.result_status,
                "justification": r.justification,
                "profile_id": r.profile_id,
                "details": r.details if isinstance(r.details, dict) else {},
                "evidence": getattr(r, "evidence", None),
            })

    # 3. Resumen cuantitativo
    total = len(evaluations_list)
    conforme = sum(1 for e in evaluations_list if e["result_status"] == "Conforme")
    hallazgo = sum(1 for e in evaluations_list if e["result_status"] == "Hallazgo")
    no_evaluable = sum(1 for e in evaluations_list if e["result_status"] == "No evaluable")

    if summary:
        total = summary.get("total", total)
        conforme = summary.get("conforme", conforme)
        hallazgo = summary.get("hallazgo", hallazgo)
        no_evaluable = summary.get("no_evaluable", no_evaluable)

    pct_conforme = round((conforme / total * 100), 1) if total > 0 else 0.0
    pct_hallazgo = round((hallazgo / total * 100), 1) if total > 0 else 0.0
    pct_no_evaluable = round((no_evaluable / total * 100), 1) if total > 0 else 0.0

    # 4. Resumen por regla técnica y control ISO
    rules_summary: Dict[str, Dict[str, Any]] = {}
    for code, info in RULE_METADATA.items():
        rules_summary[code] = {
            "rule_code": code,
            "iso_control": info["iso_control"],
            "control_name": info["control_name"],
            "total": 0,
            "conforme": 0,
            "hallazgo": 0,
            "no_evaluable": 0,
            "pct_conforme": 0.0,
        }

    for ev in evaluations_list:
        rc = ev["rule_code"]
        if rc in rules_summary:
            rules_summary[rc]["total"] += 1
            if ev["result_status"] == "Conforme":
                rules_summary[rc]["conforme"] += 1
            elif ev["result_status"] == "Hallazgo":
                rules_summary[rc]["hallazgo"] += 1
            elif ev["result_status"] == "No evaluable":
                rules_summary[rc]["no_evaluable"] += 1

    for rc, stat in rules_summary.items():
        if stat["total"] > 0:
            stat["pct_conforme"] = round((stat["conforme"] / stat["total"]) * 100, 1)

    # 5. Normalizar hallazgos
    findings_list: List[Dict[str, Any]] = []
    if findings is not None and len(findings) > 0:
        for f in findings:
            f_rule = f.get("rule_code") or "N/A"
            r_info = RULE_METADATA.get(f_rule, {})
            crit_code = f.get("criterion_code")
            if not crit_code and ":" in str(f.get("finding_title", "")):
                crit_code = str(f.get("finding_title")).split(":")[-1].strip()
            findings_list.append({
                "id": f.get("id"),
                "audit_run_id": f.get("audit_run_id", exec_run_id),
                "resource_key": f.get("resource_key") or f"ID {f.get('resource_id')}",
                "display_name": f.get("display_name") or f.get("resource_key") or "",
                "rule_code": f_rule,
                "iso_control": f.get("iso_control") or r_info.get("iso_control", "N/A"),
                "criterion_code": crit_code or "N/A",
                "severity": str(f.get("severity") or r_info.get("default_severity", "ALTA")).upper(),
                "finding_title": f.get("finding_title") or f"Hallazgo en {f_rule}",
                "description": f.get("description") or "",
                "observed_value": _safe_json_dumps(f.get("observed_value")),
                "recommendation": f.get("recommendation") or r_info.get("default_recommendation", ""),
            })
    else:
        # Derivar hallazgos a partir de evaluaciones en memoria
        finding_id_seq = 1
        for ev in evaluations_list:
            if ev["result_status"] == "Hallazgo":
                r_info = RULE_METADATA.get(ev["rule_code"], {})
                dtls = ev.get("details", {})
                evd = ev.get("evidence")
                obs_val = _safe_json_dumps(evd if evd is not None else dtls)
                
                findings_list.append({
                    "id": finding_id_seq,
                    "audit_run_id": exec_run_id,
                    "resource_key": ev["resource_key"],
                    "display_name": ev["display_name"],
                    "rule_code": ev["rule_code"],
                    "iso_control": ev["iso_control"],
                    "criterion_code": ev.get("criterion_code", "N/A"),
                    "severity": str(dtls.get("severity") or r_info.get("default_severity", "ALTA")).upper(),
                    "finding_title": f"Hallazgo en {ev['rule_code']}: {ev['criterion_code']}",
                    "description": ev["justification"],
                    "observed_value": obs_val,
                    "recommendation": dtls.get("recommendation") or r_info.get("default_recommendation", ""),
                })
                finding_id_seq += 1

    # 6. Normalizar evidencias técnicas
    evidences_list: List[Dict[str, Any]] = []
    if evidences is not None and len(evidences) > 0:
        for ev in evidences:
            evidences_list.append({
                "id": ev.get("id"),
                "target_ref": f"Hallazgo #{ev.get('finding_id')}" if ev.get("finding_id") else f"Resultado #{ev.get('audit_result_id')}",
                "resource_key": ev.get("resource_key") or "N/A",
                "display_name": ev.get("display_name") or "",
                "rule_code": ev.get("rule_code") or "N/A",
                "iso_control": ev.get("iso_control") or "N/A",
                "evidence_type": ev.get("evidence_type") or "técnica",
                "evidence_detail": _safe_json_dumps(ev.get("evidence_detail")),
                "evidence_reference": ev.get("evidence_reference") or "",
                "captured_at": str(ev.get("captured_at") or execution_date_str),
            })
    else:
        # Derivar evidencias de evaluaciones en memoria
        ev_id_seq = 1
        for ev in evaluations_list:
            evd = ev.get("evidence")
            if evd:
                ev_type = evd.get("evidence_type", "técnica_ciberseguridad") if isinstance(evd, dict) else "técnica_ciberseguridad"
                ev_detail = _safe_json_dumps(evd)
                ev_ref = f"resource:{ev['resource_key']}:{ev['criterion_code']}"
                target_ref = f"Evaluación #{ev['id']} ({ev['result_status']})"
                evidences_list.append({
                    "id": ev_id_seq,
                    "target_ref": target_ref,
                    "resource_key": ev["resource_key"],
                    "display_name": ev["display_name"],
                    "rule_code": ev["rule_code"],
                    "iso_control": ev["iso_control"],
                    "evidence_type": ev_type,
                    "evidence_detail": ev_detail,
                    "evidence_reference": ev_ref,
                    "captured_at": execution_date_str,
                })
                ev_id_seq += 1

    unique_resources_count = len({e["resource_key"] for e in evaluations_list}) if evaluations_list else len(resource_map)

    return {
        "metadata": {
            "run_id": exec_run_id,
            "execution_date": execution_date_str,
            "source_type": source_type_str,
            "status": status_str,
            "project_name": PROJECT_TITLE,
            "organization": ORGANIZATION_NAME,
            "standard": STANDARD_NAME,
            "disclaimer": TECHNICAL_DISCLAIMER,
            "total_resources": unique_resources_count,
        },
        "summary": {
            "total": total,
            "conforme": conforme,
            "hallazgo": hallazgo,
            "no_evaluable": no_evaluable,
            "pct_conforme": pct_conforme,
            "pct_hallazgo": pct_hallazgo,
            "pct_no_evaluable": pct_no_evaluable,
        },
        "rules_summary": rules_summary,
        "evaluations": evaluations_list,
        "findings": findings_list,
        "evidences": evidences_list,
    }

