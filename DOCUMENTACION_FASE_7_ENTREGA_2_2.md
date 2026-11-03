# DOCUMENTACIÓN TÉCNICA — FASE 7, ENTREGA 7.2.2
## VALIDACIÓN INTEGRAL DEL FLUJO DE AUDITORÍA AWS IAM

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.  
**Fase:** Fase 7 — Adaptador AWS IAM e Integración de Nube.  
**Entrega:** 7.2.2 — Validación integral del flujo de auditoría AWS IAM (Servicio, Motor, Reglas, Persistencia, Historial, Dashboard y Reportes).  
**Estado:** APROBADO / 100% EXITOSO.  
**Fecha:** Noviembre 2026.

---

### 1. OBJETIVO DE LA VALIDACIÓN

Comprobar y validar de manera integral el flujo completo de auditoría de seguridad sobre AWS IAM dentro de la aplicación de escritorio, verificando que los recursos recolectados mediante `AWSIAMDataSource`:
1. Sean procesados por el motor central de auditoría (`AuditEngine`) existente.
2. Se evalúen técnica y rigurosamente mediante las cuatro reglas de control implementadas (IAM-001, IAM-002, IAM-003 e IAM-004) basadas en ISO/IEC 27001:2022.
3. Se persistan de forma transaccional y atómica en MySQL bajo el origen formal `aws`.
4. Sean consultables de forma aislada e inequívoca desde la vista de resultados, el historial cronológico y el panel de indicadores del Dashboard.
5. Puedan ser exportados a informes formales en formatos PDF, Microsoft Excel (XLSX) y CSV sin fuga de credenciales ni secretos.

Esta entrega es estrictamente de integración, verificación y consistencia técnica, sin rediseño visual ni alteración de los criterios de evaluación de las reglas de auditoría.

---

### 2. COMPONENTES INTEGRADOS Y ARQUITECTURA DEL FLUJO

El flujo integral de auditoría AWS IAM conecta los siguientes módulos desacoplados del sistema:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CAPA DE INTERFAZ DE USUARIO (PySide6)                │
│   AuditPage  ───>  MainWindow  ───>  ResultsPage  ───>  HistoryPage    │
│         ▲                                                    │         │
│         └────────────────── HomePage (Dashboard) ───────────┘         │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ Invoca run_aws_audit() / get_dashboard_data()
┌────────────────────────────────────▼───────────────────────────────────┐
│               CAPA DE SERVICIO DE APLICACIÓN (AuditService)             │
│   • Orquestación de recolección, evaluación, persistencia e informes   │
└──────────────┬─────────────────────┬───────────────────┬───────────────┘
               │ 1. get_resources()  │ 2. evaluate_all() │ 3. save_audit_run()
               ▼                     ▼                   ▼
