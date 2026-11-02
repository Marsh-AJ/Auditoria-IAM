"""
Servicio de Aplicación para la Orquestación y Persistencia de Auditorías IAM.
Coordina la interacción entre las fuentes de datos (Simulador), el Motor Central
de Auditoría y la capa de almacenamiento en MySQL Server.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from src.auditoria_iam.audit.engine import AuditEngine
from src.auditoria_iam.audit.models import AuditContext, AuditResult
from src.auditoria_iam.data_sources.simulator.simulator import (
    IAMSimulatorDataSource,
    get_simulated_audit_context,
    get_simulated_resources,
)
from src.auditoria_iam.database.persistence import save_audit_run
from src.auditoria_iam.database.repository import (
    get_audit_results_by_run,
    get_audit_run_by_id,
    get_audit_runs,
    get_evidence_by_run,
    get_findings_by_run,
)
from src.auditoria_iam.reports import (
    build_report_data,
    generate_csv_report,
    generate_excel_report,
    generate_pdf_report,
)

logger = logging.getLogger(__name__)


class AuditService:
    """
    Servicio de orquestación desacoplado.
    Ejecuta el motor algorítmico existente, gestiona la persistencia transaccional en MySQL
    y permite la consulta histórica de auditorías previas.
    """

    def __init__(self, engine: Optional[AuditEngine] = None) -> None:
        self.engine = engine or AuditEngine()

    def run_simulated_audit(
        self, persist: bool = True, db_name: Optional[str] = None
    ) -> Tuple[List[AuditResult], List[Dict[str, Any]], Dict[str, int], Dict[str, Any]]:
        """
        Ejecuta la auditoría completa sobre el conjunto de datos simulados y opcionalmente
        persiste la ejecución y sus resultados en MySQL.

        Args:
            persist: Si es True, intenta registrar la auditoría en MySQL de forma transaccional.
            db_name: Nombre opcional de la base de datos (para pruebas independientes).

        Returns:
            Tuple con:
            - results: Lista de instancias AuditResult producidas por el motor.
            - resources: Lista de recursos evaluados con sus atributos normalizados.
            - summary: Diccionario resumen con conteos de total, conforme, hallazgo y no_evaluable.
            - persistence_info: Diccionario con estado de persistencia ('persisted', 'run_id', 'message').
        """
        resources = IAMSimulatorDataSource.get_resources()
        context = IAMSimulatorDataSource.get_audit_context()

        # Invocar el motor de auditoría centralizado existente
        results = self.engine.evaluate_all(resources=resources, context=context)

        summary = {
            "total": len(results),
            "conforme": sum(1 for r in results if r.result_status == "Conforme"),
            "hallazgo": sum(1 for r in results if r.result_status == "Hallazgo"),
            "no_evaluable": sum(1 for r in results if r.result_status == "No evaluable"),
        }

        persistence_info: Dict[str, Any] = {
            "persisted": False,
            "run_id": None,
            "message": "",
        }

        if persist:
            try:
                run_id = save_audit_run(
                    source_type="simulacion",
                    results=results,
                    resources=resources,
                    summary=summary,
                    context=context,
                    db_name=db_name,
                )
                persistence_info["persisted"] = True
                persistence_info["run_id"] = run_id
                persistence_info["message"] = f"✓ Auditoría guardada exitosamente en MySQL (Ejecución ID #{run_id})."
            except Exception as exc:
                logger.warning(f"No fue posible persistir la auditoría en MySQL: {exc}")
                persistence_info["persisted"] = False
                persistence_info["message"] = (
                    f"⚠️ Aviso de persistencia: No se pudo conectar o guardar en MySQL ({type(exc).__name__}). "
                    "Los resultados se conservan íntegros en memoria para esta sesión."
                )

        return results, resources, summary, persistence_info

    def get_audit_history(self, limit: int = 50, db_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Recupera el listado de ejecuciones de auditoría guardadas en MySQL.

        Args:
            limit: Límite de registros a recuperar.
            db_name: Sobreescritura opcional de base de datos.

        Returns:
            Lista de diccionarios representando los registros de `audit_runs`.
        """
        return get_audit_runs(limit=limit, db_name=db_name)

    def get_historical_run_results(
        self, run_id: int, db_name: Optional[str] = None
    ) -> Tuple[List[AuditResult], List[Dict[str, Any]], Dict[str, int]]:
        """
        Recupera los resultados de una auditoría guardada en MySQL y los transforma
        a instancias del modelo AuditResult para su consumo en la interfaz.

        Args:
            run_id: Identificador de la ejecución (`audit_runs.id`).
            db_name: Sobreescritura opcional de base de datos.

        Returns:
            Tuple con (results, resources, summary).
        """
        db_results = get_audit_results_by_run(audit_run_id=run_id, db_name=db_name)
        results: List[AuditResult] = []
        resources_dict: Dict[Any, Dict[str, Any]] = {}

        for row in db_results:
            res_id = row.get("resource_id")
            if res_id not in resources_dict:
                resources_dict[res_id] = {
                    "id": res_id,
                    "resource_key": row.get("resource_key") or f"ID {res_id}",
                    "display_name": row.get("display_name"),
                    "resource_type": "IAM_RESOURCE",
                }

            details = row.get("details")
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except Exception:
                    details = {}
            elif not isinstance(details, dict):
                details = {}

            results.append(
                AuditResult(
                    rule_code=row.get("rule_code") or "IAM-001",
                    criterion_code=row.get("criterion_code") or "N/A",
                    resource_id=res_id,
                    result_status=row.get("result_status") or "No evaluable",
                    justification=row.get("justification") or "",
                    profile_id=row.get("profile_id"),
                    details=details,
                )
            )

        resources = list(resources_dict.values())
        summary = {
            "total": len(results),
            "conforme": sum(1 for r in results if r.result_status == "Conforme"),
            "hallazgo": sum(1 for r in results if r.result_status == "Hallazgo"),
            "no_evaluable": sum(1 for r in results if r.result_status == "No evaluable"),
        }
        return results, resources, summary

    def get_dashboard_data(self, db_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Recupera y calcula de forma agregada las métricas del dashboard
        a partir de la última ejecución de auditoría persistida en MySQL.
        Operación estrictamente de solo lectura (SELECT).

        Args:
            db_name: Sobreescritura opcional de base de datos para pruebas.

        Returns:
            Diccionario estructurado con indicadores KPI, distribución porcentual,
            resumen por regla y metadatos de la última auditoría.
        """
        runs = self.get_audit_history(limit=1, db_name=db_name)
        if not runs:
            return {
                "has_data": False,
                "latest_run": None,
                "summary": {"total": 0, "conforme": 0, "hallazgo": 0, "no_evaluable": 0},
                "distribution": {
                    "conforme": {"count": 0, "percentage": 0.0},
                    "hallazgo": {"count": 0, "percentage": 0.0},
                    "no_evaluable": {"count": 0, "percentage": 0.0},
                },
                "rules_summary": {
                    "IAM-001": {"conforme": 0, "hallazgo": 0, "no_evaluable": 0, "total": 0, "iso_control": "5.15"},
                    "IAM-002": {"conforme": 0, "hallazgo": 0, "no_evaluable": 0, "total": 0, "iso_control": "5.16"},
                    "IAM-003": {"conforme": 0, "hallazgo": 0, "no_evaluable": 0, "total": 0, "iso_control": "5.18"},
                    "IAM-004": {"conforme": 0, "hallazgo": 0, "no_evaluable": 0, "total": 0, "iso_control": "8.5"},
                },
            }

        latest_run = runs[0]
        run_id = latest_run["id"]
        results, resources, summary = self.get_historical_run_results(run_id=run_id, db_name=db_name)

        total = summary.get("total", len(results))
        conforme = summary.get("conforme", 0)
        hallazgo = summary.get("hallazgo", 0)
        no_evaluable = summary.get("no_evaluable", 0)

        pct_conforme = round((conforme / total) * 100, 1) if total > 0 else 0.0
        pct_hallazgo = round((hallazgo / total) * 100, 1) if total > 0 else 0.0
        pct_no_evaluable = round((no_evaluable / total) * 100, 1) if total > 0 else 0.0

        rules_summary: Dict[str, Dict[str, Any]] = {
            "IAM-001": {"conforme": 0, "hallazgo": 0, "no_evaluable": 0, "total": 0, "iso_control": "5.15"},
            "IAM-002": {"conforme": 0, "hallazgo": 0, "no_evaluable": 0, "total": 0, "iso_control": "5.16"},
            "IAM-003": {"conforme": 0, "hallazgo": 0, "no_evaluable": 0, "total": 0, "iso_control": "5.18"},
            "IAM-004": {"conforme": 0, "hallazgo": 0, "no_evaluable": 0, "total": 0, "iso_control": "8.5"},
        }

        for r in results:
            if r.rule_code in rules_summary:
                rules_summary[r.rule_code]["total"] += 1
                if r.result_status == "Conforme":
                    rules_summary[r.rule_code]["conforme"] += 1
                elif r.result_status == "Hallazgo":
                    rules_summary[r.rule_code]["hallazgo"] += 1
                elif r.result_status == "No evaluable":
                    rules_summary[r.rule_code]["no_evaluable"] += 1

        return {
            "has_data": True,
            "latest_run": latest_run,
            "summary": summary,
            "distribution": {
                "conforme": {"count": conforme, "percentage": pct_conforme},
                "hallazgo": {"count": hallazgo, "percentage": pct_hallazgo},
                "no_evaluable": {"count": no_evaluable, "percentage": pct_no_evaluable},
            },
            "rules_summary": rules_summary,
            "run_id": run_id,
            "results": results,
            "resources": resources,
        }

    def get_audit_report_data(
        self,
        run_id: Optional[int] = None,
        results: Optional[List[AuditResult]] = None,
        resources: Optional[List[Dict[str, Any]]] = None,
        summary: Optional[Dict[str, int]] = None,
        db_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Prepara y normaliza los datos requeridos para la generación de informes (PDF, XLSX, CSV).
        Operación estrictamente de solo lectura (SELECT en MySQL o lectura de estructuras en memoria).

        Args:
            run_id: Identificador de la ejecución en MySQL (si se exporta un resultado histórico).
            results: Lista opcional de instancias AuditResult (en memoria o históricas).
            resources: Lista opcional de recursos normalizados.
            summary: Diccionario opcional con el resumen cuantitativo.
            db_name: Sobreescritura opcional de base de datos para pruebas.

        Returns:
            Estructura de datos normalizada para los generadores de informes.
        """
        audit_run = None
        findings = None
        evidences = None

        if run_id is not None:
            # Consultar metadatos de la corrida histórica
            try:
                audit_run = get_audit_run_by_id(run_id=run_id, db_name=db_name)
            except Exception as exc:
                logger.warning(f"No fue posible consultar audit_run #{run_id}: {exc}")

            # Consultar hallazgos persistidos
            try:
                findings = get_findings_by_run(audit_run_id=run_id, db_name=db_name)
            except Exception as exc:
                logger.warning(f"No fue posible consultar findings para corrida #{run_id}: {exc}")

            # Consultar evidencias persistidas
            try:
                evidences = get_evidence_by_run(audit_run_id=run_id, db_name=db_name)
            except Exception as exc:
                logger.warning(f"No fue posible consultar evidencias para corrida #{run_id}: {exc}")

            # Si no se suministraron resultados en memoria, recuperarlos de la base de datos
            if results is None:
                results, resources, summary = self.get_historical_run_results(run_id=run_id, db_name=db_name)

        return build_report_data(
            run_id=run_id,
            audit_run=audit_run,
            results=results,
            resources=resources,
            summary=summary,
            findings=findings,
            evidences=evidences,
        )

    def export_audit_report(
        self,
        filepath: str,
        format_type: str,
        run_id: Optional[int] = None,
        results: Optional[List[AuditResult]] = None,
        resources: Optional[List[Dict[str, Any]]] = None,
        summary: Optional[Dict[str, int]] = None,
        db_name: Optional[str] = None,
    ) -> str:
        """
        Exporta el informe de auditoría en el formato seleccionado (PDF, XLSX o CSV).
        Garantiza estricta ausencia de escrituras en MySQL y cero re-ejecución de auditorías.

        Args:
            filepath: Ruta completa del archivo destino.
            format_type: Formato de salida ('pdf', 'xlsx' / 'excel', 'csv').
            run_id: Identificador opcional de la corrida histórica en MySQL.
            results: Lista opcional de resultados.
            resources: Lista opcional de recursos evaluados.
            summary: Diccionario opcional con el resumen cuantitativo.
            db_name: Base de datos opcional para pruebas.

        Returns:
            Ruta absoluta del archivo exportado generado.

        Raises:
            ValueError: Si el formato no es compatible.
            OSError, PermissionError: Si hay fallas de escritura en disco.
        """
        report_data = self.get_audit_report_data(
            run_id=run_id,
            results=results,
            resources=resources,
            summary=summary,
            db_name=db_name,
        )

        fmt = format_type.strip().lower()

        if fmt == "pdf":
            return generate_pdf_report(report_data=report_data, output_path=filepath)
        elif fmt in ("xlsx", "excel"):
            return generate_excel_report(report_data=report_data, output_path=filepath)
        elif fmt == "csv":
            return generate_csv_report(report_data=report_data, output_path=filepath)
        else:
            raise ValueError(
                f"Formato de exportación no soportado: '{format_type}'. "
                "Los formatos disponibles son: 'pdf', 'xlsx' (Excel) y 'csv'."
            )


