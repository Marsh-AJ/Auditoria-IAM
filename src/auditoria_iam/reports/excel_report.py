"""
Generador de Informes de Auditoría IAM en formato Microsoft Excel (XLSX).
Construye un libro de cálculo estructurado con múltiples hojas (Resumen, Evaluaciones,
Hallazgos, Evidencias), formateo profesional, congelamiento de paneles y filtros automáticos.
"""
from pathlib import Path
from typing import Any, Dict

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


# Estilos de encabezado y celdas
NAVY_HEADER_FILL = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
SUBHEADER_FILL = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
LIGHT_GRAY_FILL = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

STATUS_FILLS = {
    "Conforme": PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid"),
    "Hallazgo": PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid"),
    "No evaluable": PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid"),
}

STATUS_FONTS = {
    "Conforme": Font(name="Calibri", size=10, bold=True, color="16A34A"),
    "Hallazgo": Font(name="Calibri", size=10, bold=True, color="DC2626"),
    "No evaluable": Font(name="Calibri", size=10, bold=True, color="64748B"),
}

SEVERITY_FONTS = {
    "CRÍTICA": Font(name="Calibri", size=10, bold=True, color="991B1B"),
    "ALTA": Font(name="Calibri", size=10, bold=True, color="DC2626"),
    "MEDIA": Font(name="Calibri", size=10, bold=True, color="D97706"),
    "BAJA": Font(name="Calibri", size=10, bold=True, color="475569"),
}

HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="0F172A")
SECTION_FONT = Font(name="Calibri", size=12, bold=True, color="1E293B")
BOLD_FONT = Font(name="Calibri", size=10, bold=True, color="0F172A")
REGULAR_FONT = Font(name="Calibri", size=10, color="0F172A")
MUTED_FONT = Font(name="Calibri", size=9, italic=True, color="64748B")

THIN_BORDER_SIDE = Side(border_style="thin", color="CBD5E1")
GRID_BORDER = Border(
    left=THIN_BORDER_SIDE,
    right=THIN_BORDER_SIDE,
    top=THIN_BORDER_SIDE,
    bottom=THIN_BORDER_SIDE,
)


def _adjust_column_widths(ws: openpyxl.worksheet.worksheet.Worksheet, min_width: int = 12, max_width: int = 65) -> None:
    """Ajusta automáticamente el ancho de las columnas según su contenido."""
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            val = cell.value
            if val is not None:
                lines = str(val).split("\n")
                line_max = max(len(l) for l in lines)
                if line_max > max_len:
                    max_len = line_max
        chosen_width = max(min(max_len + 3, max_width), min_width)
        ws.column_dimensions[col_letter].width = chosen_width


