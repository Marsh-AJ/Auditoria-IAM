# DOCUMENTACIÓN TÉCNICA — FASE 5, ENTREGA 2: INTEGRACIÓN DE LA INTERFAZ GRÁFICA CON EL MOTOR DE AUDITORÍA

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.  
**Fase:** Fase 5 — Interfaz Gráfica de Usuario (PySide6)  
**Entrega:** Entrega 2 — Integración Funcional de la Interfaz con el Motor de Auditoría (Simulador)  
**Fecha:** Noviembre 2026  
**Tecnologías:** Python 3.13, PySide6 (Qt 6.12.0), Pytest  

---

## 1. Objetivo de la Entrega

Integrar la aplicación de escritorio desarrollada con PySide6 con el motor central de auditoría algorítmica (`AuditEngine`), permitiendo ejecutar auditorías manuales completas de principio a fin utilizando exclusivamente la fuente de datos simulados.

El usuario puede:
1. Abrir la aplicación de escritorio.
2. Seleccionar la fuente "Simulador de Datos Local".
3. Ejecutar la auditoría técnica mediante el botón "Ejecutar auditoría".
4. Visualizar los resultados reales producidos por las cuatro reglas IAM (`IAM-001`, `IAM-002`, `IAM-003`, `IAM-004`) en la vista de resultados, junto con los indicadores cuantitativos de resumen (Total, Conforme, Hallazgo, No evaluable).

---

## 2. Arquitectura de Integración

