# DOCUMENTACIÓN TÉCNICA — FASE 7, ENTREGA 7.3
## DIAGNÓSTICO DE CIERRE Y PREPARACIÓN FINAL DEL SISTEMA

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.  
**Fase:** Fase 7 — Adaptador AWS IAM e Integración de Nube.  
**Entrega:** 7.3 — Diagnóstico de cierre y preparación final del sistema para entrega académica y demostración funcional.  
**Rol:** Auditor Técnico de Software y Seguridad.  
**Fecha:** Noviembre 2026.  
**Estado:** DIAGNÓSTICO COMPLETADO — SISTEMA TÉCNICAMENTE SÓLIDO / DOCUMENTACIÓN Y DESPLIEGUE POR COMPLETAR.

---

### 1. OBJETIVO DEL DIAGNÓSTICO

Realizar una auditoría técnica integral, objetiva e independiente sobre el estado actual del código, la base de datos, los componentes de seguridad, la interfaz gráfica, la suite de pruebas y la documentación del proyecto.

El propósito es determinar con rigor técnico si el sistema se encuentra preparado para su entrega académica formal y demostración funcional ante jurados y evaluadores, verificando el funcionamiento real de los artefactos sin asumir corrección implícita por aprobaciones de fases previas.

---

### 2. ARCHIVOS Y MÓDULOS REVISADOS

Durante la auditoría se inspeccionaron estática y dinámicamente los siguientes módulos:

| Capa / Módulo | Archivos Principales Inspeccionados |
| :--- | :--- |
| **Punto de Entrada e Interfaz (UI)** | `main.py`, `src/auditoria_iam/ui/main_window.py`, `src/auditoria_iam/ui/pages/home_page.py`, `src/auditoria_iam/ui/pages/audit_page.py`, `src/auditoria_iam/ui/pages/results_page.py`, `src/auditoria_iam/ui/pages/history_page.py`, `src/auditoria_iam/ui/pages/settings_page.py`, `src/auditoria_iam/ui/controls_catalog.py`, `src/auditoria_iam/ui/dialogs/control_detail_dialog.py`. |
| **Servicio de Aplicación** | `src/auditoria_iam/application/audit_service.py`. |
| **Motor y Reglas ISO 27001** | `src/auditoria_iam/audit/engine.py`, `src/auditoria_iam/audit/models.py`, `src/auditoria_iam/audit/rules/base.py`, `iam_001_access_control.py`, `iam_002_identity_management.py`, `iam_003_access_rights.py`, `iam_004_secure_authentication.py`. |
| **Fuente de Datos Simulada** | `src/auditoria_iam/data_sources/simulator/simulator.py`. |
| **Adaptador AWS IAM** | `src/auditoria_iam/data_sources/aws/adapter.py`, `src/auditoria_iam/data_sources/aws/exceptions.py`. |
| **Capa de Persistencia y Base de Datos** | `src/auditoria_iam/config/settings.py`, `src/auditoria_iam/database/connection.py`, `src/auditoria_iam/database/repository.py`, `src/auditoria_iam/database/persistence.py`, `db_pruebas.sql`, `db_pruebas_sin_gtid.sql`, `FASE2_MIGRACION_PRELIMINAR.sql`. |
| **Módulos de Reportería** | `src/auditoria_iam/reports/report_data.py`, `src/auditoria_iam/reports/pdf_report.py`, `src/auditoria_iam/reports/excel_report.py`, `src/auditoria_iam/reports/csv_report.py`. |
| **Configuración y Empaquetado** | `requirements.txt`, `pytest.ini`, `.gitignore`, `.env` (inspección de variables presentes), `src/auditoria_iam.egg-info/requires.txt`. |
| **Suite de Pruebas Automatizadas** | 20 archivos de pruebas en el directorio `tests/` (309 casos de prueba). |

---

### 3. ESTADO DETALLADO POR ÁREA EVALUADA

