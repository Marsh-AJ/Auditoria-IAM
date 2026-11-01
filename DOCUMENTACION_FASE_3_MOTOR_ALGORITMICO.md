# DOCUMENTACIÓN TÉCNICA — FASE 3
## MOTOR ALGORÍTMICO DEL SISTEMA DE AUDITORÍA IAM

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO/IEC 27001 para UPHARVEN C.A.  
**Fase:** Fase 3 — Construcción y Validación del Motor Algorítmico de Auditoría IAM  
**Fecha:** 1 de noviembre de 2026  
**Entorno de desarrollo:** Python 3.13.5 | Windows 11  
**Aislamiento y Alcance:** Ejecución técnica 100% local, desacoplada de AWS IAM (sin credenciales reales ni Boto3 en esta fase) y sin ejecución de sentencias DDL/DML sobre las bases de datos MySQL (`auditoria_iam_upharven` y `auditoria_iam_upharven_pruebas`).

---

## 1. CONTEXTO ACADÉMICO Y OBJETIVO DE LA FASE

El proyecto de grado tiene como objetivo el diseño e implementación de un prototipo de escritorio para la auditoría técnica automatizada de identidades y accesos en la nube, contrastando las configuraciones técnicas de AWS IAM frente a controles seleccionados de la norma **ISO/IEC 27001:2022**.

> [!IMPORTANT]
> **Aclaratoria sobre Datos Reales:** UPHARVEN C.A. no ha provisto acceso a cuentas reales de AWS ni datos productivos de infraestructura. Por consiguiente, todo el desarrollo, validación y prueba del motor algorítmico en esta fase se realiza mediante una fuente de datos simulados representativa (`simulator.py`), sin presentar resultados simulados como auditorías reales de la empresa.

### Objetivos Específicos Alcanzados en la Fase 3:
1. **Modelado y Contexto de Auditoría (`models.py`):** Definición de estructuras inmutables y tipadas para resultados granulares (`AuditResult`) y perfiles de referencia autorizados (`AuditContext`), con extracción defensiva de atributos JSON/dict.
2. **Arquitectura Extensible del Motor (`base.py`, `engine.py`):** Clase base abstracta (`BaseAuditRule`) y orquestador central (`AuditEngine`) con registro modular, ejecución individual o en lote, y captura de excepciones no controladas para garantizar que ningún fallo técnico impida la continuidad de la auditoría o genere falsos conformes.
3. **Implementación de Reglas Técnicas Acotadas (IAM-001 a IAM-004):**
   - **IAM-001 (Control 5.15 - Control de acceso):** Criterios C15-01 (grupos de usuarios), C15-02 (políticas de confianza de roles) y C15-03 (disponibilidad y compatibilidad del perfil de referencia).
   - **IAM-002 (Control 5.16 - Gestión de identidades):** Criterios C16-01 (estado de vigencia y ciclo de vida de identidades) y C16-02 (actividad reciente de la identidad frente al umbral operativo del prototipo).
   - **IAM-003 (Control 5.18 - Derechos de acceso):** Criterios C18-01 (ausencia de permisos irrestrictos globales mediante análisis de políticas JSON) y C18-02 (principio de mínimo privilegio).
   - **IAM-004 (Control 8.5 - Autenticación segura):** Criterio C85-01 (uso obligatorio de MFA en usuarios IAM).
4. **Exclusión Estricta del Control 8.2:** Se excluye formalmente el control ISO/IEC 27001:2022 8.2 (Derechos de acceso privilegiado). No se auditan privilegios administrativos ni se utilizan clasificaciones de superusuario o banderas auxiliares (`is_admin`, `has_admin_access`).
5. **Conjunto de Pruebas Unitarias Automatizadas:** Cobertura integral mediante 93 pruebas unitarias automatizadas ejecutadas con `pytest`, validando casos conformes, discrepancias (hallazgos), errores defensivos y prevención de falsos resultados.

---

## 2. ARQUITECTURA MODULAR DEL MOTOR

El motor algorítmico reside en el paquete `src.auditoria_iam.audit` y la fuente de datos simulada en `src.auditoria_iam.data_sources.simulator`:

