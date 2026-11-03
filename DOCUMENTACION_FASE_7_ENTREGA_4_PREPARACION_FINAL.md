# DOCUMENTACIÓN TÉCNICA — FASE 7, ENTREGA 7.4
## PREPARACIÓN FINAL, DOCUMENTACIÓN Y REPLICABILIDAD DEL SISTEMA

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.  
**Fase:** Fase 7 — Adaptador AWS IAM e Integración de Nube  
**Entrega:** 7.4 — Preparación final, documentación y replicabilidad del sistema para entrega académica y demostración en predefensa  
**Rol:** Ingeniero de Software Senior / Auditor Técnico de Software  
**Fecha:** Noviembre 2026  
**Estado:** COMPLETADA CON ÉXITO — 100% DE VALIDACIONES APROBADAS  

---

### 1. OBJETIVO DE LA ENTREGA

Preparar formalmente el proyecto de software para su entrega académica y demostración ante el jurado evaluador en la predefensa de tesis, completando la totalidad de los archivos de configuración, dependencias, documentación técnica, plantilla de variables de entorno, script SQL consolidado y guía práctica de demostración.

Esta entrega no introduce nuevas funcionalidades operativas ni modifica las reglas de negocio, modelos ni persistencia existentes; se enfoca en asegurar la replicabilidad autónoma del sistema por terceros y dotar al proyecto del rigor documental propio de una tesis de grado.

---

### 2. ARCHIVOS CREADOS Y MODIFICADOS

