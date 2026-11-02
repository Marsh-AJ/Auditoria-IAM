"""
Generador de Informes de Auditoría IAM en formato PDF profesional.
Utiliza ReportLab para construir un documento técnico formal con portada/encabezado,
resumen ejecutivo con gráfico de distribución, tablas por control ISO, detalle de
evaluaciones, hallazgos técnicos, evidencias y conclusiones con descargo de responsabilidad.
"""
from pathlib import Path
from typing import Any, Dict, List

from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Colores del sistema de ciberseguridad
COLOR_NAVY_DARK = HexColor("#0F172A")
COLOR_NAVY_SURFACE = HexColor("#1E293B")
COLOR_SLATE_BORDER = HexColor("#334155")
COLOR_SLATE_TEXT = HexColor("#64748B")
COLOR_DARK_TEXT = HexColor("#0F172A")
COLOR_GREEN = HexColor("#16A34A")
COLOR_GREEN_BG = HexColor("#DCFCE7")
COLOR_RED = HexColor("#DC2626")
COLOR_RED_BG = HexColor("#FEE2E2")
COLOR_AMBER = HexColor("#D97706")
COLOR_GRAY = HexColor("#64748B")
COLOR_GRAY_BG = HexColor("#F1F5F9")
COLOR_LIGHT_BG = HexColor("#F8FAFC")


