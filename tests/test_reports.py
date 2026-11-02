"""
Pruebas Automatizadas para la Generación y Exportación de Informes de Auditoría IAM.
Cubre la generación de PDF, Excel (XLSX) y CSV, integridad de datos, trazabilidad histórica,
conservación de los 3 estados, casos borde, caracteres especiales, manejo de errores de I/O,
estricta ausencia de escrituras en MySQL y cero re-ejecución de auditorías.
"""
import ast
import csv
import io
import os
from pathlib import Path
import tempfile
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import openpyxl
import pytest
from PySide6.QtWidgets import QApplication

from src.auditoria_iam.application.audit_service import AuditService
from src.auditoria_iam.audit.engine import AuditEngine
from src.auditoria_iam.audit.models import AuditResult
from src.auditoria_iam.data_sources.simulator.simulator import IAMSimulatorDataSource
from src.auditoria_iam.reports import (
    build_report_data,
    generate_csv_report,
    generate_excel_report,
    generate_pdf_report,
)
from src.auditoria_iam.ui.pages.history_page import HistoryPage
from src.auditoria_iam.ui.pages.results_page import ResultsPage


@pytest.fixture
def sample_audit_data():
    """Genera un lote controlado de resultados en memoria con los tres estados técnicos."""
    results = [
        AuditResult(
            rule_code="IAM-001",
            criterion_code="C15-01",
            resource_id="user_admin",
            result_status="Conforme",
            justification="El usuario cuenta exactamente con los grupos autorizados para su perfil.",
            profile_id=1,
            details={"profile_code": "PROF_ADMIN", "groups": ["Administradores"]},
            evidence={"evidence_type": "membresia_grupos", "groups": ["Administradores"]},
        ),
        AuditResult(
            rule_code="IAM-002",
            criterion_code="C16-02",
            resource_id="user_inactive",
            result_status="Hallazgo",
            justification="Identidad inactiva por 120 días, superando el umbral permitido de 90 días.",
            profile_id=2,
            details={"days_inactive": 120, "severity": "ALTA", "threshold": 90},
            evidence={"evidence_type": "inactividad", "last_activity": "2026-06-01"},
        ),
        AuditResult(
            rule_code="IAM-003",
            criterion_code="C18-01",
            resource_id="role_auditor",
            result_status="No evaluable",
            justification="No se encontró documento de política administrada recuperable.",
            profile_id=None,
            details={"reason": "policy_unfetchable"},
            evidence=None,
        ),
    ]

    resources = [
        {
            "id": 1,
            "resource_key": "user_admin",
            "display_name": "Administrador Principal",
            "resource_type": "USER",
        },
        {
            "id": 2,
            "resource_key": "user_inactive",
            "display_name": "Operador Inactivo",
            "resource_type": "USER",
        },
        {
            "id": 3,
            "resource_key": "role_auditor",
            "display_name": "Rol de Auditoría Externa",
            "resource_type": "ROLE",
        },
    ]

    summary = {
        "total": 3,
        "conforme": 1,
        "hallazgo": 1,
        "no_evaluable": 1,
    }

    return results, resources, summary


# =============================================================================
# PRUEBA 1: Generación de informe PDF
# =============================================================================
def test_pdf_report_generation(sample_audit_data):
    """Verifica que el informe PDF se genere con éxito, no esté vacío y contenga encabezados válidos."""
    results, resources, summary = sample_audit_data
    report_data = build_report_data(results=results, resources=resources, summary=summary)

    with tempfile.TemporaryDirectory() as td:
        pdf_path = os.path.join(td, "informe_test.pdf")
        generated_path = generate_pdf_report(report_data, pdf_path)

        assert os.path.exists(generated_path)
        assert os.path.getsize(generated_path) > 2000  # Archivo sustancial

        # Validar firma estándar de PDF (%PDF)
        with open(generated_path, "rb") as f:
            header = f.read(5)
            assert header.startswith(b"%PDF")