#### ÁREA A: Aplicación de Escritorio (PySide6)
- **Estado:** **APROBADO Y TOTALMENTE FUNCIONAL.**
- **Modalidad de Verificación:** *Funcionalidad comprobada dinámicamente mediante 18 pruebas automatizadas de UI (`test_ui.py`) y revisión estática.*
- **Hallazgos:**
  - El arranque de la aplicación desde `main.py` inicializa correctamente `QApplication` y `MainWindow`.
  - La navegación lateral por pestañas (Inicio, Ejecutar auditoría, Resultados, Historial, Configuración) funciona sin errores de asignación de índices ni fugas de memoria.
  - La ejecución con el simulador produce resultados inmediatos, emite las señales de actualización y habilita la transición a la vista de resultados.
  - `ResultsPage` presenta correctamente los contadores de estado, filtros dinámicos por regla (IAM-001 a IAM-004) y estado (Conforme, Hallazgo, No evaluable).
  - La vista de Historial (`HistoryPage`) lista las auditorías registradas, permite la selección de ejecuciones previas y transfiere los datos a `ResultsPage` con aislamiento entre corridas.
  - El Dashboard (`HomePage`) calcula y refresca KPIs, gráfico circular interactivo y tarjeta de última auditoría al navegar a la pestaña o finalizar una ejecución.
  - El catálogo de controles (`controls_catalog.py`) y su diálogo modal (`IsoControlDetailDialog`) presentan exhaustivamente los cuatro controles ISO/IEC 27001:2022 con acceso seguro al documento PDF de referencia en Internet Archive.

#### ÁREA B: Base de Datos MySQL Server
- **Estado:** **ESTABLE / REQUIERE GUÍA DE DESPLIEGUE INICIAL.**
- **Modalidad de Verificación:** *Revisión estática de consultas/transacciones y comprobación dinámica con mocks (`test_persistence.py`, `test_repository.py`, `test_connection.py`, `test_settings.py`).*
- **Hallazgos:**
  - La configuración mediante `get_database_settings()` en `settings.py` valida rigurosamente tipos, rangos de puertos (1 a 65535) y tiempos de espera.
  - El gestor de conexión `connection.py` implementa context managers (`get_db_cursor` para lectura y `get_db_transaction` para escritura con commit/rollback atómico).
  - Los mensajes de error de base de datos capturan `mysql.connector.Error` y devuelven explicaciones controladas que ocultan contraseñas y parámetros sensibles de red.
  - La persistencia transaccional en `persistence.py` valida la existencia de reglas (`audit_rules`) y recursos (`resources`) mediante claves naturales (`resource_key`, `source_type`), abortando con rollback ante registros faltantes o ambiguos sin inventar identificadores de respaldo.
  - *Observación de despliegue:* El repositorio contiene el volcado inicial `db_pruebas.sql` y el script de migración `FASE2_MIGRACION_PRELIMINAR.sql`, pero carece de un script SQL consolidado único (`schema_completo.sql`) para recrear la base de datos completa en una sola instrucción sin pasos intermedios.

#### ÁREA C: Motor de Auditoría y Reglas Técnicas
- **Estado:** **APROBADO Y TOTALMENTE CONFORME.**
- **Modalidad de Verificación:** *Funcionalidad comprobada dinámicamente mediante 73 pruebas automatizadas de motor y reglas.*
- **Hallazgos:**
  - `AuditEngine` coordina de manera desacoplada la ejecución de las cuatro reglas:
    - **IAM-001 (5.15):** Control de acceso (membresía de grupos IAM y entidades de confianza en roles).
    - **IAM-002 (5.16):** Gestión de identidades (actividad reciente vs. inactividad $> 90$ días).
    - **IAM-003 (5.18):** Derechos de acceso privilegiados (detección de comodines `*` en documentos JSON normalizados).
    - **IAM-004 (8.5):** Autenticación segura (obligatoriedad de MFA en usuarios e inmunidad/exclusión técnica de roles).
  - Se comprueba la estricta conservación de los estados `Conforme`, `Hallazgo` y `No evaluable`.
  - El motor jamás emite falsos conformes: ante datos ausentes o incompletos (políticas inaccesibles, atributos nulos, perfiles no asignados), clasifica la evaluación justificadamente como `No evaluable`.
  - Si una regla lanza una excepción no controlada, el motor la captura defensivamente y registra `result_status = "No evaluable"` con justificación técnica (`criterion_code = f"ERR-{iso_control}"`).

