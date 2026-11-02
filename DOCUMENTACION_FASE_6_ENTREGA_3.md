# DOCUMENTACIÓN TÉCNICA — FASE 6, ENTREGA 6.3: INTEGRACIÓN Y VALIDACIÓN DEL DASHBOARD CON EL HISTORIAL DE AUDITORÍAS

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.  
**Fase:** Fase 6 — Visualización Ejecutiva, Reportes y Catálogo Normativo  
**Entrega:** Entrega 6.3 — Integración y Validación del Dashboard con el Historial de Auditorías  
**Fecha:** Noviembre 2026  
**Tecnologías:** Python 3.13, PySide6 (Qt 6.12.0, QtCharts), MySQL Server 9.6 / mysql-connector-python, Pytest 9.2.0  
**Estado:** Finalizado y verificado (219 pruebas automatizadas aprobadas al 100%, código de salida 0)

---

## 1. OBJETIVO Y ALCANCE DE LA ENTREGA

La presente entrega tuvo como objetivo principal revisar, validar y asegurar la integración integral y la consistencia de la información entre el **Dashboard Ejecutivo (`HomePage`)**, el **Historial de Auditorías (`HistoryPage`)** y los **Registros Persistidos en MySQL Server** (`audit_runs`, `audit_results`, `findings`, `audit_evidence`).

El alcance abarcó:
1. Comprobar la correspondencia matemática exacta entre los indicadores del dashboard y los registros reales de la última auditoría.
2. Garantizar que la selección de la última auditoría utilice un criterio cronológico consistente e independiente del orden físico en disco.
3. Validar la actualización automática del dashboard en los cuatro momentos clave del ciclo de vida de la aplicación.
4. Asegurar la estricta integridad del historial, impidiendo cualquier mezcla o contaminación de resultados entre ejecuciones diferentes.
5. Verificar el comportamiento controlado y robusto de la interfaz ante escenarios especiales (ausencia de datos, auditorías sin hallazgos, fuentes heterogéneas y caídas de base de datos).
6. Confirmar el cumplimiento estricto del principio de **solo lectura** sobre la base de datos durante todas las operaciones del dashboard y del historial.

---

## 2. INFORME TÉCNICO DE COMPONENTES INSPECCIONADOS

Se realizó una inspección estática y dinámica exhaustiva de los módulos involucrados en la integración:

| Capa | Archivo / Componente | Responsabilidad Inspeccionada | Estado de Integración |
|---|---|---|:---:|
| **Presentación (UI)** | `src/auditoria_iam/ui/pages/home_page.py` | Consulta de métricas en `refresh_dashboard()`, enlace a tarjetas KPI, gráfico de dona `QPieSeries`, desglose de reglas y navegación. | **Conforme** |
| **Presentación (UI)** | `src/auditoria_iam/ui/main_window.py` | Orquestación de navegación en `_on_navigate()`, transferencia de señales `run_selected`, actualización tras auditoría (`_on_audit_completed`) y visualización histórica. | **Conforme con ajuste puntual** |
| **Presentación (UI)** | `src/auditoria_iam/ui/pages/history_page.py` | Presentación tabular de corridas históricas, selección por fila y emisión de señal `run_selected`. | **Conforme** |
| **Presentación (UI)** | `src/auditoria_iam/ui/pages/results_page.py` | Carga de resultados tanto en vivo como históricos mediante `load_results()`. | **Conforme** |
| **Aplicación** | `src/auditoria_iam/application/audit_service.py` | Métodos `get_dashboard_data()`, `get_audit_history()` y `get_historical_run_results()`. Agregación y cálculo de porcentajes. | **Conforme** |
| **Repositorio** | `src/auditoria_iam/database/repository.py` | Consultas SQL de solo lectura: `get_audit_runs()`, `get_audit_results_by_run()`, `get_findings_by_run()`. | **Conforme con ajuste puntual** |
| **Persistencia** | `src/auditoria_iam/database/persistence.py` | Inserción atómica e inmutable en `audit_runs`, `audit_results`, `findings` y `audit_evidence`. | **Conforme** |