```text
sistema/
├── src/
│   └── auditoria_iam/
│       ├── audit/
│       │   ├── __init__.py
│       │   ├── models.py                     # AuditResult, AuditContext, extractores
│       │   ├── engine.py                     # AuditEngine (orquestador defensivo)
│       │   └── rules/
│       │       ├── __init__.py
│       │       ├── base.py                   # BaseAuditRule (ABC)
│       │       ├── iam_001_access_control.py # Control 5.15 (C15-01, C15-02, C15-03)
│       │       ├── iam_002_identity_management.py # Control 5.16 (C16-01, C16-02)
│       │       ├── iam_003_access_rights.py  # Control 5.18 (C18-01, C18-02)
│       │       └── iam_004_secure_authentication.py # Control 8.5 (C85-01)
│       └── data_sources/
│           └── simulator/
│               ├── __init__.py
│               └── simulator.py              # Contexto y 10 recursos simulados
└── tests/
    ├── test_audit_models.py                  # Pruebas de modelos y utilidades
    ├── test_audit_engine.py                  # Pruebas del orquestador y manejo defensivo
    ├── test_rule_iam_001.py                  # Pruebas de la regla IAM-001
    ├── test_rule_iam_002.py                  # Pruebas de la regla IAM-002
    ├── test_rule_iam_003.py                  # Pruebas de la regla IAM-003
    ├── test_rule_iam_004.py                  # Pruebas de la regla IAM-004
    └── test_simulator.py                     # Pruebas de integridad del simulador
```

---

## 3. ESPECIFICACIÓN DE LOS MODELOS Y CONTEXTO (`models.py`)

### 3.1. `AuditResult`
Representa el resultado indivisible de la evaluación de un criterio específico sobre un recurso:
- `rule_code`: Código de la regla evaluadora (`IAM-001`, `IAM-002`, `IAM-003`, `IAM-004`).
- `criterion_code`: Código granular del criterio (`C15-01` a `C85-01`).
- `resource_id`: Identificador numérico o alfanumérico del recurso evaluado.
- `result_status`: Estado determinista, restringido estrictamente a:
  - `Conforme`: Se cumplen las condiciones normativas evaluadas.
  - `Hallazgo`: Se comprueba técnicamente una desviación o discrepancia no autorizada.
  - `No evaluable`: No se dispone de información suficiente, la estructura no es soportable con certeza o la comparación carece de un marco de referencia.
- `justification`: Explicación técnica redactada en lenguaje formal de auditoría.
- `profile_id`: Identificador del perfil de acceso utilizado como base de comparación (si aplica).
- `details`: Diccionario con detalles técnicos de la evaluación.
- `evidence`: Diccionario que resume las evidencias técnicas recolectadas (sin almacenar documentos JSON completos o sensibles).

### 3.2. `AuditContext`
Encapsula el marco de referencia formal autorizado, simulando las tablas relacionales de la base de datos:
- `profiles`: Catálogo de perfiles autorizados (`resource_access_profiles`).
- `expected_groups`: Mapeo de perfiles a grupos IAM autorizados (`profile_expected_groups`).
- `expected_trust_principals`: Mapeo de perfiles a principales de confianza autorizados (`profile_expected_trust_principals`).
- `resource_profiles`: Asignación formal recurso-perfil (`resource_profile_assignments`).

---

## 4. ESPECIFICACIÓN TÉCNICA DE LAS REGLAS DE AUDITORÍA

### 4.1. Regla IAM-001: Control de Acceso (ISO/IEC 27001:2022 Control 5.15)
- **C15-03 (Perfil de Referencia):** Valida que la identidad cuente con un perfil activo y que el tipo de recurso coincida estrictamente (`USER` con perfil `user`, `ROLE` con perfil `role`). Si el tipo de recurso es desconocido (no `USER` ni `ROLE`), o si el perfil está inactivo/ausente o tiene tipo incompatible, produce `No evaluable`.
- **C15-01 (Pertenencia a Grupos para Usuarios):** Compara los grupos observados del usuario con los grupos autorizados en el perfil. Si el perfil activo no posee grupos esperados registrados en el catálogo, retorna `No evaluable` para no emitir falsos conformes comparando conjuntos vacíos. Si existen grupos adicionales o faltantes, genera `Hallazgo`. Si coinciden exactamente, produce `Conforme`.
- **C15-02 (Política de Confianza para Roles):** Evalúa las declaraciones del documento `AssumeRolePolicyDocument`. Si `Statement` es una lista vacía (`[]`), retorna `No evaluable` en lugar de comparar conjuntos vacíos contra los principales esperados. Valida rigurosamente los tipos de `Principal` y `Action`: si los valores internos de `Principal` (claves o identificadores) o los elementos de `Action` contienen valores no admitidos (números, booleanos, objetos inválidos), retorna `No evaluable` sin convertirlos silenciosamente en listas vacías. Si la política contiene cláusulas con `Effect: "Deny"`, condiciones no soportadas o JSON malformado, retorna `No evaluable`. La evidencia registrada conserva únicamente información técnica resumida, sin incluir fragmentos de la política ni mensajes internos de excepciones. Si el perfil no cuenta con principales de confianza esperados, produce `No evaluable`. Si los principales o acciones difieren de los esperados, genera `Hallazgo`. Si coinciden exactamente, produce `Conforme`.