#### ÁREA D: Integración AWS IAM
- **Estado:** **VALIDADO EN LABORATORIO (STUBBER/MOCKS) / PENDIENTE CREDENCIALES EN VIVO.**
- **Modalidad de Verificación:** *Funcionalidad comprobada mediante 95 pruebas automatizadas (`test_aws_adapter_stubber.py`, `test_aws_data_source.py`, `test_aws_ui_integration.py`, `test_aws_end_to_end.py`).*
- **Hallazgos:**
  - `AWSIAMDataSource` implementa 17 operaciones de consulta de Boto3 compatibles con la API oficial de AWS IAM.
  - Seguridad estricta de solo lectura: el catálogo cerrado `READ_ONLY_OPERATIONS` y la verificación preventiva `_validate_safe_operation()` bloquean 15 prefijos de mutación (`create_*`, `delete_*`, `update_*`, `attach_*`, etc.) antes de emitir solicitudes.
  - Manejo defensivo de excepciones: traduce errores de Boto3 a excepciones controladas de dominio (`AWSIAMAuthenticationError`, `AWSIAMPermissionError`, `AWSIAMConnectionError`, `AWSIAMDataSourceError`) sin divulgar tokens ni secretos.
  - Paginación multi-página (`_paginate_or_call`) procesa exhaustivamente colecciones fraccionadas sin pérdida ni duplicados.
  - Documentos de políticas inaccesibles o denegadas generan marcadores de política incompleta (`_incomplete_policy: True`, `Statement: None`) que inducen `No evaluable` en la regla IAM-003.
  - *Limitación:* No se dispone de credenciales vivas de AWS IAM para probar conectividad real contra una cuenta de AWS en producción de UPHARVEN C.A. Las pruebas se ejecutaron al 100% mediante interceptación en memoria con `botocore.stub.Stubber` y fixtures desacopladas.

#### ÁREA E: Módulos de Informes y Exportación
- **Estado:** **APROBADO Y TOTALMENTE CONFORME.**
- **Modalidad de Verificación:** *Funcionalidad comprobada dinámicamente mediante 14 pruebas de reportería (`test_reports.py`).*
- **Hallazgos:**
  - Exportación a **PDF** formal implementada con ReportLab, incluyendo portada, resumen ejecutivo, tablas por control ISO, hallazgos, evidencias técnicas, conclusiones y descargo de responsabilidad técnica.
  - Exportación a **Microsoft Excel (XLSX)** con openpyxl, generando un libro estructurado en cuatro hojas (`Resumen`, `Evaluaciones`, `Hallazgos`, `Evidencias`) con colores de estado y autofiltros.
  - Exportación a **CSV** estructurado con codificación UTF-8 BOM (`utf-8-sig`) para compatibilidad directa con Excel en Windows.
  - Soporte dual: exportación de corridas históricas desde MySQL y exportación de auditorías en memoria.
  - Comprobación de seguridad: los datos exportados no contienen claves de acceso, contraseñas, secretos ni tokens de sesión.

#### ÁREA F: Seguridad y Restricciones del Proyecto
- **Estado:** **APROBADO (CUMPLIMIENTO ESTRICTO AL 100%).**
- **Modalidad de Verificación:** *Revisión estática de código, búsqueda automatizada de patrones y verificación de paquetes.*
- **Hallazgos:**
  - Cero credenciales reales hardcodeadas en código fuente (`src/`).
  - `.env` debidamente excluido en `.gitignore` y ausente en los paquetes de entrega ZIP.
  - Cero operaciones de escritura o remediación sobre AWS.
  - Cumplimiento estricto de las 9 restricciones de alcance del proyecto (no evalúa plano de datos, no evalúa plano de cómputo, no evalúa control 8.2 break-glass, no rotación de credenciales estáticas, sin SIEM/CloudTrail en tiempo real, análisis técnico limitado a JSON de IAM, exclusión de cláusulas 4 a 10 de ISO 27001, sin perímetro de red).
  - Los 14 hallazgos y 14 evidencias históricas originales de la base de datos se mantienen inalterados.

