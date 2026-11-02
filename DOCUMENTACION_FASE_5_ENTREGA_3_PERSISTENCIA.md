# DOCUMENTACIÓN TÉCNICA — FASE 5, ENTREGA 3: PERSISTENCIA E INTEGRIDAD REFERENCIAL EN MYSQL

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.  
**Fase:** Fase 5 — Interfaz Gráfica de Usuario (PySide6)  
**Entrega:** Entrega 3 (Corregida) — Persistencia Transaccional, Integridad Referencial Estricta e Historial de Auditorías en MySQL Server  
**Fecha:** Noviembre 2026  
**Tecnologías:** Python 3.13, PySide6 (Qt 6.12.0), MySQL Server 9.6 / mysql-connector-python, Pytest  

---

## 1. Objetivo de la Entrega y Alcance de Correcciones

Implementar de forma exhaustiva, defensiva y desacoplada la persistencia transaccional de las auditorías técnicas ejecutadas desde la aplicación de escritorio PySide6 en el motor relacional **MySQL Server**, garantizando una estricta **integridad referencial basada en claves naturales y catalogadas**, control transaccional íntegro y comunicación transparente de errores en la interfaz de usuario:

1. **Resolución segura de recursos mediante clave natural (`resource_key` y `source_type`):**
   - Se eliminó la asunción de que los identificadores de recursos del simulador (`res.resource_id`) coinciden con los identificadores autoincrementales de MySQL (`resources.id`).
   - Se consulta la tabla `resources` filtrando por `source_type` para construir un mapa unívoco entre `resource_key` y el `id` real de MySQL.
   - Se utiliza exclusivamente el `id` recuperado de MySQL al insertar en `audit_results` y en `findings`.
   - Queda totalmente prohibido el uso de identificadores de sustitución como el ID `1` cuando un recurso no pueda resolverse.
   - Si un recurso evaluado no existe en MySQL o su correspondencia es ambigua (duplicados por clave y origen), se interrumpe la transacción de inmediato, se ejecuta `rollback()` y se levanta una excepción controlada.
   - Bajo ninguna circunstancia se modifican ni insertan registros en la tabla `resources`.

2. **Eliminación absoluta de identificadores de reglas de respaldo:**
   - Se eliminó cualquier diccionario de respaldo fijo (ej. `{"IAM-001": 1, ...}`).
   - Los IDs de reglas se resuelven de forma estricta contra la tabla `audit_rules` mediante su código formal (`rule_code`).
   - Si una regla técnica presente en los resultados no existe en MySQL, se cancela la transacción de inmediato con `rollback()` y error controlado, prohibiendo cualquier asociación a un ID asumido.

3. **Asociación rigurosa de perfiles de acceso (`access_profiles`):**
   - Se verifica la correspondencia inequívoca entre el perfil evaluado por el motor (`profile_code`) y el catálogo existente en MySQL (`access_profiles.profile_code`).
   - Si la correspondencia no puede ser demostrada fehacientemente o el resultado no pertenece a una regla asociada a perfiles, se asigna `NULL` (dado que `profile_id` es nullable en la base de datos).
   - Queda prohibido inventar asociaciones o emplear IDs de respaldo para perfiles.

4. **Gestión visible y controlada de errores al consultar el historial:**
   - En `main_window.py`, se sustituyó el bloque silencioso `except Exception: pass` en `_on_historical_run_selected()` por un manejo de errores visible y controlado.
   - Mediante el método `show_error_message()` en `HistoryPage`, se presenta un banner informativo en la interfaz gráfica indicando el fallo de consulta de la auditoría seleccionada sin exponer credenciales ni interrumpir la ejecución de la aplicación.

5. **Restricción de exclusión mutua `chk_evidence_target`:**
   - Registro de evidencias técnicas (`audit_evidence`) garantizando que exactamente uno entre `finding_id` y `audit_result_id` sea no nulo.

---

## 2. Arquitectura de Persistencia y Flujo de Datos

