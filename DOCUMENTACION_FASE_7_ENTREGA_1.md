# DOCUMENTACIÓN TÉCNICA — FASE 7 / ENTREGA 7.1
## Integración de AWS IAM con la Aplicación de Escritorio

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.  
**Fecha:** Noviembre 2026  
**Entorno de Ejecución:** Python 3.13.5, PySide6, Boto3, MySQL 8.0+, pytest 9.2.0

---

## 1. Resumen Ejecutivo de la Entrega 7.1

En la Entrega 7.1 se completó la integración operativa entre el adaptador de solo lectura de AWS IAM (`AWSIAMDataSource` con Boto3) y la interfaz gráfica de usuario de escritorio (`AuditPage`, `MainWindow`, `ResultsPage`, `HomePage`), orquestada a través del servicio de aplicación `AuditService`.

A partir de esta entrega:
- El usuario puede seleccionar **"AWS IAM (Nube)"** como fuente de datos en el selector de la pantalla de auditoría y presionar **"Iniciar Auditoría"**.
- El sistema ejecuta la recolección en vivo de identidades, grupos, roles y políticas de AWS IAM, normaliza los recursos al formato canónico del sistema, evalúa de manera determinista las 4 reglas de auditoría ISO/IEC 27001:2022 (`IAM-001`, `IAM-002`, `IAM-003`, `IAM-004`).
- Se carga el contexto de referencia desde MySQL utilizando la función real `get_active_profiles()` del repositorio, asociando los perfiles autorizados a los recursos de AWS tanto por `resource_key` unívoco como por identificador numérico en memoria.
- Ante fallos de conexión a la base de datos o consulta de perfiles, el sistema aborta de forma controlada mediante `RuntimeError` y notifica claramente al auditor en la interfaz, evitando continuar silenciosamente con un contexto vacío.
- Los resultados analíticos y cuantitativos se despliegan en la pantalla de resultados con soporte de exportación en PDF, Excel y CSV, incluso si la persistencia histórica en MySQL no se completa por falta de registro previo de los recursos en el catálogo.

La integración mantiene una política estricta de seguridad:
- Operaciones 100% de solo lectura (`list_*` y `get_*`).
- Bloqueo preventivo de operaciones de escritura (`create`, `update`, `delete`, `put`, `attach`, etc.).
- Sin credenciales hardcodeadas, expuestas en la UI, ni almacenadas en repositorios o logs.
- Preservación íntegra e inmutable del motor de reglas y del simulador local.

---

## 2. Arquitectura de Integración y Componentes Modificados

### 2.1. Capa de Aplicación (`src/auditoria_iam/application/audit_service.py`)
- **Ampliación de inicialización:** `AuditService.__init__(self, engine=None, aws_data_source=None)` permite inyectar o instanciar de forma perezosa el adaptador AWS.
- **Implementación de `_load_aws_audit_context()`:**
  - Consulta los perfiles activos mediante la función real `get_active_profiles()` de `repository.py`.
  - Recupera grupos esperados (`get_profile_expected_groups`) y principales de confianza autorizados (`get_profile_expected_trust_principals`).
  - Asocia perfiles a recursos AWS existentes en MySQL poblando tanto `resource_profiles` (por clave primaria numérica) como `resource_key_profiles` (por clave textual única `resource_key`).
  - Ante excepciones de base de datos, comunica el error controladamente mediante `RuntimeError` sin exponer credenciales.
- **Implementación de `run_aws_audit()`:**
  - Invoca `aws_data_source.get_resources()` para recolectar y normalizar en memoria usuarios y roles.
  - Carga el contexto de perfiles y mapea los identificadores en memoria a partir de `resource_key_profiles`.
  - Evalúa los recursos contra las 4 reglas mediante `AuditEngine.evaluate_all(resources, context)`.
  - Intenta la persistencia transaccional mediante `save_audit_run(source_type="aws")`. Si falta algún recurso en el catálogo MySQL, aborta con rollback, captura la excepción y notifica de manera descriptiva al auditor manteniendo los resultados disponibles en memoria.
- **Unificación en `run_audit(source_type=...)`:** Acepta `"simulador"` o `"aws"` despachando transparentemente al flujo correspondiente.