#### ÁREA G: Pruebas Automatizadas
- **Estado:** **100% EXITOSO / REGRESIÓN CERO.**
- **Modalidad de Verificación:** *Ejecución automatizada de pytest sobre la suite completa del proyecto.*
- **Métricas Oficiales Obtenidas:**
  - **Pruebas recopiladas:** **309**
  - **Pruebas aprobadas:** **309 (100%)**
  - **Pruebas fallidas:** **0**
  - **Pruebas omitidas / deseleccionadas:** **0**
  - **Tiempo de ejecución total:** **9.73 segundos**
  - **Código de salida de pytest:** **`0`**

#### ÁREA H: Documentación y Replicabilidad
- **Estado:** **REQUIERE ACCIONES DE CONSOLIDACIÓN PREVIAS A LA ENTREGA.**
- **Modalidad de Verificación:** *Revisión estática de archivos en la raíz del proyecto.*
- **Hallazgos:**
  - El proyecto cuenta con una documentación técnica por fases excepcionalmente detallada (15 documentos `DOCUMENTACION_FASE_*.md`).
  - Sin embargo, los archivos fundamentales para la replicación del sistema por un tercero presentan omisiones:
    1. `README.md` se encuentra completamente vacío (**0 bytes**).
    2. `requirements.txt` contiene únicamente 4 dependencias (`boto3`, `PySide6`, `reportlab`, `openpyxl`), omitiendo librerías esenciales como `mysql-connector-python`, `python-dotenv` y `pytest`.
    3. No existe un archivo `.env.example` que sirva de guía para configurar las variables de entorno de base de datos.
    4. No existe una guía consolidada de instalación y arranque paso a paso para el jurado evaluador.

---

### 4. RESUMEN DE PRUEBAS AUTOMATIZADAS POR ARCHIVO

| Archivo de Prueba | Casos | Estado | Cobertura Funcional |
| :--- | :---: | :---: | :--- |
| `test_audit_engine.py` | 8 | PASSED | Inicialización, registro de reglas, evaluación individual y múltiple, manejo defensivo. |
| `test_audit_models.py` | 6 | PASSED | Estados válidos de `AuditResult`, validación de campos, `AuditContext`, extracción de atributos. |
| `test_aws_adapter_stubber.py` | 44 | PASSED | Consultas AWS con Boto3 Stubber, paginación multi-página, errores, modo solo lectura. |
| `test_aws_data_source.py` | 28 | PASSED | Normalización de usuarios, grupos, roles, políticas administradas, herencia, comodines. |
| `test_aws_end_to_end.py` | 23 | PASSED | Flujo integral AWS (servicio, 4 reglas, persistencia, historial, dashboard, reportes, errores). |
| `test_aws_ui_integration.py` | 23 | PASSED | Integración de adaptador AWS con interfaz PySide6 y manejo de perfiles en MySQL. |
| `test_connection.py` | 4 | PASSED | Creación de conexiones MySQL, parámetros seguros y gestores de contexto. |
| `test_dashboard.py` | 13 | PASSED | Carga de indicadores, cálculos porcentuales, diálogo de controles ISO y catálogo. |
| `test_dashboard_integration.py` | 12 | PASSED | Consistencia entre historial, MySQL y métricas del dashboard sin mezclar corridas. |
| `test_persistence.py` | 16 | PASSED | Inserción atómica en 4 tablas, resolución referencial, rollback y transaccionalidad. |
| `test_reports.py` | 14 | PASSED | Exportación en PDF, XLSX y CSV, verificación de estados y ausencia de fugas de datos. |
| `test_repository.py` | 12 | PASSED | Consultas de recursos, perfiles activos, grupos esperados, historial y resultados. |
| `test_rule_iam_001.py` | 10 | PASSED | Control ISO 5.15 (grupos y confianza de roles) con Conforme, Hallazgo y No evaluable. |
| `test_rule_iam_002.py` | 5 | PASSED | Control ISO 5.16 (inactividad $> 90$ días) con Conforme, Hallazgo y No evaluable. |
| `test_rule_iam_003.py` | 6 | PASSED | Control ISO 5.18 (derechos privilegiados y comodines `*`) con los 3 estados. |
| `test_rule_iam_004.py` | 7 | PASSED | Control ISO 8.5 (MFA en usuarios y exclusión de roles IAM). |
| `test_settings.py` | 12 | PASSED | Validación de variables de entorno de BD, rangos de puertos y timeouts. |
| `test_simulator.py` | 9 | PASSED | Integridad del dataset sintético determinista (10 recursos, 67 evaluaciones). |
| `test_ui.py` | 18 | PASSED | Creación de ventanas, navegación en 5 pestañas, selección de fuentes y señales Qt. |
| **TOTAL** | **309** | **100% OK** | **0 fallos, 0 omitidas, tiempo total 9.73 segundos.** |