class NumberedCanvas(canvas.Canvas):
    """
    Canvas de doble pasada para calcular el total de páginas dinámicamente
    y dibujar encabezado y pie de página en cada hoja del documento.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_and_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_and_footer(self, total_pages: int) -> None:
        self.saveState()

        # Encabezado para páginas 2 en adelante
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(COLOR_NAVY_DARK)
            self.drawString(36, 762, "AUDITORÍA IAM — UPHARVEN C.A. • ISO/IEC 27001:2022")
            self.setFont("Helvetica", 8)
            self.setFillColor(COLOR_SLATE_TEXT)
            self.drawRightString(576, 762, "INFORME TÉCNICO DE EVALUACIÓN")

            self.setStrokeColor(COLOR_SLATE_BORDER)
            self.setLineWidth(0.5)
            self.line(36, 756, 576, 756)

        # Pie de página para todas las páginas
        self.setStrokeColor(COLOR_SLATE_BORDER)
        self.setLineWidth(0.5)
        self.line(36, 42, 576, 42)

        self.setFont("Helvetica", 8)
        self.setFillColor(COLOR_SLATE_TEXT)
        self.drawString(36, 30, "Documento confidencial — Prototipo académico de auditoría IAM para UPHARVEN C.A.")

        page_str = f"Página {self._pageNumber} de {total_pages}"
        self.drawRightString(576, 30, page_str)

        self.restoreState()


def _build_pie_chart(conforme: int, hallazgo: int, no_evaluable: int, total: int) -> Drawing:
    """Construye un gráfico visual de pastel con leyenda descriptiva usando ReportLab Graphics."""
    d = Drawing(540, 130)

    # Fondo suave para el contenedor del gráfico
    d.add(Rect(0, 0, 540, 130, fillColor=COLOR_LIGHT_BG, strokeColor=COLOR_SLATE_BORDER, strokeWidth=0.5, rx=4, ry=4))

    pct_c = (conforme / total * 100) if total > 0 else 0.0
    pct_h = (hallazgo / total * 100) if total > 0 else 0.0
    pct_n = (no_evaluable / total * 100) if total > 0 else 0.0

    # Gráfico de pastel
    pc = Pie()
    pc.x = 25
    pc.y = 10
    pc.width = 110
    pc.height = 110
    
    # Manejo de caso donde todas las métricas sean cero
    if total == 0:
        pc.data = [1]
        pc.slices[0].fillColor = COLOR_GRAY
        d.add(pc)
        d.add(String(160, 60, "Sin evaluaciones registradas", fontName="Helvetica", fontSize=11, fillColor=COLOR_SLATE_TEXT))
        return d

    pc.data = [conforme, hallazgo, no_evaluable]
    pc.slices[0].fillColor = COLOR_GREEN
    pc.slices[1].fillColor = COLOR_RED
    pc.slices[2].fillColor = COLOR_GRAY
    d.add(pc)

    # Leyenda formal al costado
    legend = Legend()
    legend.x = 160
    legend.y = 95
    legend.dx = 12
    legend.dy = 12
    legend.fontName = "Helvetica-Bold"
    legend.fontSize = 10
    legend.boxAnchor = "nw"
    legend.columnMaximum = 3
    legend.alignment = "right"
    legend.colorNamePairs = [
        (COLOR_GREEN, f"Conforme: {conforme} ({pct_c:.1f}%) — Configuraciones alineadas al estándar"),
        (COLOR_RED, f"Hallazgo: {hallazgo} ({pct_h:.1f}%) — Desviaciones o riesgos técnicos detectados"),
        (COLOR_GRAY, f"No evaluable: {no_evaluable} ({pct_n:.1f}%) — Metadatos incompletos o sin política"),
    ]
    d.add(legend)

    return d


def generate_pdf_report(report_data: Dict[str, Any], output_path: str) -> str:
    """
    Genera un informe formal en PDF a partir de los datos normalizados de auditoría.

    Args:
        report_data: Diccionario estructurado con la información de la auditoría.
        output_path: Ruta destino del archivo .pdf.

    Returns:
        Ruta absoluta del archivo generado.
    """
    path_obj = Path(output_path).resolve()
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    metadata = report_data.get("metadata", {})
    summary = report_data.get("summary", {})
    rules_summary = report_data.get("rules_summary", {})
    evaluations = report_data.get("evaluations", [])
    findings = report_data.get("findings", [])
    evidences = report_data.get("evidences", [])

    # Document setup: Letter size with 36pt (0.5 in) margins -> 540pt printable width
    doc = SimpleDocTemplate(
        str(path_obj),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Estilos tipográficos personalizados
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=white,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=HexColor("#E2E8F0"),
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=COLOR_NAVY_DARK,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=COLOR_NAVY_SURFACE,
        spaceAfter=4,
    )
    cell_bold_style = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=COLOR_DARK_TEXT,
    )
    cell_regular_style = ParagraphStyle(
        "CellRegular",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=COLOR_DARK_TEXT,
    )
    cell_header_style = ParagraphStyle(
        "CellHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=white,
        alignment=1,  # Centered
    )
    cell_status_conforme = ParagraphStyle(
        "StatusConf",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=COLOR_GREEN,
        alignment=1,
    )
    cell_status_hallazgo = ParagraphStyle(
        "StatusHall",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=COLOR_RED,
        alignment=1,
    )
    cell_status_no_eval = ParagraphStyle(
        "StatusNoEval",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=COLOR_GRAY,
        alignment=1,
    )
    disclaimer_style = ParagraphStyle(
        "DisclaimerText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=HexColor("#334155"),
    )

    story: List[Any] = []

    # =========================================================================
    # 1. ENCABEZADO / BANNER INSTITUCIONAL
    # =========================================================================
    header_content = [
        [
            Paragraph("SISTEMA DE AUDITORÍA IAM — INFORME TÉCNICO", title_style),
        ],
        [
            Paragraph(
                f"<b>Proyecto:</b> {metadata.get('project_name')}<br/>"
                f"<b>Organización objetivo:</b> {metadata.get('organization')}  |  "
                f"<b>Estándar de referencia:</b> {metadata.get('standard')}",
                subtitle_style,
            ),
        ],
    ]
    header_table = Table(header_content, colWidths=[540])
    header_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_NAVY_DARK),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    story.append(header_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 2. METADATOS DE EJECUCIÓN
    # =========================================================================
    meta_data = [
        [
            Paragraph("<b>ID de Auditoría:</b>", cell_regular_style),
            Paragraph(str(metadata.get("run_id")), cell_bold_style),
            Paragraph("<b>Fecha y Hora:</b>", cell_regular_style),
            Paragraph(str(metadata.get("execution_date")), cell_bold_style),
        ],
        [
            Paragraph("<b>Fuente de Datos:</b>", cell_regular_style),
            Paragraph(str(metadata.get("source_type")), cell_bold_style),
            Paragraph("<b>Estado de Ejecución:</b>", cell_regular_style),
            Paragraph(str(metadata.get("status", "completada")).capitalize(), cell_bold_style),
        ],
        [
            Paragraph("<b>Recursos Evaluados:</b>", cell_regular_style),
            Paragraph(str(metadata.get("total_resources")), cell_bold_style),
            Paragraph("<b>Alcance Evaluado:</b>", cell_regular_style),
            Paragraph("ISO/IEC 27001 (5.15, 5.16, 5.18, 8.5)", cell_bold_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[110, 160, 110, 160])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # 3. RESUMEN EJECUTIVO Y GRÁFICO DE DISTRIBUCIÓN
    # =========================================================================
    story.append(Paragraph("1. Resumen Ejecutivo de Conformidad", h1_style))

    tot = summary.get("total", len(evaluations))
    conf = summary.get("conforme", 0)
    hall = summary.get("hallazgo", 0)
    no_ev = summary.get("no_evaluable", 0)

    # Tarjetas cuantitativas
    kpi_table_data = [
        [
            Paragraph("Total Evaluaciones", cell_header_style),
            Paragraph("Conforme", cell_header_style),
            Paragraph("Hallazgo", cell_header_style),
            Paragraph("No evaluable", cell_header_style),
        ],
        [
            Paragraph(f"<b>{tot}</b>", ParagraphStyle("KPI_Tot", parent=cell_bold_style, fontSize=12, alignment=1)),
            Paragraph(
                f"<b>{conf}</b><br/><font size=7 color='#16A34A'>({summary.get('pct_conforme', 0.0)}%)</font>",
                cell_status_conforme,
            ),
            Paragraph(
                f"<b>{hall}</b><br/><font size=7 color='#DC2626'>({summary.get('pct_hallazgo', 0.0)}%)</font>",
                cell_status_hallazgo,
            ),
            Paragraph(
                f"<b>{no_ev}</b><br/><font size=7 color='#64748B'>({summary.get('pct_no_evaluable', 0.0)}%)</font>",
                cell_status_no_eval,
            ),
        ],
    ]
    kpi_table = Table(kpi_table_data, colWidths=[135, 135, 135, 135])
    kpi_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_NAVY_SURFACE),
            ("BACKGROUND", (0, 1), (0, 1), COLOR_LIGHT_BG),
            ("BACKGROUND", (1, 1), (1, 1), COLOR_GREEN_BG),
            ("BACKGROUND", (2, 1), (2, 1), COLOR_RED_BG),
            ("BACKGROUND", (3, 1), (3, 1), COLOR_GRAY_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_SLATE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    story.append(kpi_table)
    story.append(Spacer(1, 8))

    # Gráfico de pastel ReportLab
    pie_drawing = _build_pie_chart(conf, hall, no_ev, tot)
    story.append(pie_drawing)
    story.append(Spacer(1, 14))

    # =========================================================================
    # 4. DESGLOSE POR CONTROL ISO/IEC 27001:2022
    # =========================================================================
    story.append(Paragraph("2. Resultados por Control ISO/IEC 27001:2022", h1_style))

    ctrl_headers = [
        Paragraph("Control", cell_header_style),
        Paragraph("Nombre del Control", cell_header_style),
        Paragraph("Regla", cell_header_style),
        Paragraph("Total", cell_header_style),
        Paragraph("Conforme", cell_header_style),
        Paragraph("Hallazgo", cell_header_style),
        Paragraph("No eval.", cell_header_style),
        Paragraph("% Conf.", cell_header_style),
    ]
    ctrl_rows = [ctrl_headers]

    for r_code in ["IAM-001", "IAM-002", "IAM-003", "IAM-004"]:
        r_info = rules_summary.get(r_code, {})
        ctrl_rows.append([
            Paragraph(f"<b>{r_info.get('iso_control')}</b>", cell_bold_style),
            Paragraph(r_info.get("control_name", ""), cell_regular_style),
            Paragraph(r_code, cell_bold_style),
            Paragraph(str(r_info.get("total", 0)), cell_regular_style),
            Paragraph(str(r_info.get("conforme", 0)), cell_status_conforme),
            Paragraph(str(r_info.get("hallazgo", 0)), cell_status_hallazgo),
            Paragraph(str(r_info.get("no_evaluable", 0)), cell_status_no_eval),
            Paragraph(f"<b>{r_info.get('pct_conforme', 0.0):.1f}%</b>", cell_bold_style),
        ])

    ctrl_table = Table(ctrl_rows, colWidths=[45, 175, 55, 45, 55, 55, 55, 55])
    ctrl_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_NAVY_SURFACE),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("ALIGN", (2, 1), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    story.append(ctrl_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # 5. TABLA DETALLADA DE EVALUACIONES TÉCNICAS
    # =========================================================================
    story.append(Paragraph("3. Detalle de Evaluaciones Técnicas Individuales", h1_style))

    eval_headers_pdf = [
        Paragraph("Recurso Auditado", cell_header_style),
        Paragraph("Tipo", cell_header_style),
        Paragraph("Regla", cell_header_style),
        Paragraph("Criterio", cell_header_style),
        Paragraph("Control", cell_header_style),
        Paragraph("Estado", cell_header_style),
        Paragraph("Descripción / Justificación Técnica", cell_header_style),
    ]
    eval_table_rows = [eval_headers_pdf]

    for ev in evaluations:
        status_str = ev.get("result_status", "")
        if status_str == "Conforme":
            st_p = Paragraph("Conforme", cell_status_conforme)
        elif status_str == "Hallazgo":
            st_p = Paragraph("Hallazgo", cell_status_hallazgo)
        else:
            st_p = Paragraph("No evaluable", cell_status_no_eval)

        eval_table_rows.append([
            Paragraph(f"<b>{ev.get('resource_key', '')}</b>", cell_regular_style),
            Paragraph(ev.get("resource_type", "IAM_RESOURCE"), cell_regular_style),
            Paragraph(ev.get("rule_code", ""), cell_bold_style),
            Paragraph(ev.get("criterion_code", ""), cell_regular_style),
            Paragraph(f"ISO {ev.get('iso_control', '')}", cell_regular_style),
            st_p,
            Paragraph(ev.get("justification", ""), cell_regular_style),
        ])

    eval_table = Table(eval_table_rows, colWidths=[90, 55, 45, 45, 40, 65, 200], repeatRows=1)
    eval_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_NAVY_SURFACE),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 1), (5, -1), "CENTER"),
        ])
    )
    story.append(eval_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # 6. SECCIÓN DE HALLAZGOS TÉCNICOS
    # =========================================================================
    story.append(Paragraph("4. Hallazgos Técnicos de Seguridad", h1_style))

    if findings:
        for f in findings:
            sev_str = str(f.get("severity", "ALTA")).upper()
            sev_color = COLOR_RED if sev_str in ("CRÍTICA", "ALTA") else (COLOR_AMBER if sev_str == "MEDIA" else COLOR_GRAY)

            f_card = [
                [
                    Paragraph(f"<b>{f.get('finding_title')}</b>", ParagraphStyle("F_Title", parent=cell_bold_style, textColor=COLOR_NAVY_DARK)),
                    Paragraph(f"<b>SEVERIDAD {sev_str}</b>", ParagraphStyle("F_Sev", parent=cell_bold_style, textColor=sev_color, alignment=2)),
                ],
                [
                    Paragraph(
                        f"<b>Recurso:</b> {f.get('resource_key')} ({f.get('display_name')})  |  "
                        f"<b>Control:</b> ISO {f.get('iso_control')}  |  "
                        f"<b>Regla:</b> {f.get('rule_code')}  |  "
                        f"<b>Criterio:</b> {f.get('criterion_code', 'N/A')}",
                        cell_regular_style,
                    ),
                    Paragraph("", cell_regular_style),
                ],
                [
                    Paragraph(f"<b>Descripción:</b> {f.get('description')}", cell_regular_style),
                    Paragraph("", cell_regular_style),
                ],
                [
                    Paragraph(f"<b>Evidencia o referencia disponible:</b> <font color='#475569'>{f.get('observed_value')}</font>", cell_regular_style),
                    Paragraph("", cell_regular_style),
                ],
                [
                    Paragraph(f"<b>Recomendación técnica:</b> <font color='#0F172A'><b>{f.get('recommendation')}</b></font>", cell_regular_style),
                    Paragraph("", cell_regular_style),
                ],
            ]
            t_fcard = Table(f_card, colWidths=[420, 120])
            t_fcard.setStyle(
                TableStyle([
                    ("SPAN", (0, 1), (1, 1)),
                    ("SPAN", (0, 2), (1, 2)),
                    ("SPAN", (0, 3), (1, 3)),
                    ("SPAN", (0, 4), (1, 4)),
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                    ("BOX", (0, 0), (-1, -1), 0.5, COLOR_SLATE_BORDER),
                    ("LINEBEFORE", (0, 0), (0, -1), 3.0, sev_color),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ])
            )
            story.append(KeepTogether(t_fcard))
            story.append(Spacer(1, 8))
    else:
        no_find_table = Table([[
            Paragraph("✓ No se detectaron hallazgos técnicos en las identidades y accesos evaluados.", cell_bold_style)
        ]], colWidths=[540])
        no_find_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_GREEN_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_GREEN),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ])
        )
        story.append(no_find_table)

    story.append(Spacer(1, 14))

    # =========================================================================
    # 7. SECCIÓN DE EVIDENCIAS TÉCNICAS
    # =========================================================================
    story.append(Paragraph("5. Evidencias Técnicas Recopiladas", h1_style))

    if evidences:
        evi_header_pdf = [
            Paragraph("ID", cell_header_style),
            Paragraph("Destino / Ref.", cell_header_style),
            Paragraph("Recurso", cell_header_style),
            Paragraph("Regla", cell_header_style),
            Paragraph("Tipo Evidencia", cell_header_style),
            Paragraph("Detalle Técnico / Registro", cell_header_style),
        ]
        evi_rows = [evi_header_pdf]
        for ev in evidences:
            evi_rows.append([
                Paragraph(str(ev.get("id")), cell_regular_style),
                Paragraph(ev.get("target_ref", ""), cell_regular_style),
                Paragraph(ev.get("resource_key", ""), cell_bold_style),
                Paragraph(ev.get("rule_code", ""), cell_regular_style),
                Paragraph(ev.get("evidence_type", ""), cell_regular_style),
                Paragraph(ev.get("evidence_detail", ""), cell_regular_style),
            ])
        evi_table = Table(evi_rows, colWidths=[30, 85, 85, 45, 95, 200], repeatRows=1)
        evi_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_NAVY_SURFACE),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_SLATE_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("ALIGN", (3, 1), (3, -1), "CENTER"),
            ])
        )
        story.append(evi_table)
    else:
        no_evi_table = Table([[
            Paragraph("ℹ No se registraron evidencias técnicas adicionales en esta ejecución.", cell_regular_style)
        ]], colWidths=[540])
        no_evi_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_SLATE_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ])
        )
        story.append(no_evi_table)

    story.append(Spacer(1, 14))

    # =========================================================================
    # 8. CONCLUSIONES TÉCNICAS Y DESCARGO DE RESPONSABILIDAD
    # =========================================================================
    conclusions_content = [
        [
            Paragraph("<b>6. Conclusiones Técnicas y Alcance del Dictamen</b>", h2_style),
        ],
        [
            Paragraph(
                "El presente informe refleja exclusivamente los resultados de una evaluación técnica "
                "algorítmica y automatizada sobre configuraciones de identidades y accesos (IAM) en la nube, "
                "contrastadas frente a los perfiles autorizados y los controles seleccionados del estándar "
                "ISO/IEC 27001:2022 (5.15, 5.16, 5.18 y 8.5).<br/><br/>"
                "<b>Aclaración de alcance:</b> El sistema constituye una herramienta de apoyo para la auditoría técnica "
                "de AWS IAM, limitada a los controles y criterios técnicos implementados. Este análisis no afirma que los "
                "resultados representen una certificación formal de cumplimiento organizacional bajo ISO/IEC 27001 ni una "
                "auditoría integral de tercera parte. Refleja el estado lógico de los controles implementados en los recursos "
                "analizados a la fecha de corte. Se recomienda a la administración de UPHARVEN C.A. priorizar el tratamiento "
                "de los hallazgos calificados como Críticos y Altos a fin de mitigar riesgos de privilegios excesivos "
                "y asegurar la vigencia adecuada del inventario de identidades.",
                disclaimer_style,
            ),
        ],
    ]
    conclusions_table = Table(conclusions_content, colWidths=[540])
    conclusions_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_SLATE_BORDER),
            ("LINEBEFORE", (0, 0), (0, -1), 3.0, COLOR_NAVY_DARK),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    story.append(KeepTogether(conclusions_table))

    # Construir PDF con NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return str(path_obj)

