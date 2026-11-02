"""
Generador de Informes de Auditoría IAM en formato CSV.
Produce archivos delimitados por comas con codificación UTF-8 BOM (utf-8-sig)
para compatibilidad nativa con Microsoft Excel en sistemas operativos Windows.
"""
import csv
import os
from pathlib import Path
from typing import Any, Dict


def generate_csv_report(report_data: Dict[str, Any], output_path: str) -> str:
    """
    Exporta las evaluaciones de auditoría a un archivo CSV estructurado.

    Args:
        report_data: Diccionario con la información normalizada de la auditoría.
        output_path: Ruta destino del archivo .csv.

    Returns:
        Ruta absoluta del archivo generado.

    Raises:
        OSError, PermissionError: Si la ruta de destino no es accesible o escribible.
    """
    path_obj = Path(output_path).resolve()
    
    # Crear directorio padre si no existe
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    metadata = report_data.get("metadata", {})
    run_id = metadata.get("run_id", "N/A")
    execution_date = metadata.get("execution_date", "")
    source_type = metadata.get("source_type", "")

    evaluations = report_data.get("evaluations", [])

    # Encabezados en español conforme a especificación
    fieldnames = [
        "ID de auditoría",
        "Fecha",
        "Fuente",
        "Recurso",
        "Tipo de recurso",
        "Control ISO",
        "Regla",
        "Criterio",
        "Estado",
        "Descripción",
    ]

    with open(str(path_obj), mode="w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(fieldnames)

        for ev in evaluations:
            writer.writerow([
                run_id,
                execution_date,
                source_type,
                ev.get("resource_key", ""),
                ev.get("resource_type", "IAM_RESOURCE"),
                ev.get("iso_control", ""),
                ev.get("rule_code", ""),
                ev.get("criterion_code", ""),
                ev.get("result_status", ""),
                ev.get("justification", ""),
            ])

    return str(path_obj)

