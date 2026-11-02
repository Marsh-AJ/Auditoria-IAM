"""
Pruebas automatizadas de integración y validación del Dashboard con el Historial de Auditorías.
Fase 6 — Entrega 6.3.
Verifica:
1. Correspondencia estricta entre indicadores y resultados de una ejecución.
2. Suma coherente de estados (conforme + hallazgo + no_evaluable == total) y cálculo de porcentajes.
3. Identificación y presentación de la última auditoría registrada (5 metadatos).
4. Ausencia absoluta de mezcla de datos entre ejecuciones distintas.
5. Actualización en los cuatro momentos clave del ciclo de vida de la aplicación.
6. Casos especiales: sin datos, auditoría única, auditoría sin hallazgos, fuentes mixtas y fallos de BD.
7. Cumplimiento de restricciones de solo lectura (cero modificaciones en MySQL).
"""
from unittest.mock import MagicMock, patch
import pytest

from PySide6.QtCore import Qt

from src.auditoria_iam.application.audit_service import AuditService
from src.auditoria_iam.audit.models import AuditResult
from src.auditoria_iam.database.repository import get_audit_runs
from src.auditoria_iam.ui.main_window import MainWindow
from src.auditoria_iam.ui.pages.home_page import HomePage


# =============================================================================
# FIXTURES DE APOYO
# =============================================================================

@pytest.fixture
def mock_service():
    """Crea una instancia de AuditService con mocks para pruebas aisladas."""
    return AuditService()


# =============================================================================
# 1. CONSISTENCIA DE INDICADORES Y CÁLCULO DE PORCENTAJES (3.1)
# =============================================================================

def test_indicator_consistency_and_sums(qapp):
    """Verifica que total == conforme + hallazgo + no_evaluable y que los KPIs de HomePage coincidan."""
    page = HomePage()
    try:
        sample_results = [
            AuditResult("IAM-001", "C15-01", "usr_1", "Conforme", "Justificación válida 1"),
            AuditResult("IAM-001", "C15-02", "usr_2", "Conforme", "Justificación válida 2"),
            AuditResult("IAM-002", "C16-01", "usr_3", "Hallazgo", "Justificación válida 3"),
            AuditResult("IAM-003", "C18-01", "usr_4", "No evaluable", "Justificación válida 4"),
            AuditResult("IAM-004", "C85-01", "usr_5", "Conforme", "Justificación válida 5"),
        ]

        mock_payload = {
            "has_data": True,
            "latest_run": {
                "id": 99,
                "execution_date": "2026-11-02 10:00:00",
                "source_type": "simulacion",
                "status": "completada",
                "total_findings": 1,
            },
            "summary": {"total": 5, "conforme": 3, "hallazgo": 1, "no_evaluable": 1},
            "distribution": {
                "conforme": {"count": 3, "percentage": 60.0},
                "hallazgo": {"count": 1, "percentage": 20.0},
                "no_evaluable": {"count": 1, "percentage": 20.0},
            },
            "rules_summary": {
                "IAM-001": {"conforme": 2, "hallazgo": 0, "no_evaluable": 0, "total": 2, "iso_control": "5.15"},
                "IAM-002": {"conforme": 0, "hallazgo": 1, "no_evaluable": 0, "total": 1, "iso_control": "5.16"},
                "IAM-003": {"conforme": 0, "hallazgo": 0, "no_evaluable": 1, "total": 1, "iso_control": "5.18"},
                "IAM-004": {"conforme": 1, "hallazgo": 0, "no_evaluable": 0, "total": 1, "iso_control": "8.5"},
            },
            "results": sample_results,
            "resources": [],
        }

        with patch.object(page._audit_service, "get_dashboard_data", return_value=mock_payload):
            page.refresh_dashboard()

            # Comprobar que la suma de los tres estados coincide con el total
            total = int(page.lbl_kpi_total.text())
            conf = int(page.lbl_kpi_conforme.text())
            hall = int(page.lbl_kpi_hallazgo.text())
            noev = int(page.lbl_kpi_no_evaluable.text())

            assert total == conf + hall + noev
            assert total == 5
            assert conf == 3
            assert hall == 1
            assert noev == 1

            # Comprobar etiquetas de porcentaje en distribución
            assert "60.0%" in page.badge_dist_conforme.text()
            assert "20.0%" in page.badge_dist_hallazgo.text()
            assert "20.0%" in page.badge_dist_no_eval.text()
    finally:
        page.close()
        page.deleteLater()