# =============================================================================
# PRUEBA 2: Generación de informe Excel (XLSX)
# =============================================================================
def test_excel_report_generation(sample_audit_data):
    """Verifica que el informe XLSX se genere con éxito y posea las 4 hojas requeridas."""
    results, resources, summary = sample_audit_data
    report_data = build_report_data(results=results, resources=resources, summary=summary)

    with tempfile.TemporaryDirectory() as td:
        xlsx_path = os.path.join(td, "informe_test.xlsx")
        generated_path = generate_excel_report(report_data, xlsx_path)

        assert os.path.exists(generated_path)
        assert os.path.getsize(generated_path) > 1000

        # Cargar con openpyxl y verificar las 4 hojas
        wb = openpyxl.load_workbook(generated_path)
        assert "Resumen" in wb.sheetnames
        assert "Evaluaciones" in wb.sheetnames
        assert "Hallazgos" in wb.sheetnames
        assert "Evidencias" in wb.sheetnames

        # Verificar encabezados en Evaluaciones
        ws_eval = wb["Evaluaciones"]
        assert ws_eval.cell(row=1, column=1).value == "Identificador del Resultado"
        assert ws_eval.cell(row=1, column=7).value == "Estado"
        assert ws_eval.cell(row=2, column=7).value in ("Conforme", "Hallazgo", "No evaluable")