```
┌────────────────────────────────────────────────────────────────────────┐
│                          CAPA DE PRESENTACIÓN                          │
│                                                                        │
│   AuditPage  ──────── (Ejecución) ────────► AuditService               │
│       │                                          │                     │
│       ▼ (audit_completed)                        ▼                     │
│   ResultsPage ◄────── (Visualización) ◄──── Results & History          │
│       ▲                                          ▲                     │
│       │               (run_selected)             │                     │
│   HistoryPage ───────────────────────────────────┘                     │
│   (Muestra banner de error controlado ante fallos de conexión a MySQL) │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          CAPA DE APLICACIÓN                            │
│                                                                        │
│   AuditService                                                         │
│   ├── run_simulated_audit(persist=True)                                │
│   │     ├── AuditEngine.evaluate_all() -> 67 AuditResult               │
│   │     └── save_audit_run(..., context=context) [Transaccional]       │
│   ├── get_audit_history() -> List[audit_runs]                          │
│   └── get_historical_run_results(run_id) -> (results, resources, summary)
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          CAPA DE PERSISTENCIA                          │
│                                                                        │
│   persistence.py [ESCRITURA TRANSACCIONAL CON INTEGRIDAD ESTRICTA]     │
│   └── save_audit_run()                                                 │
│         ├── 1. Resuelve audit_rules por rule_code (Fallo -> Rollback)  │
│         ├── 2. Resuelve resources por resource_key (Fallo -> Rollback) │
│         ├── 3. Resuelve access_profiles por profile_code (o NULL)      │
│         ├── 4. INSERT INTO audit_runs                                  │
│         ├── 5. INSERT INTO audit_results (con IDs reales de MySQL)     │
│         ├── 6. INSERT INTO findings (con IDs reales de MySQL)          │
│         └── 7. INSERT INTO audit_evidence (cumple chk_evidence_target) │
│                                                                        │
│   repository.py [CONSULTAS DE SOLO LECTURA]                            │
│   ├── get_audit_runs()                                                 │
│   └── get_audit_results_by_run()                                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Mecanismos de Resolución e Integridad Referencial

### 3.1. Resolución de Recursos por Clave Natural
Al invocar `save_audit_run()`:
1. Se mapea el identificador local de cada recurso evaluado a su clave unívoca (`resource_key`).
2. Se ejecuta `SELECT id, resource_key FROM resources WHERE source_type = %s` contra MySQL.
3. Se verifica que no existan duplicados para la misma clave dentro del origen. De detectarse ambigüedad, se aborta la transacción con `rollback()`.
4. Para cada `AuditResult`, se obtiene el ID real de MySQL correspondiente a su `resource_key`. Si algún recurso no se encuentra registrado en MySQL, se emite una excepción descriptiva y se ejecuta `rollback()`. Nunca se emplea un ID por defecto (como `1`).

### 3.2. Resolución de Reglas sin Fallbacks Fijos
1. Se consulta `SELECT id, rule_code, default_severity FROM audit_rules`.
2. Se comprueba que cada regla evaluada (`IAM-001`, `IAM-002`, `IAM-003`, `IAM-004`) exista en la tabla `audit_rules`.
3. Si alguna regla requerida está ausente, la operación se cancela de inmediato mediante `rollback()`. No existen diccionarios de respaldo ni IDs cableados en el código.

### 3.3. Resolución Inequívoca de Perfiles de Acceso
1. Se consulta `SELECT id, profile_code FROM access_profiles`.
2. Se extrae el código formal del perfil (`profile_code`) desde `details` o desde el catálogo `context.profiles`.
3. Si el código coincide unívocamente con un perfil activo en MySQL, se asocia su `id` real de base de datos.
4. Si no hay correspondencia demostrada o el resultado no aplica a perfiles, se inserta explícitamente `NULL` (sin asumir asociaciones ni forzar identificadores).

### 3.4. Restricción `chk_evidence_target` en Evidencias
- En hallazgos técnicos (`result_status = 'Hallazgo'`), la evidencia se asocia exclusivamente al hallazgo: `finding_id = <ID>` y `audit_result_id = NULL`.
- En otros resultados con evidencia probatoria, se asocia exclusivamente al resultado: `finding_id = NULL` y `audit_result_id = <ID>`.

---

## 4. Archivos Modificados en la Corrección

1. **`src/auditoria_iam/database/persistence.py`:**
   - Implementación de resolución unívoca por `resource_key` y `source_type`.
   - Eliminación total de IDs de fallback para recursos (`res_id = 1`) y reglas (`fallback_rules`).
   - Mapeo estricto de `profile_code` contra `access_profiles` y asignación de `NULL` ante falta de correspondencia.
   - Validación de ambigüedad en claves de recursos.
   - Referencia de evidencia actualizada a clave de recurso (`resource:resource_key:criterion_code`).

2. **`src/auditoria_iam/application/audit_service.py`:**
   - Paso del parámetro `context=context` en la llamada a `save_audit_run()` dentro de `run_simulated_audit()`.

3. **`src/auditoria_iam/ui/pages/history_page.py`:**
   - Incorporación del método público `show_error_message(message: str)` para desplegar banners de alerta visual en color rojo sin afectar el resto de la interfaz.

4. **`src/auditoria_iam/ui/main_window.py`:**
   - Corrección de `_on_historical_run_selected(run_id)`: reemplazo de `except Exception: pass` por captura controlada que registra el error y llama a `self.history_page.show_error_message()`.

5. **`tests/test_persistence.py`:**
   - Reestructuración completa con 16 pruebas unitarias que validan:
     - Mapeo de recursos cuando los IDs del simulador y MySQL difieren.
     - Rollback y rechazo ante recursos inexistentes (sin fallback a ID 1).
     - Rollback ante correspondencia ambigua (duplicados en MySQL).
     - Rollback ante reglas faltantes en `audit_rules` (sin IDs de respaldo).
     - Asociación de perfiles por código y uso de `NULL`.
     - Invariante de solo lectura sobre tablas de catálogo (`resources`, `audit_rules`, `access_profiles`, `iso_controls`).
     - Transaccionalidad completa (commit solo tras éxito total, rollback ante error).

6. **`tests/test_ui.py`:**
   - Incorporación de prueba unitaria específica (prueba 18) que valida que los fallos al recuperar auditorías históricas se comuniquen al usuario en el banner de la interfaz gráfica sin cierres abruptos ni exposición de credenciales.

---

## 5. Resultados de las Pruebas Automatizadas

Se ejecutó la suite completa de pruebas unitarias sobre el entorno virtual Python 3.13 con `pytest`:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\andre\Desktop\TESIS\sistema
collected 180 items

tests/test_audit_engine.py ........                                      [  4%]
tests/test_audit_models.py ......                                        [  7%]
tests/test_aws_data_source.py ............................               [ 23%]
tests/test_connection.py ......                                          [ 26%]
tests/test_persistence.py ................                               [ 35%]
tests/test_repository.py ...................                             [ 46%]
tests/test_rule_iam_001.py ................                              [ 55%]
tests/test_rule_iam_002.py .............                                 [ 62%]
tests/test_rule_iam_003.py ......................                        [ 74%]
tests/test_rule_iam_004.py ......                                        [ 77%]
tests/test_settings.py .............                                     [ 85%]
tests/test_simulator.py .........                                        [ 90%]
tests/test_ui.py ..................                                      [100%]

============================= 180 passed in 4.25s =============================
```

- **Total de pruebas en el sistema:** 180 pruebas.
- **Pruebas aprobadas:** 180 pruebas (100% de éxito).
- **Pruebas fallidas:** 0 pruebas.

---

## 6. Restricciones y Principios de Diseño Respetados

1. **Cero modificaciones a catálogos existentes:** Las tablas `resources`, `audit_rules`, `access_profiles`, `profile_expected_groups`, `profile_expected_trust_principals` e `iso_controls` se mantienen estrictamente como catálogos de solo lectura.
2. **Cero operaciones UPDATE, DELETE o DDL:** Verificado mediante pruebas automatizadas de análisis de código (`test_persistence_strictly_no_update_or_delete` y `test_strictly_no_modifications_on_catalog_tables`).
3. **Cero alteraciones al motor de auditoría:** Los archivos `engine.py`, `models.py` y las reglas `iam_001` a `iam_004` permanecieron inalterados.
4. **Cero suposiciones de IDs de base de datos:** Se eliminó cualquier coincidencia asumida entre identificadores numéricos locales y autonuméricos de MySQL.
5. **Cero fugas de credenciales:** Ninguna credencial ni detalle de conexión se expone en la interfaz ni en logs.