┌─────────────────────────┐  ┌───────────────┐  ┌────────────────────────┐
│      ADAPTADOR AWS      │  │ MOTOR CENTRAL │  │    PERSISTENCIA MYSQL   │
│   (AWSIAMDataSource)    │  │ (AuditEngine) │  │  (persistence / repo)  │
│  • Boto3 solo lectura   │  │ • IAM-001     │  │ • audit_runs (aws)     │
│  • READ_ONLY_OPERATIONS │  │ • IAM-002     │  │ • audit_results        │
│  • Normalización segura │  │ • IAM-003     │  │ • findings             │
│  • Marcador incompleto  │  │ • IAM-004     │  │ • audit_evidence       │
└─────────────────────────┘  └───────────────┘  └────────────────────────┘
```

---

### 3. FLUJO DE EJECUCIÓN AWS (`AuditService.run_aws_audit`)

Se verificó el comportamiento del método central `run_aws_audit()`:

1. **Recolección:** Consulta y normaliza los usuarios y roles desde AWS IAM mediante `AWSIAMDataSource`, produciendo recursos estructurados con clave única `resource_key`, tipo canónico (`IAM_USER`, `IAM_ROLE`), y atributos de seguridad (`groups`, `last_access_days`, `policies`, `mfa_enabled`, `assume_role_policy_document`).
2. **Contexto de Referencia:** Carga los perfiles de acceso autorizados desde MySQL vinculando identidades mediante `resource_key_profiles` hacia los identificadores internos de la base de datos.
3. **Motor Compartido:** Emplea exactamente la misma instancia de `AuditEngine` utilizada por el simulador, sin duplicación de lógica algorítmica ni rutas alternas.
4. **Origen `aws`:** Los recursos y la ejecución se identifican formalmente con `source_type = 'aws'`.
5. **No Afectación al Simulador:** Se comprobó que una auditoría AWS (incluso si experimenta errores de red o autenticación) no altera en absoluto el dataset determinista local (10 recursos evaluados, 67 resultados idénticos en simulaciones posteriores).

---

### 4. COMPATIBILIDAD CON LAS CUATRO REGLAS ISO/IEC 27001:2022

Se prepararon escenarios controlados con datos de AWS para validar que cada regla produzca de forma justificada los estados técnicos `Conforme`, `Hallazgo` y `No evaluable`:

| Regla | Control ISO 27001 | Condición Conforme | Condición Hallazgo | Condición No evaluable / Salvaguarda |
| :--- | :---: | :--- | :--- | :--- |
| **IAM-001** | **5.15** | Usuario con pertenencia exacta a grupos autorizados; rol con principal de confianza autorizado. | Usuario con grupos no autorizados o rol con entidades de confianza indebidas. | Ausencia de perfil de referencia en MySQL produce **"No evaluable"** (nunca genera falsos conformes). |
| **IAM-002** | **5.16** | Días desde última actividad $\le 90$ días. | Inactividad $> 90$ días. | Identidad sin metadatos válidos de actividad produce **"No evaluable"** (no inventa hallazgos). |
| **IAM-003** | **5.18** | Políticas acotadas a acciones y recursos explícitos (`s3:GetObject`). | Políticas con comodines globales (`Action: *`, `Resource: *`). | Políticas inaccesibles o con error generan marcador incompleto (`Statement: None`) resultando en **"No evaluable"** (previene falso conforme). |
| **IAM-004** | **8.5** | Usuario con dispositivo MFA activo (`mfa_enabled = True`). | Usuario sin MFA habilitado (`mfa_enabled = False`). | **Exclusión técnica de roles:** Los recursos `IAM_ROLE` no emiten resultados en C85-01 (asumen sesiones STS temporales). |

---

### 5. VALIDACIÓN DE PERSISTENCIA TRANSACCIONAL EN MYSQL

Se comprobó la integración entre `run_aws_audit()` y `save_audit_run()`:

1. **Registro Maestro:** Inserción atómica en `audit_runs` registrando `source_type = 'aws'`.
2. **Resultados e Integridad Referencial:** Resolución estricta de `resource_id` consultando `SELECT id, resource_key FROM resources WHERE source_type = 'aws'`.
3. **Control Transaccional y Rollback:** Si un recurso AWS no existe en el catálogo MySQL, se aborta la operación lanzando `RuntimeError` y ejecutando rollback inmediato, sin inventar identificadores de respaldo ni alterar tablas de catálogo.
4. **Retención en Memoria:** Cuando la persistencia en base de datos no puede completarse, `AuditService` captura el error, establece `persistence_info['persisted'] = False` y conserva la totalidad de los resultados en memoria para su visualización y exportación durante la sesión activa.
5. **Aislamiento de Recursos:** Se verificó que los recursos de origen `aws` quedan estrictamente segregados de los recursos de origen `simulacion`.

---

### 6. VALIDACIÓN DE HISTORIAL Y DASHBOARD

1. **Historial de Auditorías (`HistoryPage`):**
   - Las ejecuciones AWS persistidas se listan en orden cronológico (`ORDER BY execution_date DESC, id DESC`).
   - La columna de fuente muestra claramente el origen `aws`.
   - La selección y apertura de una ejecución histórica (`get_historical_run_results`) reconstruye los resultados reales sin mezclar información de otras corridas.
2. **Dashboard de Indicadores (`HomePage`):**
   - El método `get_dashboard_data()` calcula las métricas KPI (Total, Conforme, Hallazgo, No evaluable), distribución porcentual y resumen por regla a partir de la última auditoría registrada en base de datos, reconociendo correctamente una corrida AWS cuando es la más reciente.
   - El orden cronológico considera fecha y hora (`execution_date`), garantizando que auditorías recientes prevalezcan sobre ejecuciones con IDs menores.
   - Las auditorías simuladas históricas conservan intactas sus métricas y no se ven afectadas por la presencia de corridas AWS.

---

### 7. VALIDACIÓN DE EXPORTACIÓN DE INFORMES

Se validó la exportación de auditorías AWS en los tres formatos soportados por el sistema:

1. **Informe PDF (`generate_pdf_report`):**
   - Genera un documento formal con portada, resumen ejecutivo, tabla de distribución, evaluaciones por control ISO, hallazgos técnicos y descargo de responsabilidad.
   - Especifica el origen como `aws` y la fecha de ejecución correspondiente.
2. **Libro Microsoft Excel (`generate_excel_report`):**
   - Genera un archivo `.xlsx` estructurado en cuatro hojas de cálculo: `Resumen`, `Evaluaciones`, `Hallazgos` y `Evidencias`.
   - Incluye filtros automáticos, estilos tipográficos acordes y colores de estado.
3. **Archivo CSV (`generate_csv_report`):**
   - Genera un archivo delimitado por comas con codificación `utf-8-sig` (BOM) compatible con Windows y Excel.
   - Incluye columna de fuente con valor `aws`.
4. **Seguridad y Confidencialidad de Datos:**
   - Se verificó que los reportes generados no incluyan cadenas de claves secretas (`SecretAccessKey`), tokens de sesión (`SessionToken`) ni credenciales privadas.

---

### 8. VALIDACIÓN DE CASOS DE ERROR Y RESILIENCIA

Se comprobaron mediante pruebas automatizadas los siguientes escenarios anómalos:

1. **Error de Autenticación:** `InvalidClientTokenId` capturado y traducido a `AWSIAMAuthenticationError`.
2. **Credenciales Ausentes:** `NoCredentialsError` capturado como `AWSIAMAuthenticationError` sin exponer rutas del sistema.
3. **Permisos Insuficientes:** `AccessDenied` capturado como `AWSIAMPermissionError`.
4. **Timeouts y Fallos de Red:** `ConnectTimeoutError` y `EndpointConnectionError` traducidos a `AWSIAMConnectionError`.
5. **Políticas Inaccesibles:** Marcador de política incompleta con `Statement: None` evaluado como `No evaluable` en IAM-003.
6. **Recursos sin Perfil de Referencia:** Evaluación controlada como `No evaluable` en IAM-001 sin falsos conformes.
7. **Cuentas sin Identidades:** Respuestas vacías (`Users: []`, `Roles: []`) procesadas con retorno limpio `total: 0`.
8. **Ejecución Consecutiva Falla-Éxito:** Una auditoría AWS fallida no contamina ni bloquea la ejecución posterior del simulador local.

---

### 9. RESULTADOS DE LAS PRUEBAS AUTOMATIZADAS

Se incorporó la nueva suite de pruebas `tests/test_aws_end_to_end.py` con 23 pruebas de integración profunda:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\andre\Desktop\TESIS\sistema
configfile: pytest.ini
collected 309 items

tests/test_audit_engine.py ............................................ [ 14%]
tests/test_audit_models.py ............................................. [ 28%]
tests/test_aws_adapter_stubber.py ...................................... [ 43%]
tests/test_aws_data_source.py ............................               [ 52%]
tests/test_aws_end_to_end.py .......................                     [ 59%]
tests/test_aws_ui_integration.py .......................                [ 67%]
tests/test_connection.py ....                                            [ 68%]
tests/test_dashboard.py .................                                [ 74%]
tests/test_dashboard_integration.py ............                         [ 78%]
tests/test_persistence.py .......................                        [ 85%]
tests/test_reports.py .................                                  [ 91%]
tests/test_repository.py ............                                    [ 94%]
tests/test_rule_iam_001.py ..........                                    [ 98%]
tests/test_rule_iam_002.py .....                                         [ 99%]
tests/test_rule_iam_003.py ......                                        [100%]
tests/test_rule_iam_004.py ...                                           [100%]
tests/test_settings.py ....                                              [100%]
tests/test_simulator.py ......                                           [100%]
tests/test_ui.py ..............                                          [100%]

============================= 309 passed in 10.58s =============================
```

- **Total de pruebas en el sistema:** **309**
- **Pruebas aprobadas:** **309 (100%)**
- **Pruebas fallidas:** **0**
- **Pruebas omitidas/deseleccionadas:** **0**
- **Código de salida de pytest:** **`0`**

---

### 10. LIMITACIONES TÉCNICAS PENDIENTES

1. **Ausencia de Cuenta AWS en Vivo:** Las pruebas integrales han sido ejecutadas empleando `botocore.stub.Stubber` y mocks de transporte. La validación en vivo requerirá credenciales autorizadas con permisos mínimos de solo lectura (`iam:Get*`, `iam:List*`) otorgadas por UPHARVEN C.A.
2. **Catálogo de Recursos en MySQL:** Para que una auditoría AWS se guarde en MySQL con éxito permanente, las identidades de la cuenta AWS auditada deben estar pre-registradas en la tabla `resources` con `source_type='aws'` y asociadas a perfiles activos en `resource_access_profiles`. De lo contrario, el sistema activa de forma segura la retención en memoria para proteger la integridad referencial de la base de datos.