# =============================================================================
# PRUEBA 3: Generación de informe CSV con UTF-8 BOM
# =============================================================================
def test_csv_report_generation(sample_audit_data):
    """Verifica que el informe CSV contenga codificación UTF-8 con BOM y encabezados correctos."""
    results, resources, summary = sample_audit_data
    report_data = build_report_data(results=results, resources=resources, summary=summary)

    with tempfile.TemporaryDirectory() as td:
        csv_path = os.path.join(td, "informe_test.csv")
        generated_path = generate_csv_report(report_data, csv_path)

        assert os.path.exists(generated_path)
        assert os.path.getsize(generated_path) > 0

        # Verificar presencia de BOM utf-8 (\xef\xbb\xbf)
        with open(generated_path, "rb") as f:
            raw_bytes = f.read(3)
            assert raw_bytes == b"\xef\xbb\xbf", "El archivo CSV debe tener BOM UTF-8 para Excel en Windows"

        # Leer con csv.reader y validar encabezados
        with open(generated_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader)
            expected_headers = [
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
            assert header == expected_headers
            rows = list(reader)
            assert len(rows) == 3


# =============================================================================
# PRUEBA 4: Coincidencia exacta de datos entre origen y reporte
# =============================================================================
def test_report_data_matches_audit_results(sample_audit_data):
    """Verifica que los datos normalizados en el reporte coincidan exactamente con la auditoría."""
    results, resources, summary = sample_audit_data
    report_data = build_report_data(results=results, resources=resources, summary=summary)

    assert report_data["summary"]["total"] == 3
    assert report_data["summary"]["conforme"] == 1
    assert report_data["summary"]["hallazgo"] == 1
    assert report_data["summary"]["no_evaluable"] == 1

    # Porcentajes exactos
    assert report_data["summary"]["pct_conforme"] == 33.3
    assert report_data["summary"]["pct_hallazgo"] == 33.3
    assert report_data["summary"]["pct_no_evaluable"] == 33.3

    # Recursos en evaluaciones
    eval_keys = [e["resource_key"] for e in report_data["evaluations"]]
    assert "user_admin" in eval_keys
    assert "user_inactive" in eval_keys
    assert "role_auditor" in eval_keys


# =============================================================================
# PRUEBA 5: Exportación de auditoría histórica
# =============================================================================
def test_historical_run_export():
    """Verifica la exportación correcta de una corrida histórica simulando respuestas de MySQL."""
    service = AuditService()

    mock_run = {
        "id": 42,
        "execution_date": "2026-11-01 10:30:00",
        "source_type": "simulacion",
        "status": "completada",
        "total_findings": 1,
        "summary": "Total: 1 | Conforme: 0 | Hallazgo: 1 | No evaluable: 0",
    }
    mock_results = [
        AuditResult(
            rule_code="IAM-001",
            criterion_code="C15-01",
            resource_id="user_test",
            result_status="Hallazgo",
            justification="Grupo no autorizado asignado.",
            details={"severity": "ALTA"},
            evidence={"evidence_type": "grupo_no_autorizado"},
        )
    ]
    mock_resources = [{"id": 1, "resource_key": "user_test", "display_name": "Test User", "resource_type": "USER"}]
    mock_summary = {"total": 1, "conforme": 0, "hallazgo": 1, "no_evaluable": 0}

    mock_findings = [{
        "id": 10,
        "audit_run_id": 42,
        "resource_id": 1,
        "resource_key": "user_test",
        "rule_code": "IAM-001",
        "iso_control": "5.15",
        "severity": "ALTA",
        "finding_title": "Membresía no autorizada",
        "description": "Grupo no autorizado asignado.",
        "observed_value": '{"groups": ["Sudo"]}',
        "recommendation": "Revocar grupo.",
    }]
    mock_evidences = [{
        "id": 5,
        "finding_id": 10,
        "audit_result_id": None,
        "resource_key": "user_test",
        "rule_code": "IAM-001",
        "iso_control": "5.15",
        "evidence_type": "grupo_no_autorizado",
        "evidence_detail": '{"observed": ["Sudo"]}',
        "evidence_reference": "resource:user_test:C15-01",
        "captured_at": "2026-11-01 10:30:00",
    }]

    with patch("src.auditoria_iam.application.audit_service.get_audit_run_by_id", return_value=mock_run), \
         patch.object(service, "get_historical_run_results", return_value=(mock_results, mock_resources, mock_summary)), \
         patch("src.auditoria_iam.application.audit_service.get_findings_by_run", return_value=mock_findings), \
         patch("src.auditoria_iam.application.audit_service.get_evidence_by_run", return_value=mock_evidences):

        with tempfile.TemporaryDirectory() as td:
            pdf_path = os.path.join(td, "hist_report.pdf")
            out = service.export_audit_report(filepath=pdf_path, format_type="pdf", run_id=42)
            assert os.path.exists(out)

            # Validar reporte en datos normalizados
            data = service.get_audit_report_data(run_id=42)
            assert data["metadata"]["run_id"] == "42"
            assert len(data["findings"]) == 1
            assert data["findings"][0]["severity"] == "ALTA"
            assert len(data["evidences"]) == 1


# =============================================================================
# PRUEBA 6: Conservación estricta de los 3 estados técnicos
# =============================================================================
def test_preservation_of_three_statuses(sample_audit_data):
    """
    Verifica que los tres estados ('Conforme', 'Hallazgo', 'No evaluable') se preserven
    como categorías completamente diferenciadas y que 'No evaluable' no se convierta en 'Conforme'.
    """
    results, resources, summary = sample_audit_data
    report_data = build_report_data(results=results, resources=resources, summary=summary)

    # 1. En datos normalizados
    assert report_data["summary"]["conforme"] == 1
    assert report_data["summary"]["hallazgo"] == 1
    assert report_data["summary"]["no_evaluable"] == 1

    statuses = [e["result_status"] for e in report_data["evaluations"]]
    assert "Conforme" in statuses
    assert "Hallazgo" in statuses
    assert "No evaluable" in statuses
    assert statuses.count("Conforme") == 1
    assert statuses.count("No evaluable") == 1

    # 2. En archivo CSV
    with tempfile.TemporaryDirectory() as td:
        csv_p = os.path.join(td, "test_status.csv")
        generate_csv_report(report_data, csv_p)
        with open(csv_p, mode="r", encoding="utf-8-sig") as f:
            content = f.read()
            assert "Conforme" in content
            assert "Hallazgo" in content
            assert "No evaluable" in content


# =============================================================================
# PRUEBA 7: Caso borde — Auditoría sin hallazgos
# =============================================================================
def test_edge_case_no_findings():
    """Verifica que una auditoría sin hallazgos (100% conformes/no evaluables) exporte sin fallas."""
    results = [
        AuditResult(
            rule_code="IAM-001",
            criterion_code="C15-01",
            resource_id="user_clean",
            result_status="Conforme",
            justification="Todo conforme.",
        ),
        AuditResult(
            rule_code="IAM-004",
            criterion_code="C08-01",
            resource_id="user_clean",
            result_status="Conforme",
            justification="MFA habilitado.",
        ),
    ]
    resources = [{"id": 1, "resource_key": "user_clean", "display_name": "Usuario Limpio", "resource_type": "USER"}]
    summary = {"total": 2, "conforme": 2, "hallazgo": 0, "no_evaluable": 0}

    report_data = build_report_data(results=results, resources=resources, summary=summary)
    assert len(report_data["findings"]) == 0

    with tempfile.TemporaryDirectory() as td:
        # Generar en los 3 formatos
        p_pdf = os.path.join(td, "no_find.pdf")
        p_xlsx = os.path.join(td, "no_find.xlsx")
        p_csv = os.path.join(td, "no_find.csv")

        generate_pdf_report(report_data, p_pdf)
        generate_excel_report(report_data, p_xlsx)
        generate_csv_report(report_data, p_csv)

        assert os.path.exists(p_pdf)
        assert os.path.exists(p_xlsx)
        assert os.path.exists(p_csv)

        # En Excel, verificar mensaje informativo en hoja Hallazgos
        wb = openpyxl.load_workbook(p_xlsx)
        ws_find = wb["Hallazgos"]
        assert "No se detectaron hallazgos técnicos" in str(ws_find["A2"].value)


# =============================================================================
# PRUEBA 8: Caso borde — Auditoría sin evidencias explícitas
# =============================================================================
def test_edge_case_no_evidences():
    """Verifica que una auditoría sin evidencias registradas exporte con normalidad sin excepciones."""
    results = [
        AuditResult(
            rule_code="IAM-001",
            criterion_code="C15-01",
            resource_id="user_simple",
            result_status="Conforme",
            justification="Evaluado sin evidencia adjunta.",
            evidence=None,
        )
    ]
    resources = [{"id": 1, "resource_key": "user_simple", "display_name": "Usuario Simple", "resource_type": "USER"}]
    summary = {"total": 1, "conforme": 1, "hallazgo": 0, "no_evaluable": 0}

    report_data = build_report_data(results=results, resources=resources, summary=summary)
    assert len(report_data["evidences"]) == 0

    with tempfile.TemporaryDirectory() as td:
        p_pdf = os.path.join(td, "no_evi.pdf")
        p_xlsx = os.path.join(td, "no_evi.xlsx")
        p_csv = os.path.join(td, "no_evi.csv")

        generate_pdf_report(report_data, p_pdf)
        generate_excel_report(report_data, p_xlsx)
        generate_csv_report(report_data, p_csv)

        assert os.path.exists(p_pdf)
        assert os.path.exists(p_xlsx)
        assert os.path.exists(p_csv)


# =============================================================================
# PRUEBA 9: Caracteres especiales, acentos y eñes
# =============================================================================
def test_special_characters_and_accents():
    """Verifica que textos con tildes, eñes y caracteres complejos se exporten adecuadamente."""
    complex_text = "Evaluación de configuración: contraseña expirada en «año 2026», ¿acción requerida? ¡Sí!"
    results = [
        AuditResult(
            rule_code="IAM-002",
            criterion_code="C16-01",
            resource_id="usuarió_diseño",
            result_status="Hallazgo",
            justification=complex_text,
            details={"nota": "áéíóúñÁÉÍÓÚÑ"},
            evidence={"detalle": complex_text},
        )
    ]
    resources = [{
        "id": 99,
        "resource_key": "usuarió_diseño",
        "display_name": "Diseñador Gráfico & Administración",
        "resource_type": "USUARIO_ESPECIAL",
    }]
    summary = {"total": 1, "conforme": 0, "hallazgo": 1, "no_evaluable": 0}

    report_data = build_report_data(results=results, resources=resources, summary=summary)

    with tempfile.TemporaryDirectory() as td:
        p_pdf = os.path.join(td, "special.pdf")
        p_xlsx = os.path.join(td, "special.xlsx")
        p_csv = os.path.join(td, "special.csv")

        generate_pdf_report(report_data, p_pdf)
        generate_excel_report(report_data, p_xlsx)
        generate_csv_report(report_data, p_csv)

        # En CSV verificar decodificación exacta
        with open(p_csv, mode="r", encoding="utf-8-sig") as f:
            csv_content = f.read()
            assert "usuarió_diseño" in csv_content
            assert "contraseña expirada" in csv_content
            assert "¡Sí!" in csv_content

        # En XLSX verificar lectura exacta de la celda
        wb = openpyxl.load_workbook(p_xlsx)
        ws_eval = wb["Evaluaciones"]
        assert ws_eval.cell(row=2, column=2).value == "usuarió_diseño"
        assert complex_text in ws_eval.cell(row=2, column=8).value


# =============================================================================
# PRUEBA 10: Manejo de errores de escritura en ruta no válida
# =============================================================================
def test_file_write_error_handling(sample_audit_data):
    """Verifica que el intento de escribir en un directorio protegido o inválido lance excepción controlada."""
    results, resources, summary = sample_audit_data
    service = AuditService()

    invalid_path = "/ruta_imposible_del_sistema/inexistente/informe.pdf"
    if os.name == "nt":
        invalid_path = "Z:\\ruta_imposible_inexistente_12345\\informe.pdf"

    with pytest.raises((OSError, PermissionError)):
        service.export_audit_report(
            filepath=invalid_path,
            format_type="pdf",
            results=results,
            resources=resources,
            summary=summary,
        )


# =============================================================================
# PRUEBA 11: Cero operaciones de escritura en MySQL durante la exportación
# =============================================================================
def test_export_does_not_perform_mysql_writes():
    """
    Verifica mediante análisis estático (AST) y mock del cursor que
    los módulos de reportes no ejecutan ninguna instrucción de modificación en MySQL.
    """
    reports_dir = Path("src/auditoria_iam/reports")
    forbidden_sql_keywords = ["INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "TRUNCATE "]

    for py_file in reports_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8").upper()
        for kw in forbidden_sql_keywords:
            assert kw not in content, f"Se detectó instrucción prohibida de escritura '{kw}' en {py_file.name}"

    # Verificación en tiempo de ejecución de AuditService.export_audit_report
    service = AuditService()
    mock_cursor = MagicMock()

    with patch("src.auditoria_iam.database.connection.get_db_cursor") as mock_get_cursor:
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor

        with tempfile.TemporaryDirectory() as td:
            pdf_path = os.path.join(td, "no_write.pdf")
            service.export_audit_report(
                filepath=pdf_path,
                format_type="pdf",
                results=[],
                resources=[],
                summary={"total": 0, "conforme": 0, "hallazgo": 0, "no_evaluable": 0},
            )

        # Confirmar que si se llamó execute, ninguna llamada fue de escritura
        for call_item in mock_cursor.execute.call_args_list:
            sql_query = str(call_item[0][0]).strip().upper()
            assert not any(sql_query.startswith(kw.strip()) for kw in forbidden_sql_keywords), (
                f"La exportación intentó ejecutar una consulta SQL de modificación: {sql_query}"
            )


# =============================================================================
# PRUEBA 12: Cero re-ejecución de auditorías durante la exportación
# =============================================================================
def test_export_does_not_execute_new_audits(sample_audit_data):
    """
    Verifica que exportar un informe no re-ejecute el motor de auditoría ni
    consulte orígenes de datos externos.
    """
    results, resources, summary = sample_audit_data
    service = AuditService()

    with patch.object(service.engine, "evaluate_all") as mock_engine_all, \
         patch.object(service.engine, "evaluate_resource") as mock_engine_single, \
         patch("src.auditoria_iam.data_sources.simulator.simulator.IAMSimulatorDataSource.get_resources") as mock_sim_res:

        with tempfile.TemporaryDirectory() as td:
            pdf_path = os.path.join(td, "no_reeval.pdf")
            service.export_audit_report(
                filepath=pdf_path,
                format_type="pdf",
                results=results,
                resources=resources,
                summary=summary,
            )

        # Verificar que el motor de evaluación no fue invocado
        mock_engine_all.assert_not_called()
        mock_engine_single.assert_not_called()
        mock_sim_res.assert_not_called()


# =============================================================================
# PRUEBAS DE INTERFAZ: ResultsPage y HistoryPage
# =============================================================================
def test_results_page_export_controls(qapp, sample_audit_data):
    """Verifica que los botones de exportación en ResultsPage se habiliten al cargar datos."""
    results, resources, summary = sample_audit_data
    page = ResultsPage()

    # Inicialmente deshabilitados
    assert not page.btn_export_pdf.isEnabled()
    assert not page.btn_export_excel.isEnabled()
    assert not page.btn_export_csv.isEnabled()

    # Cargar resultados
    page.load_results(results=results, resources=resources, summary=summary, run_id=10)

    # Ahora deben estar habilitados
    assert page.btn_export_pdf.isEnabled()
    assert page.btn_export_excel.isEnabled()
    assert page.btn_export_csv.isEnabled()
    assert page._current_run_id == 10


def test_history_page_export_controls_on_selection(qapp):
    """Verifica que los botones de exportación en HistoryPage se habiliten solo con selección activa."""
    page = HistoryPage()

    # Inicialmente deshabilitados
    assert not page.btn_export_pdf.isEnabled()
    assert not page.btn_export_excel.isEnabled()
    assert not page.btn_export_csv.isEnabled()

    # Simular presencia de filas y selección
    page.history_table.setRowCount(1)
    from PySide6.QtWidgets import QTableWidgetItem
    page.history_table.setItem(0, 0, QTableWidgetItem("#15"))
    page.history_table.selectRow(0)

    # Con selección activa deben habilitarse
    assert page.btn_export_pdf.isEnabled()
    assert page.btn_export_excel.isEnabled()
    assert page.btn_export_csv.isEnabled()
    assert page._get_selected_run_id() == 15
