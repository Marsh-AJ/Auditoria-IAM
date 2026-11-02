"""
Suite de pruebas automatizadas para la Entrega 6.1: Dashboard y Catálogo de Controles ISO/IEC 27001:2022.
Verifica:
1. Carga correcta de indicadores KPI (total, conforme, hallazgo, no evaluable).
2. Cálculo preciso de cantidades y porcentajes en la distribución de resultados.
3. Distribución correcta y granular por regla técnica (IAM-001 a IAM-004).
4. Actualización bajo demanda mediante botón de refresco sin ejecutar nuevas auditorías.
5. Comportamiento defensivo cuando no existen auditorías previas registradas.
6. Manejo resiliente de fallos cuando MySQL no está disponible (sin colapsos ni datos ficticios).
7. Ausencia total de operaciones de escritura (INSERT, UPDATE, DELETE) desde el dashboard.
8. Integración ergonómica con la navegación existente (hacia Resultados e Historial).
9. Apertura y contenido de la vista detallada para los cuatro controles ISO/IEC 27001.
10. Correspondencia unívoca entre cada control ISO y su regla técnica IAM.
11. Apertura segura del enlace externo a la norma ISO/IEC 27001 en Internet Archive.
12. Exactitud y correspondencia de los criterios C16-01 y C16-02 con RuleIAM002IdentityManagement.
13. Ausencia de atribución de carácter «oficial» al documento en Internet Archive.
"""
import inspect
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication

from src.auditoria_iam.application.audit_service import AuditService
from src.auditoria_iam.audit.models import AuditResult
from src.auditoria_iam.ui.controls_catalog import (
    EXTERNAL_ISO_URL,
    ISO_CONTROLS_DETAILS,
    get_all_controls,
    get_control_detail,
)
from src.auditoria_iam.ui.dialogs.control_detail_dialog import IsoControlDetailDialog
from src.auditoria_iam.ui.main_window import MainWindow
from src.auditoria_iam.ui.pages.home_page import HomePage


@pytest.fixture
def mock_dashboard_payload():
    """Genera un lote controlado de datos agregados del dashboard."""
    return {
        "has_data": True,
        "latest_run": {
            "id": 42,
            "execution_date": "2026-11-01 20:30:00",
            "source_type": "simulacion",
            "status": "completada",
            "total_findings": 6,
            "summary": "Total: 67 | Conforme: 36 | Hallazgo: 6 | No evaluable: 25",
        },
        "summary": {
            "total": 67,
            "conforme": 36,
            "hallazgo": 6,
            "no_evaluable": 25,
        },
        "distribution": {
            "conforme": {"count": 36, "percentage": 53.7},
            "hallazgo": {"count": 6, "percentage": 9.0},
            "no_evaluable": {"count": 25, "percentage": 37.3},
        },
        "rules_summary": {
            "IAM-001": {"conforme": 15, "hallazgo": 2, "no_evaluable": 3, "total": 20, "iso_control": "5.15"},
            "IAM-002": {"conforme": 10, "hallazgo": 1, "no_evaluable": 9, "total": 20, "iso_control": "5.16"},
            "IAM-003": {"conforme": 8, "hallazgo": 2, "no_evaluable": 7, "total": 17, "iso_control": "5.18"},
            "IAM-004": {"conforme": 3, "hallazgo": 1, "no_evaluable": 6, "total": 10, "iso_control": "8.5"},
        },
        "run_id": 42,
        "results": [],
        "resources": [],
    }


# =============================================================================
# 1. PRUEBAS DE INDICADORES PRINCIPALES Y DISTRIBUCIÓN
# =============================================================================

def test_dashboard_indicators_load_correctly(qapp, mock_dashboard_payload):
    """1. Verifica que los 4 KPIs principales carguen valores reales y dinámicos."""
    mock_service = MagicMock(spec=AuditService)
    mock_service.get_dashboard_data.return_value = mock_dashboard_payload

    home_page = HomePage(audit_service=mock_service)

    assert home_page.lbl_kpi_total.text() == "67"
    assert home_page.lbl_kpi_conforme.text() == "36"
    assert home_page.lbl_kpi_hallazgo.text() == "6"
    assert home_page.lbl_kpi_no_evaluable.text() == "25"

    # Verificar datos de última auditoría
    assert home_page.lbl_run_id.text() == "#42"
    assert "2026-11-01" in home_page.lbl_run_date.text()
    assert home_page.lbl_run_source.text() == "Simulacion"
    assert home_page.lbl_run_status.text() == "Completada"
    assert home_page.lbl_run_findings.text() == "6"
    assert home_page.btn_view_results.isEnabled()


