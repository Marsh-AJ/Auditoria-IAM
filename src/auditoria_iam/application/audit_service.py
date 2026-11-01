"""
Servicio de Aplicación para la Orquestación de Auditorías IAM.
Coordina la interacción entre las fuentes de datos (Simulador) y el Motor Central de Auditoría,
estructurando los resultados para su presentación en la interfaz de usuario.
"""
from typing import Any, Dict, List, Optional, Tuple

from src.auditoria_iam.audit.engine import AuditEngine
from src.auditoria_iam.audit.models import AuditContext, AuditResult
from src.auditoria_iam.data_sources.simulator.simulator import (
    IAMSimulatorDataSource,
    get_simulated_audit_context,
    get_simulated_resources,
)


class AuditService:
    """
    Servicio de orquestación de auditorías.
    Ejecuta el motor algorítmico existente sobre las fuentes de datos admitidas
    sin acoplar la interfaz gráfica a la lógica interna de evaluación.
    """

    def __init__(self, engine: Optional[AuditEngine] = None) -> None:
        self.engine = engine or AuditEngine()

    def run_simulated_audit(self) -> Tuple[List[AuditResult], List[Dict[str, Any]], Dict[str, int]]:
        """
        Ejecuta la auditoría completa sobre el conjunto de datos simulados.

        Returns:
            Tuple con:
            - results: Lista de instancias AuditResult producidas por el motor.
            - resources: Lista de recursos evaluados con sus atributos normalizados.
            - summary: Diccionario resumen con conteos de total, conforme, hallazgo y no_evaluable.
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

        return results, resources, summary