Se adoptó un diseño desacoplado mediante una capa de aplicación intermedia ([`AuditService`](file:///c:/Users/andre/Desktop/TESIS/sistema/src/auditoria_iam/application/audit_service.py)) y el patrón de señales y slots de Qt:

```
┌────────────────────────────────────────────────────────┐
│                   CAPA DE PRESENTACIÓN                 │
│                                                        │
│   MainWindow ──────── (Signals / Navigation) ────────┐ │
│       ▲                                              │ │
│       │                                              ▼ │
│   AuditPage                                     ResultsPage
│  [Ejecutar]                                   [Tabla y Resumen]
└───────┬──────────────────────────────────────────────▲─┘
        │                                              │
        │ Signals (results, resources, summary)        │
        ▼                                              │
┌──────────────────────────────────────────────────────┴─┐
│                    CAPA DE APLICACIÓN                  │
│                                                        │
│   AuditService.run_simulated_audit()                   │
└───────┬────────────────────────────────────────────────┘
        │
        ├──► IAMSimulatorDataSource (data_sources/simulator/)
        │       ├── get_resources() -> 10 identidades
        │       └── get_audit_context() -> AuditContext
        │
        └──► AuditEngine.evaluate_all() (audit/engine.py)
                ├── RuleIAM001AccessControl (ISO 5.15)
                ├── RuleIAM002IdentityManagement (ISO 5.16)
                ├── RuleIAM003AccessRights (ISO 5.18)
                └── RuleIAM004SecureAuthentication (ISO 8.5)
```

### Características de la Integración:
- **Desacoplamiento Estricto:** La interfaz gráfica no implementa lógica de evaluación de reglas ni analiza documentos JSON directamente. Delega la orquestación en `AuditService`, el cual consulta `IAMSimulatorDataSource` e invoca `AuditEngine.evaluate_all()`.
- **Comunicación Reactiva mediante Señales Qt:**
  - `AuditPage.audit_completed = Signal(list, list, dict)`: Transmite la lista de instancias `AuditResult`, la colección de recursos evaluados y el resumen de conteos.
  - `AuditPage.navigate_requested = Signal(int)`: Permite saltar directamente a la vista de resultados desde el botón informativo posterior a la auditoría.
  - `MainWindow._on_audit_completed`: Conecta ambas páginas sin acoplarlas entre sí, actualizando la tabla y los contadores en `ResultsPage.load_results()`.
- **Control de Concurrencia y Estado de UI:**
  - Durante el procesamiento, el botón "Ejecutar auditoría" se deshabilita temporalmente y se procesan los eventos pendientes (`QApplication.processEvents()`) para reflejar de inmediato el mensaje de progreso ("⏳ Ejecutando auditoría técnica...").
  - Al concluir (o en caso de error capturado en bloque defensivo `try/except/finally`), el botón vuelve a habilitarse para permitir ejecuciones consecutivas.
- **Protección Restrictiva sobre AWS IAM:**
  - Si el usuario selecciona "Adaptador AWS IAM", el botón de ejecución se deshabilita de forma automática y se presenta una advertencia que aclara que la ejecución en vivo desde la interfaz se abordará en una fase posterior. Se previene cualquier invocación accidental al motor o llamadas a la nube.

---

## 3. Funciones Existentes Reutilizadas

La integración reutilizó de forma íntegra los componentes y contratos previamente aprobados:

1. **Simulador de Datos ([`simulator.py`](file:///c:/Users/andre/Desktop/TESIS/sistema/src/auditoria_iam/data_sources/simulator/simulator.py)):**
   - `IAMSimulatorDataSource.get_resources()` / `get_simulated_resources()`: Recupera la colección normalizada de 10 identidades simuladas (usuarios y roles).
   - `IAMSimulatorDataSource.get_audit_context()` / `get_simulated_audit_context()`: Recupera la instancia de `AuditContext` con perfiles, grupos y confianzas de referencia.

2. **Motor Central de Auditoría ([`engine.py`](file:///c:/Users/andre/Desktop/TESIS/sistema/src/auditoria_iam/audit/engine.py)):**
   - `AuditEngine()`: Inicialización estándar con registro automático de las 4 reglas.
   - `AuditEngine.evaluate_all(resources=resources, context=context)`: Ejecución algorítmica sobre la colección completa, devolviendo la lista de `AuditResult`.

3. **Modelos de Auditoría ([`models.py`](file:///c:/Users/andre/Desktop/TESIS/sistema/src/auditoria_iam/audit/models.py)):**
   - `AuditResult`: Estructura inmutable con `rule_code`, `criterion_code`, `resource_id`, `result_status`, `justification`, `details` y `evidence`.
   - `AuditContext`: Contenedor referencial de perfiles autorizados.

4. **Reglas Técnicas:**
   - `RuleIAM001AccessControl` (Control 5.15)
   - `RuleIAM002IdentityManagement` (Control 5.16)
   - `RuleIAM003AccessRights` (Control 5.18)
   - `RuleIAM004SecureAuthentication` (Control 8.5)

---

## 4. Archivos Nuevos y Modificados

### Archivos Nuevos:
1. `src/auditoria_iam/application/audit_service.py`: Servicio de aplicación para orquestar la ejecución del simulador en el motor algorítmico y calcular resúmenes cuantitativos.
2. `DOCUMENTACION_FASE_5_ENTREGA_2_INTEGRACION.md`: Presente informe técnico.

### Archivos Modificados:
1. `src/auditoria_iam/application/__init__.py`: Exportación formal de `AuditService`.
2. `src/auditoria_iam/ui/pages/audit_page.py`:
   - Incorporación de `audit_completed` y `navigate_requested` signals.
   - Control de activación/desactivación del botón de ejecución según la fuente seleccionada.
   - Flujo de ejecución interactivo con manejo defensivo de excepciones y restauración de estado.
   - Mensaje de confirmación detallado y botón de navegación directa a resultados.
3. `src/auditoria_iam/ui/pages/results_page.py`:
   - Incorporación de 4 tarjetas de resumen métrico (*Total Evaluaciones*, *Conforme*, *Hallazgo*, *No evaluable*).
   - Estructuración de la tabla en 6 columnas con autoajuste, colores condicionales según el estado y modo solo lectura.
   - Implementación del método `load_results(results, resources, summary)` para poblar la vista dinámicamente.
4. `src/auditoria_iam/ui/main_window.py`:
   - Conexión de señales `audit_completed` y `navigate_requested` entre `AuditPage` y `ResultsPage`.
   - Implementación del slot `_on_audit_completed`.
5. `tests/test_ui.py`:
   - Ampliación de la suite de pruebas a 14 pruebas completas que verifican selección, ejecución real, contadores, tabla, manejo de errores, bloqueo de AWS IAM y ausencia de consultas a MySQL.

### Archivos No Modificados (Preservación Absoluta de Fases Anteriores):
- Motor y reglas: `engine.py`, `models.py`, `iam_001_access_control.py`, `iam_002_identity_management.py`, `iam_003_access_rights.py`, `iam_004_secure_authentication.py`.
- Simulador y adaptador: `simulator.py`, `adapter.py`.
- Base de datos relacional y configuración: `database/`, `config/settings.py`.

---

## 5. Instrucciones de Uso y Ejecución

### Forma de Iniciar la Aplicación:
Desde la terminal en el directorio raíz del proyecto:
```powershell
python main.py
```
*(O utilizando el intérprete del entorno virtual: `.\.venv\Scripts\python.exe main.py`)*

### Forma de Ejecutar una Auditoría Simulada:
1. En el menú lateral izquierdo, hacer clic en **"Ejecutar auditoría"**.
2. Verificar que en el selector figure **"Simulador de Datos Local (Fase 4 - Entrega 1)"** (opción predeterminada).
3. Hacer clic en el botón azul **"Ejecutar auditoría"**.
4. El sistema evaluará automáticamente las 10 identidades simuladas frente a los controles 5.15, 5.16, 5.18 y 8.5.
5. Se desplegará el mensaje de confirmación con el resumen:
   - Total de evaluaciones: **67**
   - Conforme: **36**
   - Hallazgo: **6**
   - No evaluable: **25**
6. Hacer clic en **"Ver resultados detallados →"** (o en la pestaña **"Resultados"** del menú lateral) para consultar la tabla con cada evaluación individual, tipo de recurso, control ISO, estado coloreado y descripción técnica.

---

## 6. Resultados de las Pruebas Automatizadas

Se ejecutó la suite completa de pruebas unitarias del proyecto con `pytest`:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\andre\Desktop\TESIS\sistema
collected 160 items

tests/test_audit_engine.py ........                                      [  5%]
tests/test_audit_models.py ......                                        [  9%]
tests/test_aws_data_source.py ............................               [ 26%]
tests/test_connection.py ......                                          [ 30%]
tests/test_repository.py ...................                             [ 42%]
tests/test_rule_iam_001.py ................                              [ 52%]
tests/test_rule_iam_002.py .............                                 [ 60%]
tests/test_rule_iam_003.py ......................                        [ 74%]
tests/test_rule_iam_004.py ......                                        [ 78%]
tests/test_settings.py .............                                     [ 86%]
tests/test_simulator.py .........                                        [ 91%]
tests/test_ui.py ..............                                          [100%]

============================= 160 passed in 2.93s =============================
```

### Cobertura de las Pruebas de Interfaz (`tests/test_ui.py`):
1. `test_ui_modules_import`: Importación de módulos y servicios.
2. `test_main_window_creation`: Inicialización, dimensiones mínimas y título.
3. `test_five_sections_exist_in_stack`: Verificación de las 5 páginas en el stack.
4. `test_navigation_between_screens`: Navegación interactiva por el menú lateral.
5. `test_audit_page_source_selector`: Opciones disponibles en el selector de fuente.
6. `test_audit_page_aws_does_not_allow_execution`: Bloqueo de ejecución al seleccionar AWS IAM.
7. `test_results_page_structure`: Estructura inicial de 6 columnas y estado vacío.
8. `test_history_page_structure`: Estructura desacoplada de la vista de historial.
9. `test_settings_page_sections_and_no_credentials`: Parámetros sin exposición de secretos.
10. `test_audit_execution_invokes_engine_and_processes_all_four_rules`: Invocación del motor real y evaluación de las 4 reglas técnicas.
11. `test_results_page_counters_and_statuses_match_engine_output`: Coincidencia exacta de contadores (67, 36, 6, 25) y presencia de los tres estados en la tabla.
12. `test_error_handling_does_not_crash_application`: Manejo defensivo ante excepciones sin caída de la aplicación.
13. `test_multiple_audits_execution_updates_cleanly`: Posibilidad de reejecución sin duplicación ni acumulación de filas.
14. `test_no_mysql_interactions_during_audit`: Ausencia absoluta de consultas o escrituras a MySQL.

---

## 7. Restricciones Respetadas

- **Sin modificación del motor ni de las reglas:** `engine.py`, `models.py` y las reglas `iam_001` a `iam_004` permanecen exactamente iguales.
- **Sin modificación del simulador ni del adaptador AWS:** `simulator.py` y `adapter.py` se mantuvieron intactos.
- **Sin conexiones ni escrituras a MySQL:** No se realizaron llamadas a la base de datos relacional.
- **Sin llamadas de red a AWS:** Se preservó el bloqueo operativo para la fuente AWS en esta entrega.
- **Sin exposición de credenciales:** Ningún valor confidencial ni variable del archivo `.env` es accesible desde la interfaz.