def test_percentage_calculations_and_zero_division(mock_service):
    """Comprueba el cálculo de porcentajes con un decimal y el caso seguro cuando total == 0."""
    # Caso 1: División con decimal periódico redondeado a 1 decimal
    with patch.object(mock_service, "get_audit_history", return_value=[{"id": 1, "execution_date": "2026-11-01"}]):
        with patch.object(
            mock_service,
            "get_historical_run_results",
            return_value=(
                [
                    AuditResult("IAM-001", "C15-01", "u1", "Conforme", "Válido"),
                    AuditResult("IAM-001", "C15-02", "u2", "Hallazgo", "Fallo"),
                    AuditResult("IAM-002", "C16-01", "u3", "Conforme", "Válido"),
                ],
                [],
                {"total": 3, "conforme": 2, "hallazgo": 1, "no_evaluable": 0},
            ),
        ):
            data = mock_service.get_dashboard_data()
            assert data["has_data"] is True
            # 2/3 = 66.7%
            assert data["distribution"]["conforme"]["percentage"] == 66.7
            # 1/3 = 33.3%
            assert data["distribution"]["hallazgo"]["percentage"] == 33.3
            assert data["distribution"]["no_evaluable"]["percentage"] == 0.0

    # Caso 2: Total 0 no genera ZeroDivisionError y reporta 0.0%
    with patch.object(mock_service, "get_audit_history", return_value=[{"id": 2, "execution_date": "2026-11-01"}]):
        with patch.object(
            mock_service,
            "get_historical_run_results",
            return_value=([], [], {"total": 0, "conforme": 0, "hallazgo": 0, "no_evaluable": 0}),
        ):
            data = mock_service.get_dashboard_data()
            assert data["has_data"] is True
            assert data["distribution"]["conforme"]["percentage"] == 0.0
            assert data["distribution"]["hallazgo"]["percentage"] == 0.0
            assert data["distribution"]["no_evaluable"]["percentage"] == 0.0


# =============================================================================
# 2. IDENTIFICACIÓN DE LA ÚLTIMA AUDITORÍA (3.2)
# =============================================================================

def test_latest_audit_selection_and_five_metadata_fields(qapp):
    """Verifica que el dashboard presente los 5 campos requeridos de la última ejecución."""
    page = HomePage()
    try:
        mock_payload = {
            "has_data": True,
            "latest_run": {
                "id": 105,
                "execution_date": "2026-11-02 14:45:00",
                "source_type": "aws",
                "status": "completada",
                "total_findings": 3,
            },
            "summary": {"total": 12, "conforme": 9, "hallazgo": 3, "no_evaluable": 0},
            "distribution": {
                "conforme": {"count": 9, "percentage": 75.0},
                "hallazgo": {"count": 3, "percentage": 25.0},
                "no_evaluable": {"count": 0, "percentage": 0.0},
            },
            "rules_summary": {},
            "results": [],
            "resources": [],
        }

        with patch.object(page._audit_service, "get_dashboard_data", return_value=mock_payload):
            page.refresh_dashboard()

            # 1. Identificador de auditoría
            assert page.lbl_run_id.text() == "#105"
            # 2. Fecha y hora
            assert page.lbl_run_date.text() == "2026-11-02 14:45:00"
            # 3. Fuente de datos
            assert page.lbl_run_source.text() == "Aws"
            # 4. Estado de ejecución
            assert page.lbl_run_status.text() == "Completada"
            # 5. Cantidad de hallazgos
            assert page.lbl_run_findings.text() == "3"

            # El botón para ver resultados debe estar habilitado
            assert page.btn_view_results.isEnabled() is True
    finally:
        page.close()
        page.deleteLater()


def test_repository_get_audit_runs_orders_consistently():
    """Verifica que la consulta de repositorio ordene por fecha y por id DESC sin depender del orden físico."""
    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            {"id": 10, "execution_date": "2026-11-02 12:00:00", "source_type": "simulacion", "status": "completada"},
        ]
        mock_ctx.return_value.__enter__.return_value = cursor

        runs = get_audit_runs(limit=5)
        assert len(runs) == 1

        query = cursor.execute.call_args[0][0]
        # Debe contener ORDER BY con criterio consistente
        assert "ORDER BY execution_date DESC, id DESC" in query
        assert "LIMIT %s" in query