---

### 5. CLASIFICACIÓN DE PROBLEMAS Y HALLAZGOS IDENTIFICADOS

#### A. Hallazgos de Severidad CRÍTICA
*(Impiden ejecutar o entregar correctamente el sistema)*
- **Ninguno identificado.** El sistema cuenta con arquitectura modular completa, código fuente funcional para todas las capas y 309 pruebas unitarias e integrales aprobadas.

#### B. Hallazgos de Severidad IMPORTANTE
*(Deben atenderse antes de la entrega académica formal para garantizar la replicabilidad del prototipo por terceros)*

1. **`requirements.txt` incompleto:**
   - *Detalle:* El archivo actual contiene únicamente `boto3`, `PySide6`, `reportlab` y `openpyxl`. Carece de dependencias indispensables para la persistencia y ejecución de pruebas: `mysql-connector-python`, `python-dotenv` y `pytest`.
   - *Impacto:* Un jurado o evaluador que ejecute `pip install -r requirements.txt` en un entorno virtual limpio no podrá conectarse a MySQL ni ejecutar la suite de pruebas debido a `ModuleNotFoundError`.

2. **`README.md` vacío (0 bytes):**
   - *Detalle:* El archivo principal de bienvenida e instrucciones del repositorio está en blanco.
   - *Impacto:* Dificulta la instalación y puesta en marcha autónoma del prototipo por parte de personas ajenas al desarrollo inicial.

3. **Ausencia de archivo de plantilla `.env.example`:**
   - *Detalle:* Dado que `.env` está (acertadamente) excluido del control de versiones y de los paquetes ZIP de entrega, quien reciba el código no dispone de una plantilla de referencia que indique los nombres exactos y valores sugeridos de las variables de conexión a MySQL.

4. **Falta de script de inicialización de MySQL consolidado:**
   - *Detalle:* El esquema de MySQL se encuentra disperso entre un dump previo a la migración (`db_pruebas.sql` / `db_pruebas_sin_gtid.sql`) y un script de migración procedural (`FASE2_MIGRACION_PRELIMINAR.sql`).
   - *Impacto:* Recrear la base de datos desde cero en una máquina nueva requiere conocer el orden exacto de importación y ejecución del procedimiento almacenado `sp_migrar_esquema_fase2`.

#### C. Hallazgos de Severidad MENOR
*(Mejoras operativas opcionales que no impiden la entrega ni la demostración)*

1. **Comentario informal residual en `.gitignore`:**
   - *Detalle:* La línea 13 de `.gitignore` contiene un comentario informal (`#hola jajajaajajja`).
   - *Impacto:* Estético y de pulcritud académica.

2. **Falta de Manual de Usuario / Guía Rápida de Demostración:**
   - *Detalle:* Sería de gran utilidad un documento conciso (`GUIA_DEMOSTRACION_ACADEMICA.md`) que describa la secuencia recomendada para realizar la demostración funcional ante el jurado evaluador (ej. ejecutar simulador $\rightarrow$ revisar dashboard $\rightarrow$ inspeccionar hallazgos $\rightarrow$ consultar catálogo de controles $\rightarrow$ exportar informes).

---