| Archivo | Tipo de Acción | Propósito Técnico |
| :--- | :---: | :--- |
| [`requirements.txt`](file:///c:/Users/andre/Desktop/TESIS/sistema/requirements.txt) | **Modificado** | Actualizado con la totalidad de dependencias de ejecución requeridas (`boto3`, `PySide6`, `mysql-connector-python`, `python-dotenv`, `reportlab`, `openpyxl`). |
| [`requirements-dev.txt`](file:///c:/Users/andre/Desktop/TESIS/sistema/requirements-dev.txt) | **Creado** | Creado para aislar las dependencias de desarrollo y calidad de software (`-r requirements.txt`, `pytest>=8.0.0`). |
| [`.env.example`](file:///c:/Users/andre/Desktop/TESIS/sistema/.env.example) | **Creado** | Plantilla de configuración con las 6 variables consumidas por `settings.py` (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_CONNECT_TIMEOUT`) con valores de ejemplo no confidenciales. |
| [`.gitignore`](file:///c:/Users/andre/Desktop/TESIS/sistema/.gitignore) | **Modificado** | Limpieza controlada: se eliminó el comentario informal residual de la línea 13 y se formalizaron exclusiones de seguridad (`.env`, `.venv/`, `*.zip`, `.pytest_cache/`, `*.egg-info/`). |
| [`init_database_upharven.sql`](file:///c:/Users/andre/Desktop/TESIS/sistema/init_database_upharven.sql) | **Creado** | Script SQL consolidado para el despliegue del esquema relacional completo (10 tablas en InnoDB con claves primarias, foráneas, restricciones UNIQUE, CHECK, columnas generadas e inserción de catálogo de las 4 reglas ISO 27001). |
| [`README.md`](file:///c:/Users/andre/Desktop/TESIS/sistema/README.md) | **Creado** | Manual técnico principal de bienvenida, arquitectura, diagrama Mermaid, instalación paso a paso en PowerShell, comandos de prueba, descripción de fuentes, tablas y limitaciones. |
| [`GUIA_DEMOSTRACION_ACADEMICA.md`](file:///c:/Users/andre/Desktop/TESIS/sistema/GUIA_DEMOSTRACION_ACADEMICA.md) | **Creado** | Guía de 14 puntos para la defensa y demostración del sistema ante el jurado evaluador, explicando cada pantalla, KPI, estados de evaluación y ejemplo de hallazgos. |
| [`DOCUMENTACION_FASE_7_ENTREGA_4_PREPARACION_FINAL.md`](file:///c:/Users/andre/Desktop/TESIS/sistema/DOCUMENTACION_FASE_7_ENTREGA_4_PREPARACION_FINAL.md) | **Creado** | Informe oficial de la entrega con registro de validaciones y métricas. |
| `auditoria_iam_entrega_final.zip` | **Creado** | Paquete comprimido final con exclusión estricta de secretos, `.env`, entornos virtuales y cachés. |

---

### 3. DEPENDENCIAS INCORPORADAS Y VERSIONES VERIFICADAS

Se contrastaron las dependencias instaladas en el entorno virtual (`pip list`) con los archivos de requerimientos:

```ini
# requirements.txt (Ejecución)
boto3>=1.34.0
PySide6>=6.6.0
mysql-connector-python>=9.0.0
python-dotenv>=1.0.0
reportlab>=4.0.0
openpyxl>=3.1.0

# requirements-dev.txt (Desarrollo y Pruebas)
-r requirements.txt
pytest>=8.0.0
```

---

### 4. SCRIPT SQL CONSOLIDADO (`init_database_upharven.sql`)

El script reúne la estructura relacional definitiva y normalizada de la base de datos `auditoria_iam_upharven` bajo MySQL Server 8.0/9.6:

#### Tablas Incluidas (10 en Total):
1. **`audit_runs`:** Maestro de auditorías (ID, fecha, tipo de fuente, estado, hallazgos totales, resumen).
2. **`resources`:** Identidades y recursos con clave única compuesta `(resource_key, source_type)` y atributos técnicos en formato JSON.
3. **`audit_rules`:** Catálogo de reglas técnicas vinculadas a los controles ISO/IEC 27001:2022.
4. **`access_profiles`:** Perfiles de acceso autorizados (`identity_type` CHECK `'user'` o `'role'`).
5. **`profile_expected_groups`:** Lista blanca de grupos IAM permitidos para perfiles de usuario (FK a `access_profiles`).
6. **`profile_expected_trust_principals`:** Lista blanca de entidades de confianza autorizadas para perfiles de rol (FK a `access_profiles`).
7. **`resource_access_profiles`:** Asignación de perfiles a recursos con columna generada `is_active_flag` y restricción UNIQUE `(resource_id, is_active_flag)` que impide múltiples perfiles activos simultáneos.
8. **`audit_results`:** Veredictos exhaustivos (`Conforme`, `Hallazgo`, `No evaluable`) con restricción UNIQUE `(audit_run_id, resource_id, audit_rule_id, criterion_code)`.
9. **`findings`:** Incumplimientos de seguridad con severidad (`ALTA`, `MEDIA`, `CRITICA`), recomendaciones y vinculación a `audit_result_id`.
10. **`audit_evidence`:** Evidencias técnicas con restricción `chk_evidence_target` que exige exclusión mutua entre `finding_id` y `audit_result_id`.

#### Datos de Catálogo Incorporados:
Se incluyeron las 4 reglas técnicas correspondientes a los controles 5.15, 5.16, 5.18 y 8.5 de ISO/IEC 27001:2022 mediante `INSERT ... ON DUPLICATE KEY UPDATE`. No se incluyeron corridas ficticias ni datos históricos inventados.

---

### 5. RESULTADO DE VALIDACIONES EJECUTADAS

1. **Ejecución de la Suite Completa de Pruebas (Pytest):**
   - Comando: `.\.venv\Scripts\pytest.exe -q`
   - **Pruebas recopiladas:** **309**
   - **Pruebas aprobadas:** **309 (100%)**
   - **Pruebas fallidas:** **0**
   - **Pruebas omitidas:** **0**
   - **Tiempo de ejecución:** **9.93 segundos**
   - **Código de retorno:** **`0`**

2. **Validación de Inicio de la Aplicación de Escritorio:**
   - Se ejecutó una prueba de ciclo de vida verificando la instanciación de `MainWindow`, el conteo de 5 páginas en el contenedor `QStackedWidget` y el cierre controlado mediante temporizador.
   - Resultado: **Aprobada sin errores ni excepciones.**

3. **Verificación Estática del Script SQL:**
   - Se validaron dependencias topológicas entre claves foráneas: `audit_runs`, `resources`, `audit_rules` y `access_profiles` se declaran primero; seguidas por tablas intermedias y finalmente `findings` y `audit_evidence`.
   - Coincide plenamente con las sentencias `SELECT` de [`repository.py`](file:///c:/Users/andre/Desktop/TESIS/sistema/src/auditoria_iam/database/repository.py) y los `INSERT` de [`persistence.py`](file:///c:/Users/andre/Desktop/TESIS/sistema/src/auditoria_iam/database/persistence.py).

4. **Verificación de Exclusiones en `.gitignore`:**
   - Comentario residual `#hola jajajaajajja` eliminado.
   - Reglas activas para `.env`, `.venv/`, `*.zip`, `.pytest_cache/`, `*.egg-info/`, `__pycache__/` y `*.log`.

---

### 6. RESTRICCIONES RESPETADAS

- **Cero modificaciones a la lógica del sistema:** Motor, reglas (IAM-001 a IAM-004), modelos, adaptador Boto3, UI, reportes, repositorio y persistencia se mantuvieron intactos.
- **Cero modificaciones a la base de datos MySQL:** No se ejecutó el script `init_database_upharven.sql` ni sentencias DDL/DML contra la base de datos real.
- **Cero acciones sobre AWS:** No se conectó a una cuenta real de AWS ni se usaron credenciales en vivo.
- **Protección de secretos:** No se expusieron valores reales del archivo `.env`; `.env.example` contiene únicamente valores demostrativos.

---

### 7. LIMITACIONES Y ALCANCE

1. **Simulador Determinista:** Diseñado para fines de laboratorio y demostración; no refleja datos reales de UPHARVEN C.A.
2. **Conexión en Vivo con AWS:** Requiere credenciales que la empresa no facilitó; interoperabilidad validada mediante `botocore.stub.Stubber` y pruebas unitarias.
3. **Herramienta Diagnóstica:** No sustituye una certificación formal de un SGSI bajo ISO/IEC 27001.
4. **Alcance Técnico:** Limitado a cuatro controles de identidad en AWS IAM (5.15, 5.16, 5.18, 8.5).

---

### 8. ESTADO FINAL DE LA ENTREGA

El sistema se encuentra **completamente documentado, probado al 100% y listo para su entrega académica formal y demostración en la predefensa de grado**.