# =============================================================================
# 3. AUSENCIA DE MEZCLA ENTRE EJECUCIONES (3.1 & 3.4)
# =============================================================================

def test_no_mixing_between_different_runs(mock_service):
    """Comprueba que al calcular el dashboard para la corrida más reciente, no se mezclen datos de corridas anteriores."""
    # Simulamos dos ejecuciones en el historial: Run 20 (reciente) y Run 10 (antigua)
    history = [
        {"id": 20, "execution_date": "2026-11-02 12:00:00", "source_type": "simulacion", "status": "completada"},
        {"id": 10, "execution_date": "2026-11-01 09:00:00", "source_type": "aws", "status": "completada"},
    ]

    # Resultados específicos de la corrida 20
    results_run_20 = [
        AuditResult("IAM-001", "C15-01", "r1", "Conforme", "Conforme 1"),
        AuditResult("IAM-002", "C16-01", "r2", "Conforme", "Conforme 2"),
    ]
    summary_run_20 = {"total": 2, "conforme": 2, "hallazgo": 0, "no_evaluable": 0}

    with patch.object(mock_service, "get_audit_history", return_value=[history[0]]) as mock_hist:
        with patch.object(
            mock_service,
            "get_historical_run_results",
            return_value=(results_run_20, [], summary_run_20),
        ) as mock_results:
            data = mock_service.get_dashboard_data()

            # Solo se debió solicitar la última corrida (limit=1)
            mock_hist.assert_called_once_with(limit=1, db_name=None)

            # Se debieron recuperar ÚNICAMENTE los resultados de run_id=20
            mock_results.assert_called_once_with(run_id=20, db_name=None)

            # Indicadores corresponden únicamente a run 20
            assert data["latest_run"]["id"] == 20
            assert data["summary"]["total"] == 2
            assert data["summary"]["conforme"] == 2
            assert data["summary"]["hallazgo"] == 0
            assert data["distribution"]["conforme"]["percentage"] == 100.0


# =============================================================================
# 4. ACTUALIZACIÓN DEL DASHBOARD EN EL CICLO DE VIDA (3.3)
# =============================================================================

def test_dashboard_update_lifecycle_moments(qapp):
    """Verifica que el dashboard se actualice en los cuatro momentos clave."""
    with patch.object(AuditService, "get_dashboard_data", return_value={"has_data": False}):
        with patch.object(AuditService, "get_audit_history", return_value=[]):
            window = MainWindow()
            try:
                # Momento 1: Al abrir la aplicación, el dashboard se actualiza
                assert window.stacked_widget.currentIndex() == 0
                assert window.home_page.lbl_kpi_total.text() == "0"

                # Momento 2: Al ingresar nuevamente a la pantalla principal
                with patch.object(window.home_page, "refresh_dashboard") as mock_refresh:
                    # Navegar a Resultados (2)
                    window._on_navigate(2)
                    assert window.stacked_widget.currentIndex() == 2
                    # Regresar a Inicio (0)
                    window._on_navigate(0)
                    assert window.stacked_widget.currentIndex() == 0
                    mock_refresh.assert_called_once()

                # Momento 3: Después de ejecutar una auditoría
                with patch.object(window.home_page, "refresh_dashboard") as mock_refresh_audit:
                    sample_summary = {"total": 4, "conforme": 3, "hallazgo": 1, "no_evaluable": 0}
                    window._on_audit_completed(results=[], resources=[], summary=sample_summary)
                    mock_refresh_audit.assert_called_once()

                # Momento 4: Después de consultar una ejecución histórica y regresar al dashboard
                with patch.object(
                    window.audit_service,
                    "get_historical_run_results",
                    return_value=([], [], {"total": 6, "conforme": 6, "hallazgo": 0, "no_evaluable": 0}),
                ):
                    # Seleccionar corrida histórica #7
                    window._on_historical_run_selected(7)
                    assert window.stacked_widget.currentIndex() == 2  # Navega a Resultados

                    with patch.object(window.home_page, "refresh_dashboard") as mock_refresh_return:
                        # Regresar a Inicio
                        window._on_navigate(0)
                        assert window.stacked_widget.currentIndex() == 0
                        mock_refresh_return.assert_called_once()
            finally:
                window.close()
                window.deleteLater()


# =============================================================================
# 5. CASOS ESPECIALES (3.5)
# =============================================================================