---

## 3. DEFECTOS ENCONTRADOS Y CORRECCIONES REALIZADAS

Durante la inspección de consistencia se identificaron dos aspectos de mejora puntual requeridos para cumplir a cabalidad con los lineamientos de la entrega:

### Defecto 1: Criterio de ordenamiento de la última ejecución en el repositorio
- **Ubicación:** `src/auditoria_iam/database/repository.py`, función `get_audit_runs()`.
- **Condición detectada:** La consulta SQL ordenaba exclusivamente por `ORDER BY id DESC`. Aunque en inserciones secuenciales normales el ID autoincremental refleja el orden de creación, este criterio no garantizaba de forma estricta la precedencia cronológica del campo de negocio `execution_date` frente a inserciones asíncronas o migraciones de datos.
- **Corrección aplicada:** Se sustituyó la cláusula por:
  ```sql
  ORDER BY execution_date DESC, id DESC
  ```
  Esto asegura un criterio consistente basado primero en la fecha/hora real de la auditoría y desempatando de manera determinista por el identificador primario, cumpliendo el requisito 3.2.

### Defecto 2: Acceso a atributo privado en la navegación de MainWindow
- **Ubicación:** `src/auditoria_iam/ui/main_window.py`, método `_on_historical_run_selected()`.
- **Condición detectada:** Se realizaba la llamada `self.audit_page._audit_service.get_historical_run_results(run_id)`, accediendo a un miembro privado de la página de auditoría en lugar de utilizar directamente el servicio centralizado `self.audit_service` instanciado en la propia ventana principal.
- **Corrección aplicada:** Se modificó la invocación para utilizar directamente `self.audit_service.get_historical_run_results(run_id)`, eliminando acoplamientos innecesarios.

---

## 4. VERIFICACIÓN DETALLADA DE LAS ACTIVIDADES REQUERIDAS

### 4.1. Consistencia de Indicadores (Actividad 3.1)
- **Fórmula de verificación:** Se validó que para cualquier ejecución:
  $$\text{Total} = \text{Conforme} + \text{Hallazgo} + \text{No evaluable}$$
- **Cálculo porcentual:** Se verificó que los porcentajes se calculan como $\text{round}((\text{conteo} / \text{total}) \times 100, 1)$. En caso de que $\text{total} == 0$, el sistema maneja la condición de forma segura estableciendo los porcentajes en $0.0\%$ sin generar excepción por división por cero (`ZeroDivisionError`).
- **Aislamiento de auditorías:** `AuditService.get_dashboard_data()` invoca `get_historical_run_results(run_id=latest_run["id"])`, la cual ejecuta:
  ```sql
  WHERE ar.audit_run_id = %s
  ```
  garantizando que bajo ninguna circunstancia se mezclen o sumen resultados de diferentes corridas.

### 4.2. Identificación de la Última Auditoría (Actividad 3.2)
Se comprobó que la tarjeta `Información de la Última Auditoría` en `HomePage` extrae y renderiza los 5 campos exigidos:
1. **Identificador de auditoría:** Formateado como `#<id>`.
2. **Fecha y hora:** Cadena ISO o estándar recuperada de `execution_date`.
3. **Fuente de datos:** Capitalizada (`Simulacion` o `Aws`).
4. **Estado de ejecución:** Capitalizada (`Completada`).
5. **Cantidad de hallazgos:** Conteo exacto coloreado en rojo de advertencia.