### 4.2. Regla IAM-002: Gestión de Identidades (ISO/IEC 27001:2022 Control 5.16)
- **C16-01 (Estado de Vigencia y Ciclo de Vida):** Identidades en estado `active`/`enabled` resultan `Conforme`. Identidades en estado `inactive`, `suspended` o `disabled` retornan `No evaluable` a menos que exista evidencia técnica explícita y no arbitraria de una deficiencia en el proceso de desprovisionamiento (`deprovisioning_flaw` o `deprovisioning_pending` como booleano `True` o confirmación textual unívoca), caso en el cual se genera `Hallazgo`. Valores arbitrarios (cadenas aleatorias, números) son rechazados retornando `No evaluable`.
- **C16-02 (Actividad Reciente de Identidades):** Evalúa los días de inactividad de la identidad (`last_access_days`) frente a un umbral operativo configurable (entero mayor o igual a cero, con 90 días por defecto). Se documenta expresamente que dicho umbral es un parámetro operativo del prototipo y no un requisito textual de la norma ISO/IEC 27001:2022. Se rechazan valores booleanos, flotantes, cadenas y números negativos. Si la inactividad supera el umbral, genera `Hallazgo`. Si es menor o igual, genera `Conforme`. Valores negativos, flotantes o ausentes producen `No evaluable`.

### 4.3. Regla IAM-003: Derechos de Acceso (ISO/IEC 27001:2022 Control 5.18)
- **Exclusión del Control 8.2:** No realiza clasificación de cuentas privilegiadas ni auditoría de superusuarios.
- **Extracción Defensiva de Políticas:** Distingue rigurosamente entre atributo ausente, lista vacía, sintaxis JSON malformada, tipos de elementos no admitidos y documentos analizables. La ausencia de atributos no relacionados con políticas (como grupos o MFA) no descarta las políticas JSON válidas disponibles.
- **Validación Estricta de Action y Resource:** Acepta exclusivamente cadenas no vacías o listas no vacías compuestas íntegramente por cadenas no vacías. Rechaza números, booleanos, objetos, listas mixtas y cadenas vacías sin realizar conversiones forzadas con `str()`, retornando `No evaluable`.
- **Validación Estricta de Condition:** Cualquier declaración que contenga la propiedad `Condition` (vacía, malformada o estructurada) retorna deterministamente `No evaluable` para no interpretar condiciones no soportables ni permitir que pasen inadvertidas. No se almacenan documentos completos en evidencia.
- **C18-01 (Ausencia de Permisos Irrestrictos Globales):** Analiza el contenido de los documentos de política JSON buscando declaraciones con `Effect: "Allow"` que otorguen comodines globales (`Action: "*"` y `Resource: "*"`, o `Action: "iam:*"` sobre `Resource: "*"`). Si no se dispone de documentos JSON (incluso si la identidad tiene nombres de políticas vinculadas como `AdministratorAccess`), retorna `No evaluable`. Políticas con declaraciones vacías (`Statement: []`), cláusulas `NotAction` o `NotResource`, o declaraciones malformadas, producen `No evaluable`. La conformidad se define como la ausencia de los patrones específicos evaluados, sin aseverar que la política sea globalmente infalible.
- **C18-02 (Principio de Mínimo Privilegio):** Retorna `No evaluable` de forma sistemática y justificada, documentando que la base de datos actual no dispone de un catálogo formal de permisos esperados por perfil para contrastar técnicamente el mínimo privilegio. Se eliminó la duplicidad previa de su definición en el código fuente.