def test_special_case_no_audits_registered(qapp):
    """Comprueba el comportamiento del dashboard cuando no existen auditorías en MySQL."""
    page = HomePage()
    try:
        empty_payload = {
            "has_data": False,
            "latest_run": None,
            "summary": {"total": 0, "conforme": 0, "hallazgo": 0, "no_evaluable": 0},
            "distribution": {
                "conforme": {"count": 0, "percentage": 0.0},
                "hallazgo": {"count": 0, "percentage": 0.0},
                "no_evaluable": {"count": 0, "percentage": 0.0},
            },
            "rules_summary": {},
        }

        with patch.object(page._audit_service, "get_dashboard_data", return_value=empty_payload):
            page.refresh_dashboard()

            # Banner informativo amarillo de ausencia de auditorías
            assert "No hay ejecuciones registradas" in page.banner_text.text()

            # Campos de última auditoría reseteados a guiones
            assert page.lbl_run_id.text() == "—"
            assert page.lbl_run_date.text() == "—"
            assert page.lbl_run_source.text() == "—"
            assert page.lbl_run_status.text() == "—"
            assert page.lbl_run_findings.text() == "—"

            # KPIs en cero
            assert page.lbl_kpi_total.text() == "0"
            assert page.lbl_kpi_conforme.text() == "0"
            assert page.lbl_kpi_hallazgo.text() == "0"
            assert page.lbl_kpi_no_evaluable.text() == "0"

            # Gráfico oculto y placeholder no oculto
            assert page.chart_view.isHidden() is True
            assert not page.lbl_chart_empty.isHidden()

            # Botón de ver resultados deshabilitado
            assert page.btn_view_results.isEnabled() is False
    finally:
        page.close()
        page.deleteLater()


def test_special_case_latest_run_zero_findings(qapp):
    """Comprueba el caso cuando la última auditoría tiene 0 hallazgos (100% conforme/no evaluable)."""
    page = HomePage()
    try:
        clean_payload = {
            "has_data": True,
            "latest_run": {
                "id": 88,
                "execution_date": "2026-11-02 08:30:00",
                "source_type": "simulacion",
                "status": "completada",
                "total_findings": 0,
            },
            "summary": {"total": 8, "conforme": 7, "hallazgo": 0, "no_evaluable": 1},
            "distribution": {
                "conforme": {"count": 7, "percentage": 87.5},
                "hallazgo": {"count": 0, "percentage": 0.0},
                "no_evaluable": {"count": 1, "percentage": 12.5},
            },
            "rules_summary": {},
            "results": [],
            "resources": [],
        }

        with patch.object(page._audit_service, "get_dashboard_data", return_value=clean_payload):
            page.refresh_dashboard()

            assert page.lbl_run_findings.text() == "0"
            assert page.lbl_kpi_hallazgo.text() == "0"
            assert "Hallazgo: 0 (0.0%)" in page.badge_dist_hallazgo.text()
            assert not page.chart_view.isHidden()
            assert page.lbl_chart_empty.isHidden() is True
    finally:
        page.close()
        page.deleteLater()


def test_special_case_different_sources_display(qapp):
    """Comprueba que distintas fuentes ('simulacion', 'aws') se muestren con formato adecuado."""
    page = HomePage()
    try:
        for source_in, expected_out in [("simulacion", "Simulacion"), ("aws", "Aws")]:
            payload = {
                "has_data": True,
                "latest_run": {
                    "id": 50,
                    "execution_date": "2026-11-02 12:00:00",
                    "source_type": source_in,
                    "status": "completada",
                    "total_findings": 1,
                },
                "summary": {"total": 4, "conforme": 3, "hallazgo": 1, "no_evaluable": 0},
                "distribution": {
                    "conforme": {"count": 3, "percentage": 75.0},
                    "hallazgo": {"count": 1, "percentage": 25.0},
                    "no_evaluable": {"count": 0, "percentage": 0.0},
                },
                "rules_summary": {},
                "results": [],
                "resources": [],
            }
            with patch.object(page._audit_service, "get_dashboard_data", return_value=payload):
                page.refresh_dashboard()
                assert page.lbl_run_source.text() == expected_out
    finally:
        page.close()
        page.deleteLater()