### 2.2. Modelos de Auditoría (`src/auditoria_iam/audit/models.py`)
- **Ampliación de `AuditContext`:**
  - Se incorporó el diccionario `resource_key_profiles: Dict[str, int] = field(default_factory=dict)` para permitir mapear perfiles mediante `resource_key` sin alterar el mapeo existente por ID (`resource_profiles`).
  - Se adaptó `get_profile_for_resource(resource_id=None, resource_key=None)` para soportar resolución indistinta por ID numérico o por `resource_key` unívoco. No realiza asignaciones aproximadas ni difusas.

### 2.3. Regla de Control de Acceso (`src/auditoria_iam/audit/rules/iam_001_access_control.py`)
- Se ajustó la invocación a `context.get_profile_for_resource(resource_id, resource_key=resource.get("resource_key"))` para permitir que los recursos de AWS IAM con IDs sintéticos resuelvan de forma inmediata su perfil de referencia autorizado.

### 2.4. Capa de Presentación / UI (`src/auditoria_iam/ui/pages/audit_page.py`)
- **Habilitación de ejecución para AWS:** Al seleccionar `"AWS IAM (Nube)"`, el botón **"Iniciar Auditoría"** permanece activo y listo para disparar la ejecución.
- **Mensajes de orientación técnica contextual:** Informa los requisitos de credenciales estándar (variables de entorno `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` o perfil en `~/.aws/credentials`) y la política de solo lectura.
- **Captura y retroalimentación de errores de AWS:**
  - `AWSIAMAuthenticationError`: Informa la ausencia o invalidez de credenciales.
  - `AWSIAMPermissionError`: Notifica si el rol o usuario carece de permisos de lectura IAM (`iam:List*`, `iam:Get*`).
  - `AWSIAMConnectionError`: Reporta fallas de conectividad de red con endpoints de AWS.
  - `AWSIAMDataSourceError`: Informa errores genéricos del SDK o servicio AWS.
  - Fallos de base de datos no impiden que los resultados permanezcan en memoria y se presenten al usuario.
- **Transición fluida a resultados:** Tras completar la auditoría con éxito, emite la señal `audit_completed` y despliega el botón de acceso directo a la pantalla de resultados.

---

## 3. Diagrama de Flujo de Datos

```
[ Usuario en PySide6 UI ]
        │
        ▼ Selecciona "AWS IAM (Nube)" en AuditPage y pulsa "Iniciar Auditoría"
[ AuditPage._on_execute_clicked() ]
        │
        ▼ Invoca AuditService.run_aws_audit()
[ AuditService ]
        ├───► [ AWSIAMDataSource (Boto3) ]
        │             │
        │             ├── Consultas Boto3: list_users, list_roles, list_groups, list_mfa_devices...
        │             └── Normalización canónica (tipo, identificador, atributos)
        │             │
        │             ◄ Retorna: List[Dict[str, Any]] (recursos normalizados)
        │
        ├───► [ _load_aws_audit_context() ]
        │             │
        │             └── Consulta perfiles y grupos esperados en MySQL (get_active_profiles)
        │                 ◄ Retorna: AuditContext (mapeo por ID y por resource_key)
        │
        ├───► [ AuditEngine.evaluate_all(resources, context) ]
        │             │
        │             ├── Regla IAM-001 (ISO 5.15): Control de acceso según perfil autorizado
        │             ├── Regla IAM-002 (ISO 5.16): Gestión de ciclo de vida e inactividad
        │             ├── Regla IAM-003 (ISO 5.18): Derechos de acceso y comodines en políticas JSON
        │             └── Regla IAM-004 (ISO 8.5):  Autenticación MFA obligatoria en usuarios
        │             │
        │             ◄ Retorna: List[AuditResult] + Dict[str, int] (summary)
        │
        ├───► [ MySQL Persistence (save_audit_run) ]
        │             │
        │             ├── Si recursos existen en catálogo MySQL:
        │             │   └── INSERT audit_runs (source_type='aws') + audit_results
        │             │       ◄ Retorna: db_status {"persisted": True, "run_id": N}
        │             │
        │             └── Si falta algún recurso en catálogo MySQL:
        │                 └── ROLLBACK atómico
        │                     ◄ Retorna: db_status {"persisted": False, "message": "Aviso..."}
        │
        ▼ Retorna tupla: (results, resources, summary, db_status)
[ AuditPage ]
        │
        ▼ Emite señal audit_completed(results, summary, db_status)
[ MainWindow ]
        │
        ▼ Despacha a ResultsPage.set_results(results, summary, db_status)
[ ResultsPage ]
        ├── Muestra tarjetas cuantitativas (Total, Conforme, Hallazgo, No evaluable)
        ├── Despliega tabla interactiva con detalles de cada regla evaluada
        └── Habilita exportación de informe en memoria (PDF, Excel, CSV)
```