### 4.4. Regla IAM-004: Autenticación Segura (ISO/IEC 27001:2022 Control 8.5)
- **C85-01 (Autenticación Multifactor - MFA):** Aplica a identidades de usuario IAM. Si `mfa_enabled` es `True`, produce `Conforme`. Si es `False`, genera `Hallazgo`. Para roles IAM, no aplica evaluación directa de credenciales humanas fijas, produciendo `No evaluable`.

---

## 5. FUENTE DE DATOS SIMULADA Y MATRIZ DE EVALUACIÓN (`simulator.py`)

El módulo `simulator.py` suministra 10 identidades técnicas representativas evaluadas sobre los 8 criterios del sistema:

| ID | Resource Key | Tipo | C15-01 | C15-02 | C15-03 | C16-01 | C16-02 | C18-01 | C18-02 | C85-01 |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| 1 | `ana.operaciones` | USER | Conforme | N/A | Conforme | Conforme | Conforme | Conforme | No evaluable | Conforme |
| 2 | `carlos.soporte` | USER | Hallazgo | N/A | Conforme | Conforme | Conforme | Hallazgo | No evaluable | Conforme |
| 3 | `usuario.inactivo` | USER | Conforme | N/A | Conforme | No evaluable | Hallazgo | No evaluable | No evaluable | Conforme |
| 4 | `cuenta.sin_mfa` | USER | Conforme | N/A | Conforme | Conforme | Conforme | No evaluable | No evaluable | Hallazgo |
| 5 | `usuario.sin_perfil` | USER | No evaluable | N/A | No evaluable | Conforme | Conforme | No evaluable | No evaluable | Conforme |
| 6 | `usuario.grupos_discrepantes` | USER | Hallazgo | N/A | Conforme | Conforme | Conforme | No evaluable | No evaluable | Conforme |
| 7 | `rol.operaciones_valido` | ROLE | N/A | Conforme | Conforme | Conforme | Conforme | Conforme | No evaluable | N/A |
| 8 | `rol.principal_no_autorizado` | ROLE | N/A | Hallazgo | Conforme | Conforme | Conforme | No evaluable | No evaluable | N/A |
| 9 | `rol.politica_no_soportada` | ROLE | N/A | No evaluable | Conforme | Conforme | Conforme | No evaluable | No evaluable | N/A |
| 10 | `usuario.datos_incompletos` | USER | No evaluable | N/A | Conforme | No evaluable | No evaluable | No evaluable | No evaluable | No evaluable |

### Resumen Estadístico de la Simulación:
- **Total de evaluaciones granulares ejecutadas:** 67 evaluaciones.
- **Conforme:** 36 evaluaciones (53.73%).
- **No evaluable:** 25 evaluaciones (37.31%).
- **Hallazgo:** 6 evaluaciones (8.96%).

---

## 6. VERIFICACIÓN Y PRUEBAS AUTOMATIZADAS

La suite completa de pruebas unitarias consta de 108 pruebas ejecutadas mediante `pytest`:

```text
tests\test_audit_engine.py ........                                      [  7%]
tests\test_audit_models.py ......                                        [ 12%]
tests\test_connection.py ......                                          [ 18%]
tests\test_repository.py ...................                             [ 36%]
tests\test_rule_iam_001.py ................                              [ 50%]
tests\test_rule_iam_002.py .............                                 [ 62%]
tests\test_rule_iam_003.py ...................                           [ 80%]
tests\test_rule_iam_004.py ......                                        [ 86%]
tests\test_settings.py .............                                     [ 98%]
tests\test_simulator.py ..                                               [100%]

============================= 108 passed in 0.69s =============================
```

---

## 7. CUMPLIMIENTO DE RESTRICCIONES TÉCNICAS

1. **Aislamiento de Bases de Datos:** No se ejecutó ninguna sentencia SQL ni se alteraron tablas o registros en `auditoria_iam_upharven` ni `auditoria_iam_upharven_pruebas`.
2. **Aislamiento de Nube:** No se realizaron conexiones a AWS ni llamadas mediante Boto3.
3. **Preservación del Alcance ISO:** No se incorporaron funcionalidades del control 8.2 ni se alteró el catálogo de 4 reglas y 8 criterios.
4. **Estados Deterministas:** Se mantuvieron exclusivamente los tres estados normativos (`Conforme`, `Hallazgo`, `No evaluable`).
5. **Configuración Segura:** No se alteró el archivo `.env` ni credenciales del sistema.