### 4.3. Actualización del Dashboard en el Ciclo de Vida (Actividad 3.3)
Se validó la actualización en los cuatro momentos clave del sistema:
1. **Al abrir la aplicación:** `HomePage.__init__()` ejecuta `self.refresh_dashboard()` en su inicialización.
2. **Al ingresar nuevamente a la pantalla principal:** `MainWindow._on_navigate(0)` detecta la navegación a Inicio e invoca `self.home_page.refresh_dashboard()`.
3. **Después de ejecutar una auditoría:** Al finalizar la ejecución en `AuditPage`, se emite la señal `audit_completed`, capturada por `MainWindow._on_audit_completed()`, la cual invoca de inmediato `self.home_page.refresh_dashboard()`.
4. **Después de consultar una ejecución histórica y regresar:** Al seleccionar una corrida en `HistoryPage`, se visualizan sus resultados en `ResultsPage`; al pulsar el botón `Inicio` en el menú lateral, `MainWindow._on_navigate(0)` refresca el dashboard con la última auditoría persistida en MySQL, sin que la consulta histórica previa contamine las métricas globales.

### 4.4. Integridad del Historial (Actividad 3.4)
- Cada corrida en `audit_runs` posee un identificador inmutable asignado por `AUTO_INCREMENT`.
- Los resultados individuales en `audit_results` y los hallazgos en `findings` están estrictamente vinculados por clave foránea a su `audit_run_id`.
- La persistencia (`save_audit_run`) es puramente aditiva (`INSERT`); ninguna ejecución posterior altera o sobrescribe filas de auditorías anteriores.

### 4.5. Casos Especiales y Resiliencia (Actividad 3.5)
| Escenario Especial | Comportamiento del Sistema Verificado | Resultado |
|---|---|:---:|
| **Sin auditorías registradas (`has_data: False`)** | Muestra banner informativo amarillo, resetea metadatos a guiones (`—`), fija KPIs en 0, oculta el gráfico de dona, muestra etiqueta placeholder y deshabilita el botón «Ver resultados detallados». | **Aprobado** |
| **Auditoría única** | Presenta los datos de esa única corrida como última auditoría, activa gráficos y permite navegar a su detalle. | **Aprobado** |
| **Múltiples auditorías** | Selecciona la más reciente (`ORDER BY execution_date DESC, id DESC`), aislando completamente sus métricas de las demás. | **Aprobado** |
| **Última corrida sin hallazgos** | Indicador KPI de hallazgos en 0, insignia `Hallazgo: 0 (0.0%)`, el gráfico de dona omite el sector rojo (evitando distorsión visual) y muestra sectores verde y ámbar. | **Aprobado** |
| **Fuentes mixtas (`simulacion` y `aws`)** | Identifica correctamente el campo `source_type` sin colisión de identidades. | **Aprobado** |
| **Fallo de conexión MySQL / excepción** | Captura la excepción en bloque `try/except`, despliega banner rojo de advertencia con tipo de error, resetea KPIs a guiones para evitar mostrar datos falsos y no bloquea ni colapsa la interfaz. | **Aprobado** |

---

## 5. CONFIRMACIÓN DE RESTRICCIONES DE SEGURIDAD Y SOLO LECTURA

Se verificó el cumplimiento estricto de todas las restricciones obligatorias:
1. **Reglas IAM intactas:** No se modificaron `IAM-001`, `IAM-002`, `IAM-003` ni `IAM-004`.
2. **Motor de auditoría intacto:** Cero alteraciones a criterios de evaluación en `AuditEngine`.
3. **Cero modificaciones en MySQL:** Se verificó mediante inspección de código y mocks de cursor que el dashboard y el historial ejecutan exclusivamente sentencias `SELECT`. No se ejecutan `INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE` ni `ALTER`.
4. **Cero ejecuciones no autorizadas:** Abrir o refrescar el dashboard no dispara auditorías ni realiza peticiones hacia APIs externas de AWS IAM.
5. **Protección de secretos:** No se modificaron ni expusieron variables ni credenciales del archivo `.env`.
6. **Ciclo de vida Qt respetado:** Se conservó la arquitectura centralizada de pruebas en `tests/conftest.py`.

---

## 6. RESULTADOS DE PRUEBAS AUTOMATIZADAS