def test_dashboard_quantities_and_percentages_calculation(qapp):
    """2. Verifica el cálculo riguroso de cantidades y porcentajes en AuditService y el desglose visual."""
    service = AuditService()

    mock_runs = [{"id": 1, "execution_date": "2026-11-01", "source_type": "simulacion", "status": "completada", "total_findings": 1}]
    # 2 conforme, 1 hallazgo, 1 no evaluable -> Total 4 (50%, 25%, 25%)
    mock_results = [
        AuditResult("IAM-001", "C15-01", 1, "Conforme", "OK"),
        AuditResult("IAM-002", "C16-01", 1, "Conforme", "OK"),
        AuditResult("IAM-003", "C18-01", 1, "Hallazgo", "Permiso excesivo"),
        AuditResult("IAM-004", "C85-01", 1, "No evaluable", "Incompleto"),
    ]
    mock_resources = [{"id": 1, "resource_key": "user.test"}]
    mock_summary = {"total": 4, "conforme": 2, "hallazgo": 1, "no_evaluable": 1}

    with patch.object(service, "get_audit_history", return_value=mock_runs), \
         patch.object(service, "get_historical_run_results", return_value=(mock_results, mock_resources, mock_summary)):

        data = service.get_dashboard_data()
        assert data["has_data"] is True
        assert data["summary"]["total"] == 4
        assert data["distribution"]["conforme"]["count"] == 2
        assert data["distribution"]["conforme"]["percentage"] == 50.0
        assert data["distribution"]["hallazgo"]["count"] == 1
        assert data["distribution"]["hallazgo"]["percentage"] == 25.0
        assert data["distribution"]["no_evaluable"]["count"] == 1
        assert data["distribution"]["no_evaluable"]["percentage"] == 25.0

    # Comprobar reflejo en HomePage
    mock_service = MagicMock(spec=AuditService)
    mock_service.get_dashboard_data.return_value = data
    home_page = HomePage(audit_service=mock_service)

    assert "2 (50.0%)" in home_page.badge_dist_conforme.text()
    assert "1 (25.0%)" in home_page.badge_dist_hallazgo.text()
    assert "1 (25.0%)" in home_page.badge_dist_no_eval.text()
    assert not home_page.chart_view.isHidden()


def test_dashboard_rule_distribution_summary(qapp, mock_dashboard_payload):
    """3. Verifica que el resumen por regla presente los conteos exactos de audit_results."""
    mock_service = MagicMock(spec=AuditService)
    mock_service.get_dashboard_data.return_value = mock_dashboard_payload

    home_page = HomePage(audit_service=mock_service)

    # IAM-001
    assert home_page.rule_widgets["IAM-001"]["conforme"].text() == "Conf: 15"
    assert home_page.rule_widgets["IAM-001"]["hallazgo"].text() == "Hall: 2"
    assert home_page.rule_widgets["IAM-001"]["no_evaluable"].text() == "NoEv: 3"

    # IAM-002
    assert home_page.rule_widgets["IAM-002"]["conforme"].text() == "Conf: 10"
    assert home_page.rule_widgets["IAM-002"]["hallazgo"].text() == "Hall: 1"

    # IAM-003
    assert home_page.rule_widgets["IAM-003"]["conforme"].text() == "Conf: 8"
    assert home_page.rule_widgets["IAM-003"]["hallazgo"].text() == "Hall: 2"

    # IAM-004
    assert home_page.rule_widgets["IAM-004"]["conforme"].text() == "Conf: 3"
    assert home_page.rule_widgets["IAM-004"]["hallazgo"].text() == "Hall: 1"


def test_dashboard_refresh_button_updates_data(qapp, mock_dashboard_payload):
    """4. Verifica que el botón de actualizar invoque la consulta sin ejecutar nueva auditoría."""
    mock_service = MagicMock(spec=AuditService)
    mock_service.get_dashboard_data.return_value = mock_dashboard_payload

    home_page = HomePage(audit_service=mock_service)
    initial_calls = mock_service.get_dashboard_data.call_count

    # Pulsar botón de refrescar
    home_page.btn_refresh.click()

    assert mock_service.get_dashboard_data.call_count == initial_calls + 1
    # Asegurar que run_simulated_audit NO fue invocado
    assert not hasattr(mock_service.run_simulated_audit, "call_count") or mock_service.run_simulated_audit.call_count == 0