def test_special_case_database_error_handling(qapp):
    """Comprueba que ante un fallo de conexión o consulta a MySQL la aplicación no se bloquee."""
    page = HomePage()
    try:
        with patch.object(
            page._audit_service,
            "get_dashboard_data",
            side_effect=RuntimeError("MySQL connection lost (error 2013)"),
        ):
            # No debe propagar la excepción hacia la aplicación
            page.refresh_dashboard()

            # Se debe haber capturado el error
            assert page.last_error is not None
            assert "MySQL connection lost" in page.last_error

            # Banner rojo de advertencia controlado
            assert "No se pudo conectar a la base de datos MySQL" in page.banner_text.text()
            assert "RuntimeError" in page.banner_text.text()

            # Los KPIs deben resetearse a guión para no mostrar datos erróneos
            assert page.lbl_kpi_total.text() == "—"
            assert page.lbl_kpi_conforme.text() == "—"
            assert page.lbl_kpi_hallazgo.text() == "—"
            assert page.lbl_kpi_no_evaluable.text() == "—"

            # Gráfico oculto y botón deshabilitado
            assert page.chart_view.isHidden() is True
            assert not page.lbl_chart_empty.isHidden()
            assert page.btn_view_results.isEnabled() is False
    finally:
        page.close()
        page.deleteLater()


# =============================================================================
# 6. INTEGRIDAD Y RESTRICCIÓN DE SOLO LECTURA (4.4 & 4.6)
# =============================================================================

def test_dashboard_and_history_strict_read_only():
    """Verifica mediante inspección de código y mocks que el dashboard no ejecuta sentencias de escritura."""
    service = AuditService()

    with patch("src.auditoria_iam.database.repository.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        # Primer fetchall para get_audit_runs, segundo para get_audit_results_by_run
        cursor.fetchall.side_effect = [
            [{"id": 1, "execution_date": "2026-11-01 10:00:00", "source_type": "simulacion", "status": "completada"}],
            [
                {
                    "id": 1,
                    "audit_run_id": 1,
                    "resource_id": 1,
                    "rule_code": "IAM-001",
                    "criterion_code": "C15-01",
                    "result_status": "Conforme",
                    "justification": "Evaluación conforme",
                    "details": None,
                    "resource_key": "user_admin",
                    "display_name": "Administrador",
                }
            ],
        ]
        mock_ctx.return_value.__enter__.return_value = cursor

        # Ejecutar consulta de dashboard
        service.get_dashboard_data()

        # Inspeccionar todas las sentencias ejecutadas en el cursor
        for call_args in cursor.execute.call_args_list:
            sql_query = call_args[0][0].strip().upper()
            assert not sql_query.startswith("INSERT"), f"Consulta de escritura detectada: {sql_query}"
            assert not sql_query.startswith("UPDATE"), f"Consulta de escritura detectada: {sql_query}"
            assert not sql_query.startswith("DELETE"), f"Consulta de escritura detectada: {sql_query}"
            assert not sql_query.startswith("DROP"), f"Consulta de escritura detectada: {sql_query}"
            assert not sql_query.startswith("ALTER"), f"Consulta de escritura detectada: {sql_query}"
            assert not sql_query.startswith("TRUNCATE"), f"Consulta de escritura detectada: {sql_query}"
            assert sql_query.startswith("SELECT"), f"Se esperaba sentencia SELECT, se obtuvo: {sql_query}"


# =============================================================================
# 7. SEÑALES Y ACCIONES INTERACTIVAS DEL DASHBOARD (HomePage)
# =============================================================================

def test_dashboard_interactive_actions_and_signals(qapp):
    """Verifica la emisión de señales al hacer clic en ver resultados, ver historial y refrescar."""
    page = HomePage()
    try:
        page.current_run_id = 42
        page.btn_view_results.setEnabled(True)

        # 1. Señal run_selected al hacer clic en 'Ver resultados detallados'
        run_selected_received = []
        page.run_selected.connect(lambda rid: run_selected_received.append(rid))
        page.btn_view_results.click()
        assert run_selected_received == [42]

        # 2. Señal navigate_requested al hacer clic en 'Ver historial completo'
        nav_requested_received = []
        page.navigate_requested.connect(lambda idx: nav_requested_received.append(idx))
        page.btn_view_history.click()
        assert nav_requested_received == [3]

        # 3. Clic en 'Actualizar dashboard 🔄'
        with patch.object(page, "refresh_dashboard") as mock_refresh:
            page.btn_refresh.click()
            mock_refresh.assert_called_once()
    finally:
        page.close()
        page.deleteLater()