Se diseñó e integró la suite especializada [`tests/test_dashboard_integration.py`](file:///c:/Users/andre/Desktop/TESIS/sistema/tests/test_dashboard_integration.py) con 12 pruebas unitarias y de integración que validan exhaustivamente los requerimientos de la Entrega 6.3:

| # | Identificador de Prueba | Alcance Validado | Resultado |
|---|---|---|:---:|
| 1 | `test_indicator_consistency_and_sums` | Verifica que `total == conf + hall + noev` y que los KPIs coincidan exactamente. | **PASSED** |
| 2 | `test_percentage_calculations_and_zero_division` | Verifica el cálculo de porcentajes con 1 decimal y la protección contra división entre cero cuando `total == 0`. | **PASSED** |
| 3 | `test_latest_audit_selection_and_five_metadata_fields` | Comprueba la presentación de los 5 campos de metadatos de la última auditoría. | **PASSED** |
| 4 | `test_repository_get_audit_runs_orders_consistently` | Comprueba que el repositorio aplique `ORDER BY execution_date DESC, id DESC`. | **PASSED** |
| 5 | `test_no_mixing_between_different_runs` | Demuestra que no existen mezclas de resultados ni hallazgos entre distintas ejecuciones. | **PASSED** |
| 6 | `test_dashboard_update_lifecycle_moments` | Valida la actualización en los 4 momentos del ciclo de vida de la aplicación. | **PASSED** |
| 7 | `test_special_case_no_audits_registered` | Verifica el comportamiento seguro y banner informativo cuando no hay registros en MySQL. | **PASSED** |
| 8 | `test_special_case_latest_run_zero_findings` | Valida el caso de última auditoría con 0 hallazgos (100% conforme/no evaluable). | **PASSED** |
| 9 | `test_special_case_different_sources_display` | Verifica la representación adecuada de fuentes de datos (`simulacion` y `aws`). | **PASSED** |
| 10 | `test_special_case_database_error_handling` | Valida el manejo de excepciones de base de datos sin colapsar la interfaz. | **PASSED** |
| 11 | `test_dashboard_and_history_strict_read_only` | Inspección estricta de consultas SQL confirmando cero sentencias de escritura. | **PASSED** |
| 12 | `test_dashboard_interactive_actions_and_signals` | Verifica emisión de señales de navegación, ver resultados y refresco interactivo. | **PASSED** |

### 6.1. Ejecución de las 4 Suites de Interfaz Gráfica Combinadas (57 Pruebas)
Comando: `python -X faulthandler -m pytest tests/test_ui.py tests/test_dashboard.py tests/test_reports.py tests/test_dashboard_integration.py -v`
- **Resultado:** **57 passed in 8.09s** (Código de salida: 0, Excepciones nativas: 0).

### 6.2. Tres Ejecuciones Consecutivas de la Suite Completa del Sistema (219 Pruebas)
Comando: `python -X faulthandler -m pytest tests -q`

```
Corrida 1: ................................................................ [ 32%]
           ................................................................ [ 65%]
           ................................................................ [ 98%]
           ...                                                              [100%]
           219 passed in 9.36s (Código de salida: 0)

Corrida 2: ................................................................ [ 32%]
           ................................................................ [ 65%]
           ................................................................ [ 98%]
           ...                                                              [100%]
           219 passed in 9.22s (Código de salida: 0)

Corrida 3: ................................................................ [ 32%]
           ................................................................ [ 65%]
           ................................................................ [ 98%]
           ...                                                              [100%]
           219 passed in 9.45s (Código de salida: 0)
```

---

## 7. CONCLUSIONES

La Entrega 6.3 concluye de manera satisfactoria la fase de visualización e integración del sistema de auditoría IAM:
- Se garantiza la fidelidad analítica de los datos presentados al usuario directivo y técnico.
- El dashboard opera como una capa de visualización estrictamente desacoplada, segura y de solo lectura.
- La aplicación responde de forma resiliente ante cualquier contingencia de conectividad o ausencia de datos previos.
- La suite completa de 219 pruebas automatizadas ratifica la estabilidad, confiabilidad y rendimiento de todo el sistema.