def generate_excel_report(report_data: Dict[str, Any], output_path: str) -> str:
    """
    Genera un informe detallado de auditoría en formato Excel (.xlsx).

    Args:
        report_data: Diccionario con la información normalizada de la auditoría.
        output_path: Ruta destino del archivo Excel.

    Returns:
        Ruta absoluta del archivo generado.
    """
    path_obj = Path(output_path).resolve()
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.Workbook()
    # Eliminar hoja por defecto al configurar las hojas requeridas
    wb.remove(wb.active)

    metadata = report_data.get("metadata", {})
    summary = report_data.get("summary", {})
    rules_summary = report_data.get("rules_summary", {})
    evaluations = report_data.get("evaluations", [])
    findings = report_data.get("findings", [])
    evidences = report_data.get("evidences", [])

    # =========================================================================
    # HOJA 1: RESUMEN
    # =========================================================================
    ws_resumen = wb.create_sheet(title="Resumen")
    ws_resumen.views.sheetView[0].showGridLines = True

    # Título institucional
    ws_resumen["A1"] = "INFORME DE AUDITORÍA IAM — GESTIÓN DE IDENTIDADES Y ACCESOS"
    ws_resumen["A1"].font = TITLE_FONT
    ws_resumen["A2"] = f"Organización: {metadata.get('organization', 'UPHARVEN C.A.')}  |  Estándar: {metadata.get('standard', 'ISO/IEC 27001:2022')}"
    ws_resumen["A2"].font = Font(name="Calibri", size=10, italic=True, color="475569")

    # Metadatos generales
    ws_resumen["A4"] = "Metadatos de la Evaluación"
    ws_resumen["A4"].font = SECTION_FONT

    meta_items = [
        ("Identificador de Auditoría:", str(metadata.get("run_id", "N/A"))),
        ("Fecha y Hora:", str(metadata.get("execution_date", ""))),
        ("Fuente de Datos:", str(metadata.get("source_type", ""))),
        ("Estado de Ejecución:", str(metadata.get("status", "completada")).capitalize()),
        ("Recursos IAM Evaluados:", str(metadata.get("total_resources", 0))),
    ]

    for row_idx, (label, val) in enumerate(meta_items, start=5):
        c_lbl = ws_resumen.cell(row=row_idx, column=1, value=label)
        c_lbl.font = BOLD_FONT
        c_val = ws_resumen.cell(row=row_idx, column=2, value=val)
        c_val.font = REGULAR_FONT

    # Resumen cuantitativo global (KPIs)
    ws_resumen["A10"] = "Indicadores Globales de Conformidad"
    ws_resumen["A10"].font = SECTION_FONT

    headers_kpi = ["Métrica", "Cantidad", "Porcentaje (%)"]
    for col_idx, h in enumerate(headers_kpi, start=1):
        c = ws_resumen.cell(row=11, column=col_idx, value=h)
        c.fill = NAVY_HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = Alignment(horizontal="center")
        c.border = GRID_BORDER

    kpi_rows = [
        ("Conforme", summary.get("conforme", 0), summary.get("pct_conforme", 0.0) / 100.0),
        ("Hallazgo", summary.get("hallazgo", 0), summary.get("pct_hallazgo", 0.0) / 100.0),
        ("No evaluable", summary.get("no_evaluable", 0), summary.get("pct_no_evaluable", 0.0) / 100.0),
        ("Total Evaluaciones", summary.get("total", 0), 1.0),
    ]

    for idx, (label, count, pct) in enumerate(kpi_rows, start=12):
        c1 = ws_resumen.cell(row=idx, column=1, value=label)
        c2 = ws_resumen.cell(row=idx, column=2, value=count)
        c3 = ws_resumen.cell(row=idx, column=3, value=pct)

        c1.border = GRID_BORDER
        c2.border = GRID_BORDER
        c3.border = GRID_BORDER

        c2.alignment = Alignment(horizontal="center")
        c3.alignment = Alignment(horizontal="center")
        c3.number_format = "0.0%"

        if label in STATUS_FONTS:
            c1.font = STATUS_FONTS[label]
            c1.fill = STATUS_FILLS[label]
            c2.font = STATUS_FONTS[label]
            c3.font = STATUS_FONTS[label]
        elif label == "Total Evaluaciones":
            c1.font = BOLD_FONT
            c2.font = BOLD_FONT
            c3.font = BOLD_FONT
            c1.fill = LIGHT_GRAY_FILL
            c2.fill = LIGHT_GRAY_FILL
            c3.fill = LIGHT_GRAY_FILL

    # Resumen por Control ISO / Regla IAM
    start_rules_row = 18
    ws_resumen.cell(row=start_rules_row, column=1, value="Desglose por Control ISO/IEC 27001:2022").font = SECTION_FONT

    rules_headers = [
        "Control ISO",
        "Nombre del Control",
        "Regla IAM",
        "Total",
        "Conforme",
        "Hallazgo",
        "No evaluable",
        "Conformidad (%)",
    ]
    for col_idx, h in enumerate(rules_headers, start=1):
        c = ws_resumen.cell(row=start_rules_row + 1, column=col_idx, value=h)
        c.fill = NAVY_HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = Alignment(horizontal="center")
        c.border = GRID_BORDER

    curr_row = start_rules_row + 2
    for r_code in ["IAM-001", "IAM-002", "IAM-003", "IAM-004"]:
        r_data = rules_summary.get(r_code, {})
        row_vals = [
            f"Control {r_data.get('iso_control', '')}",
            r_data.get("control_name", ""),
            r_code,
            r_data.get("total", 0),
            r_data.get("conforme", 0),
            r_data.get("hallazgo", 0),
            r_data.get("no_evaluable", 0),
            (r_data.get("pct_conforme", 0.0)) / 100.0,
        ]
        for col_idx, v in enumerate(row_vals, start=1):
            cell = ws_resumen.cell(row=curr_row, column=col_idx, value=v)
            cell.font = REGULAR_FONT
            cell.border = GRID_BORDER
            if col_idx in (1, 3):
                cell.alignment = Alignment(horizontal="center")
            elif col_idx >= 4:
                cell.alignment = Alignment(horizontal="center")
            if col_idx == 8:
                cell.number_format = "0.0%"
        curr_row += 1

    # Nota técnica / Descargo de responsabilidad
    curr_row += 2
    ws_resumen.cell(row=curr_row, column=1, value="Nota Técnica:").font = BOLD_FONT
    curr_row += 1
    cell_disc = ws_resumen.cell(row=curr_row, column=1, value=metadata.get("disclaimer", ""))
    cell_disc.font = MUTED_FONT
    cell_disc.alignment = Alignment(wrap_text=True)
    ws_resumen.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row + 1, end_column=8)

    _adjust_column_widths(ws_resumen)

    # =========================================================================
    # HOJA 2: EVALUACIONES
    # =========================================================================
    ws_eval = wb.create_sheet(title="Evaluaciones")
    ws_eval.views.sheetView[0].showGridLines = True

    eval_headers = [
        "Identificador del Resultado",
        "Recurso",
        "Tipo de Recurso",
        "Código de Control",
        "Código de Regla",
        "Código de Criterio",
        "Estado",
        "Descripción",
    ]

    for col_idx, h in enumerate(eval_headers, start=1):
        cell = ws_eval.cell(row=1, column=col_idx, value=h)
        cell.fill = NAVY_HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")
        cell.border = GRID_BORDER

    for r_idx, ev in enumerate(evaluations, start=2):
        row_data = [
            ev.get("id"),
            ev.get("resource_key", ""),
            ev.get("resource_type", "IAM_RESOURCE"),
            f"ISO {ev.get('iso_control', '')}",
            ev.get("rule_code", ""),
            ev.get("criterion_code", ""),
            ev.get("result_status", ""),
            ev.get("justification", ""),
        ]
        status_val = ev.get("result_status", "")
        for c_idx, val in enumerate(row_data, start=1):
            cell = ws_eval.cell(row=r_idx, column=c_idx, value=val)
            cell.font = REGULAR_FONT
            cell.border = GRID_BORDER
            if c_idx in (1, 3, 4, 5, 6):
                cell.alignment = Alignment(horizontal="center")
            elif c_idx == 7:
                cell.alignment = Alignment(horizontal="center")
                if status_val in STATUS_FONTS:
                    cell.font = STATUS_FONTS[status_val]
                    cell.fill = STATUS_FILLS[status_val]

    ws_eval.freeze_panes = "A2"
    ws_eval.auto_filter.ref = f"A1:H{max(len(evaluations) + 1, 1)}"
    _adjust_column_widths(ws_eval)

    # =========================================================================
    # HOJA 3: HALLAZGOS
    # =========================================================================
    ws_find = wb.create_sheet(title="Hallazgos")
    ws_find.views.sheetView[0].showGridLines = True

    find_headers = [
        "Identificador",
        "Recurso",
        "Control",
        "Regla",
        "Criterio",
        "Severidad",
        "Descripción",
        "Evidencia disponible",
        "Recomendación Técnica",
    ]

    for col_idx, h in enumerate(find_headers, start=1):
        cell = ws_find.cell(row=1, column=col_idx, value=h)
        cell.fill = NAVY_HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")
        cell.border = GRID_BORDER

    if findings:
        for r_idx, f in enumerate(findings, start=2):
            sev_str = str(f.get("severity", "ALTA")).upper()
            row_data = [
                f.get("id"),
                f.get("resource_key", ""),
                f"ISO {f.get('iso_control', '')}",
                f.get("rule_code", ""),
                f.get("criterion_code", "N/A"),
                sev_str,
                f.get("description", ""),
                f.get("observed_value", ""),
                f.get("recommendation", ""),
            ]
            for c_idx, val in enumerate(row_data, start=1):
                cell = ws_find.cell(row=r_idx, column=c_idx, value=val)
                cell.font = REGULAR_FONT
                cell.border = GRID_BORDER
                if c_idx in (1, 3, 4, 5):
                    cell.alignment = Alignment(horizontal="center")
                elif c_idx == 6:
                    cell.alignment = Alignment(horizontal="center")
                    if sev_str in SEVERITY_FONTS:
                        cell.font = SEVERITY_FONTS[sev_str]
        ws_find.auto_filter.ref = f"A1:I{len(findings) + 1}"
    else:
        # Caso borde: Sin hallazgos
        cell = ws_find.cell(row=2, column=1, value="No se detectaron hallazgos técnicos en esta auditoría.")
        cell.font = MUTED_FONT
        ws_find.merge_cells("A2:I2")

    ws_find.freeze_panes = "A2"
    _adjust_column_widths(ws_find)

    # =========================================================================
    # HOJA 4: EVIDENCIAS
    # =========================================================================
    ws_evi = wb.create_sheet(title="Evidencias")
    ws_evi.views.sheetView[0].showGridLines = True

    evi_headers = [
        "Identificador de Evidencia",
        "Resultado o Hallazgo Asociado",
        "Recurso",
        "Regla",
        "Control ISO",
        "Tipo de Evidencia",
        "Detalle Técnico",
        "Referencia Técnica",
        "Fecha de Captura",
    ]

    for col_idx, h in enumerate(evi_headers, start=1):
        cell = ws_evi.cell(row=1, column=col_idx, value=h)
        cell.fill = NAVY_HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")
        cell.border = GRID_BORDER

    if evidences:
        for r_idx, ev in enumerate(evidences, start=2):
            row_data = [
                ev.get("id"),
                ev.get("target_ref", ""),
                ev.get("resource_key", ""),
                ev.get("rule_code", ""),
                f"ISO {ev.get('iso_control', '')}",
                ev.get("evidence_type", ""),
                ev.get("evidence_detail", ""),
                ev.get("evidence_reference", ""),
                ev.get("captured_at", ""),
            ]
            for c_idx, val in enumerate(row_data, start=1):
                cell = ws_evi.cell(row=r_idx, column=c_idx, value=val)
                cell.font = REGULAR_FONT
                cell.border = GRID_BORDER
                if c_idx in (1, 4, 5, 9):
                    cell.alignment = Alignment(horizontal="center")
        ws_evi.auto_filter.ref = f"A1:I{len(evidences) + 1}"
    else:
        # Caso borde: Sin evidencias
        cell = ws_evi.cell(row=2, column=1, value="No se registraron evidencias técnicas adicionales en esta auditoría.")
        cell.font = MUTED_FONT
        ws_evi.merge_cells("A2:I2")

    ws_evi.freeze_panes = "A2"
    _adjust_column_widths(ws_evi)

    # Guardar archivo
    wb.save(str(path_obj))
    return str(path_obj)