---

## 4. Normalización de Recursos y Entrega a AuditEngine

El adaptador AWS IAM (`AWSIAMDataSource`) abstrae las estructuras de Boto3 para generar diccionarios con la estructura estándar requerida por el motor de auditoría:

```python
{
    "id": int,                           # ID sintético en memoria (1000 + idx)
    "resource_key": str,                 # Nombre unívoco (UserName o RoleName)
    "resource_type": "IAM_USER" | "IAM_ROLE",
    "display_name": str,
    "arn": str,
    "source_type": "aws",
    "resource_status": "active",
    "attributes": {
        "mfa_enabled": bool,             # (solo usuarios)
        "last_access_days": int | None,  # Días desde último uso de contraseña o access keys
        "groups": [str],                 # Nombres de grupos IAM asignados
        "policies": [                    # Políticas administradas directas, integradas y de grupos
            {
                "Statement": [ ... ]
            }
        ],
        "assume_role_policy_document": Dict[str, Any] | None  # (solo roles)
    }
}
```

---

## 5. Comportamiento de las Reglas ISO/IEC 27001 sobre Recursos AWS IAM

| Regla | Control ISO/IEC | Recurso AWS evaluado | Criterio de Evaluación | Estados posibles |
|---|---|---|---|---|
| **IAM-001** | **5.15** (Control de acceso) | Usuarios y Roles AWS | Pertenencia a grupos autorizados (`groups`) o entidades de confianza (`assume_role_policy_document`) validadas contra perfil de referencia (`resource_key`). | **CONFORME** (pertenencia alineada a perfil), **HALLAZGO** (grupos/asunciones no autorizadas), **NO_EVALUABLE** (sin perfil asignado). |
| **IAM-002** | **5.16** (Gestión de identidades) | Usuarios y Roles AWS | Estado de vigencia (`resource_status`) e inactividad de credenciales (`last_access_days`) frente a umbral de 90 días. | **CONFORME** (actividad $\le$ 90d), **HALLAZGO** (inactivo > 90d), **NO_EVALUABLE** (sin metadatos de actividad). |
| **IAM-003** | **5.18** (Derechos de acceso) | Políticas de Usuarios, Grupos y Roles | Detección de comodines `*` en `Action` y `Resource` con `Effect: Allow`. | **CONFORME** (sin comodines excesivos), **HALLAZGO** (política con `"Action": "*"` y `"Resource": "*"`), **NO_EVALUABLE** (política malformada o no recuperable). |
| **IAM-004** | **8.5** (Autenticación segura) | Usuarios AWS (`IAM_USER`) | Presencia de dispositivos MFA registrados en AWS IAM. Roles quedan formalmente excluidos. | **CONFORME** (MFA activo), **HALLAZGO** (sin MFA), **NO_EVALUABLE** (metadato ausente o inválido). |

---

## 6. Persistencia y Catálogo en MySQL

### 6.1. Requisitos de Persistencia Histórica
Para que una ejecución sobre AWS IAM quede registrada en el historial permanente de MySQL:
1. Todos los usuarios y roles evaluados en AWS deben estar previamente dados de alta en la tabla `resources` de MySQL con su `resource_key` exacto y `source_type = 'aws'`.
2. Las reglas deben existir en la tabla `audit_rules`.