def test_dashboard_behavior_when_no_audits_exist(qapp):
    """5. Verifica el comportamiento cuando no existen auditorías previas registradas."""
    mock_service = MagicMock(spec=AuditService)
    mock_service.get_dashboard_data.return_value = {
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

    home_page = HomePage(audit_service=mock_service)

    assert "No hay ejecuciones registradas" in home_page.banner_text.text()
    assert home_page.lbl_kpi_total.text() == "0"
    assert home_page.lbl_run_id.text() == "—"
    assert not home_page.btn_view_results.isEnabled()
    assert not home_page.lbl_chart_empty.isHidden()
    assert home_page.chart_view.isHidden()


def test_dashboard_behavior_when_mysql_unavailable(qapp):
    """6. Verifica el manejo defensivo cuando la base de datos MySQL no responde."""
    mock_service = MagicMock(spec=AuditService)
    mock_service.get_dashboard_data.side_effect = RuntimeError("Conexión rechazada: 2003 Can't connect to MySQL")

    home_page = HomePage(audit_service=mock_service)

    assert "No se pudo conectar a la base de datos MySQL" in home_page.banner_text.text()
    assert "RuntimeError" in home_page.banner_text.text()
    assert home_page.last_error is not None
    assert "2003" in home_page.last_error

    # Evitar mostrar datos inventados o antiguos como actuales
    assert home_page.lbl_kpi_total.text() == "—"
    assert home_page.lbl_run_id.text() == "—"
    assert not home_page.btn_view_results.isEnabled()
    assert not home_page.chart_view.isVisible()


def test_dashboard_strictly_no_write_operations():
    """7. Verifica mediante análisis de código que el dashboard no contenga sentencias de escritura."""
    import src.auditoria_iam.ui.pages.home_page as hp_mod

    forbidden = ["INSERT INTO", "UPDATE ", "DELETE FROM", "DROP TABLE", "ALTER TABLE", "TRUNCATE "]
    source = inspect.getsource(hp_mod)

    for word in forbidden:
        assert word not in source.upper(), f"Violación de seguridad: Sentencia prohibida '{word}' detectada en home_page."


# =============================================================================
# 2. PRUEBAS DE NAVEGACIÓN E INTEGRACIÓN CON LA VENTANA PRINCIPAL
# =============================================================================

def test_dashboard_navigation_integration(qapp, mock_dashboard_payload):
    """8. Verifica la integración con MainWindow para ver resultados e historial desde el dashboard."""
    main_window = MainWindow()

    with patch.object(main_window.home_page._audit_service, "get_dashboard_data", return_value=mock_dashboard_payload):
        main_window.home_page.refresh_dashboard()

        # Comprobar navegación hacia Resultados al pulsar ver resultados de la auditoría 42
        with patch.object(main_window.audit_page._audit_service, "get_historical_run_results", return_value=([], [], {"total": 0})):
            main_window.home_page.btn_view_results.click()
            # Debe haber navegado a ResultsPage (índice 2)
            assert main_window.stacked_widget.currentIndex() == 2

        # Comprobar navegación hacia Historial al pulsar ver historial
        main_window.home_page.btn_view_history.click()
        assert main_window.stacked_widget.currentIndex() == 3

        # Comprobar que al regresar a Inicio (índice 0), se refresca el dashboard
        with patch.object(main_window.home_page, "refresh_dashboard") as mock_ref:
            main_window._on_navigate(0)
            mock_ref.assert_called_once()


# =============================================================================
# 3. PRUEBAS DEL CATÁLOGO INTERACTIVO DE CONTROLES ISO/IEC 27001:2022
# =============================================================================

def test_open_control_detail_dialog_for_all_four_controls(qapp):
    """9. Verifica la apertura y contenido de la vista de detalle para los 4 controles ISO."""
    expected_controls = ["5.15", "5.16", "5.18", "8.5"]

    for code in expected_controls:
        data = get_control_detail(code)
        assert data is not None, f"El control {code} no existe en el catálogo."

        dialog = IsoControlDetailDialog(control_code=code)

        # 1. Título y referencia
        assert code in dialog.windowTitle()
        assert "ISO/IEC 27001:2022" in dialog.windowTitle()

        # 2. Secciones obligatorias
        assert len(data.get("summary", "")) > 20
        assert len(data.get("security_objective", "")) > 20
        assert len(data.get("technical_aspect", "")) > 20
        assert len(data.get("verification_criteria", [])) >= 1

        # 3. Interpretación de estados
        meanings = data.get("status_meanings", {})
        assert "Conforme" in meanings
        assert "Hallazgo" in meanings
        assert "No evaluable" in meanings

        # 4. Limitación de alcance y advertencia sobre certificación
        scope_notice = data.get("scope_notice", "")
        assert "certificación" in scope_notice.lower() or "limit" in scope_notice.lower()


def test_iso_controls_and_iam_rules_correspondence():
    """10. Verifica la correspondencia formal y unívoca entre controles ISO y reglas IAM."""
    expected_mapping = {
        "5.15": "IAM-001",
        "5.16": "IAM-002",
        "5.18": "IAM-003",
        "8.5": "IAM-004",
    }

    all_controls = get_all_controls()
    assert len(all_controls) == 4

    for ctrl in all_controls:
        code = ctrl["code"]
        assert code in expected_mapping
        assert ctrl["rule_code"] == expected_mapping[code]


def test_external_iso_document_access(qapp):
    """11. Verifica que la opción de consultar la norma abra de forma segura el enlace en Internet Archive."""
    mock_service = MagicMock(spec=AuditService)
    mock_service.get_dashboard_data.return_value = {"has_data": False}

    home_page = HomePage(audit_service=mock_service)

    with patch("src.auditoria_iam.ui.pages.home_page.QDesktopServices.openUrl") as mock_open:
        home_page.btn_open_iso_doc.click()

        mock_open.assert_called_once()
        called_url: QUrl = mock_open.call_args[0][0]
        assert isinstance(called_url, QUrl)
        assert called_url == QUrl(EXTERNAL_ISO_URL)
        assert "archive.org" in called_url.toString()
        assert "Standard.pdf" in called_url.toString()


def test_control_516_criteria_and_status_meanings_exact_match():
    """12. Verifica que C16-01 y C16-02 coincidan exactamente con la implementación de RuleIAM002."""
    data_516 = get_control_detail("5.16")
    assert data_516 is not None

    criteria = dict(data_516["verification_criteria"])
    assert "C16-01" in criteria
    assert "C16-02" in criteria

    c16_01_text = criteria["C16-01"]
    assert "resource_status" in c16_01_text
    assert "inactivas" in c16_01_text or "deshabilitadas" in c16_01_text
    assert "desprovisionamiento" in c16_01_text
    assert "No evaluable" in c16_01_text

    c16_02_text = criteria["C16-02"]
    assert "metadatos normalizados" in c16_02_text
    assert "90 días" in c16_02_text
    # No debe describir como evaluación directa de password_last_used y access_keys_last_used
    assert "password_last_used" not in c16_02_text
    assert "access_keys_last_used" not in c16_02_text

    # Significados de estado deben reflejar ambos criterios
    meanings = data_516["status_meanings"]
    assert "C16-01" in meanings["Conforme"] and "C16-02" in meanings["Conforme"]
    assert "C16-01" in meanings["Hallazgo"] and "C16-02" in meanings["Hallazgo"]
    assert "C16-01" in meanings["No evaluable"] and "C16-02" in meanings["No evaluable"]


def test_external_iso_pdf_not_called_oficial():
    """13. Verifica que no se atribuya carácter de «oficial» al documento o sitio de Internet Archive."""
    import src.auditoria_iam.ui.controls_catalog as cc_mod
    import src.auditoria_iam.ui.pages.home_page as hp_mod

    cc_source = inspect.getsource(cc_mod)
    hp_source = inspect.getsource(hp_mod)

    # Verificar en controls_catalog
    assert "enlace externo oficial" not in cc_source.lower()
    assert "documento oficial" not in cc_source.lower()
    assert "sitio oficial" not in cc_source.lower()

    # Verificar en home_page
    assert "documento pdf oficial" not in hp_source.lower()
    assert "sitio oficial" not in hp_source.lower()