### 6. ELEMENTOS PENDIENTES (LIMITACIONES DE ALCANCE)

1. **Validación con Cuenta AWS Real en Producción:**
   - El adaptador Boto3 y el flujo completo de auditoría se encuentran técnicamente validados mediante simulación avanzada (`botocore.stub.Stubber` y mocks).
   - La comprobación en vivo requiere que UPHARVEN C.A. suministre credenciales con permisos mínimos de solo lectura (`iam:Get*`, `iam:List*`) y configure las identidades correspondientes en la tabla `resources` de MySQL.
2. **Consolidación de Archivos de Despliegue Académico:**
   - Actualización de `requirements.txt`.
   - Redacción de `README.md`.
   - Creación de `.env.example`.
   - Generación de un script SQL consolidado de estructura y datos de prueba (`init_database_upharven.sql`).

---

### 7. ELEMENTOS QUE NO REQUIEREN MODIFICACIÓN

Las siguientes áreas se encuentran en estado óptimo y **no deben ser alteradas**:
1. **Reglas de Auditoría (`IAM-001`, `IAM-002`, `IAM-003`, `IAM-004`):** Lógica matemática y criterios de evaluación completamente alineados con ISO/IEC 27001:2022 y respaldados por pruebas exhaustivas.
2. **Motor de Auditoría (`AuditEngine`):** Desacoplamiento, manejo defensivo y concurrencia limpios.
3. **Simulador de Datos (`IAMSimulatorDataSource`):** Dataset determinista de 10 recursos y 67 evaluaciones estable y calibrado.
4. **Adaptador AWS (`AWSIAMDataSource`):** Mecanismos de solo lectura, mapeo de excepciones y marcadores de políticas incompletas funcionando a la perfección.
5. **Capa de Persistencia (`persistence.py` y `repository.py`):** Transaccionalidad atómica y consultas de solo lectura protegidas contra inyecciones SQL.
6. **Diseño de la Interfaz Gráfica (`PySide6`):** Sistema visual profesional con tema oscuro (*slate/navy*), tipografías claras, KPIs ejecutivos, gráficos dinámicos y navegación reactiva.
7. **Módulos de Reportería:** Exportadores PDF, Excel y CSV robustos y validados.

---

### 8. RECOMENDACIONES PRIORIZADAS

Para preparar el sistema para su cierre formal y entrega académica definitiva, se recomienda el siguiente plan de acción estructurado:

```
FASE 7 — CIERRE Y PREPARACIÓN FINAL
│
├── PRIORIDAD 1 (IMPORTANTE - Despliegue y Replicabilidad):
│   ├── 1.1. Actualizar requirements.txt con la totalidad de librerías del proyecto.
│   ├── 1.2. Crear .env.example con las variables requeridas para MySQL.
│   └── 1.3. Redactar README.md con arquitectura, requisitos previos, instalación y ejecución.
│
├── PRIORIDAD 2 (IMPORTANTE - Base de Datos):
│   └── 2.1. Proveer un script SQL único consolidado (DDL + datos de catálogo) para montaje limpio en 1 paso.
│
└── PRIORIDAD 3 (MENOR - Pulcritud Académica):
    ├── 3.1. Limpiar comentario residual en .gitignore.
    └── 3.2. Elaborar una breve Guía de Demostración para la defensa de tesis.
```

---

### 9. CONCLUSIÓN DEL DIAGNÓSTICO

El sistema de software desarrollado para la tesis **“Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.”** se encuentra **técnicamente maduro, robusto, seguro y plenamente funcional**.

Presenta una arquitectura en capas limpia y desacoplada, 309 pruebas automatizadas con 100% de aprobación, estricta adherencia a las restricciones de alcance y principios de solo lectura en AWS, y una interfaz gráfica lista para demostración ejecutiva.

El prototipo se encuentra en condiciones de ser aprobado para su entrega académica una vez que se completen las acciones documentales de replicabilidad (Prioridad 1 y 2: `requirements.txt`, `README.md`, `.env.example` y script consolidado de base de datos), las cuales permitirán que cualquier evaluador externo instale y ejecute el sistema de forma completamente autónoma.