### 6.2. Comportamiento ante Recursos no Registrados
Si se ejecuta una auditoría sobre una cuenta de AWS que contiene identidades no registradas en el catálogo de MySQL:
- `save_audit_run()` detecta la discrepancia y lanza `RuntimeError` para impedir inserciones con IDs huérfanos o sustitutos.
- La transacción ejecuta un `ROLLBACK` completo en MySQL.
- `AuditService` captura la situación y genera una advertencia descriptiva:
  *"⚠️ Aviso de persistencia: La auditoría se ejecutó correctamente en memoria, pero no pudo registrarse en el historial de MySQL porque faltan recursos registrados previamente en el catálogo de MySQL."*
- **Garantía de disponibilidad:** Los resultados no se pierden; se presentan en `ResultsPage` y el usuario puede exportar los informes en PDF, Excel o CSV directamente desde la memoria de la sesión.

---

## 7. Garantías de Seguridad Verificadas

1. **Estricto Modo de Solo Lectura:**
   - La lista blanca del adaptador solo autoriza llamadas `list_*` y `get_*`.
   - Bloqueo preventivo de prefijos de modificación (`create`, `update`, `delete`, `put`, `attach`, `detach`, `remove`, `add`).
2. **Protección de Credenciales:**
   - Sin claves de acceso en código, configuraciones fijas, logs ni mensajes de interfaz.
   - Resolución estándar mediante la cadena de credenciales de Boto3.
3. **Aislamiento en Pruebas:**
   - Ninguna prueba automatizada realiza llamadas a la red ni a la infraestructura real de AWS.

---

## 8. Resumen de Pruebas Automatizadas

| Módulo de Pruebas | Pruebas | Estado | Descripción |
|---|---|---|---|
| `test_aws_ui_integration.py` | 23 | **23 PASSED** | Carga de perfiles con función real, asociación por `resource_key`, reglas IAM-001 a IAM-004, ausencia de perfil, persistencia y exportación en memoria. |
| `test_aws_data_source.py` | 23 | **23 PASSED** | Consultas, paginación, normalización, políticas de grupo e inline, solo lectura. |
| `test_ui.py` | 18 | **18 PASSED** | Navegación, stacks de pantallas, habilitación de ejecución para AWS, manejo de errores en UI. |
| `test_dashboard.py` | 13 | **13 PASSED** | Indicadores cuantitativos, porcentajes, navegación a controles técnicos ISO. |
| `test_dashboard_integration.py` | 12 | **12 PASSED** | Integración del Dashboard con MySQL, actualización por ciclo de vida. |
| `test_reports.py` | 13 | **13 PASSED** | Generación de informes PDF, Excel, CSV con datos reales de auditoría. |
| `test_audit_engine.py` | 8 | **8 PASSED** | Motor central de auditoría y evaluación de reglas. |
| `test_audit_models.py` | 6 | **6 PASSED** | Modelos `AuditResult`, `AuditContext` (búsqueda por ID y por clave). |
| `test_rule_iam_001.py` | 27 | **27 PASSED** | Evaluación exhaustiva de control de acceso y perfiles. |
| `test_rule_iam_002.py` | 28 | **28 PASSED** | Evaluación exhaustiva de inactividad de usuarios y ciclo de vida. |
| `test_rule_iam_003.py` | 33 | **33 PASSED** | Detección de comodines en políticas técnicas IAM. |
| `test_rule_iam_004.py` | 6 | **6 PASSED** | Validación de dispositivos multifactor (MFA). |
| `test_simulator.py` | 9 | **9 PASSED** | Dataset simulado y validación de integridad referencial. |
| `test_settings.py` | 12 | **12 PASSED** | Configuración de entorno y validación de variables. |
| `test_database.py` | 11 | **11 PASSED** | Persistencia transaccional y consultas de auditoría en MySQL. |
| **TOTAL** | **242** | **242 PASSED (100%)** | **0 fallos, 0 errores, 0 excepciones nativas** |

---

## 9. Consideraciones para la Entrega 7.2

- En la Entrega 7.2 se ejecutará la validación de campo en un entorno real/sandbox de AWS IAM.
- Se mantendrá el dataset simulado para propósitos académicos y de demostración repetible.
- Para habilitar la persistencia histórica completa en AWS, se podrán dar de alta previamente los usuarios de prueba en la tabla `resources` de MySQL.
