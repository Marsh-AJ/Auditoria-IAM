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
from src.auditoria_iam.database.repository import get_audit_results_by_run, get_audit_runs

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
