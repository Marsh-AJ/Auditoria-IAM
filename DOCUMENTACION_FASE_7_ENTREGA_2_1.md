# DOCUMENTACIÓN TÉCNICA — FASE 7, ENTREGA 7.2.1
## VALIDACIÓN TÉCNICA DEL ADAPTADOR AWS IAM MEDIANTE BOTO3 STUBBER

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.  
**Fase:** Fase 7 — Adaptador AWS IAM e Integración de Nube.  
**Entrega:** 7.2.1 — Validación técnica del adaptador AWS IAM mediante Boto3 Stubber, mocks y pruebas automatizadas.  
**Estado:** APROBADO / 100% EXITOSO.  
**Fecha:** Noviembre 2026.

---

### 1. OBJETIVO Y ALCANCE DE LA ENTREGA

El objetivo de la Entrega 7.2.1 es completar la validación técnica exhaustiva del adaptador AWS IAM (`AWSIAMDataSource`), asegurando su confiabilidad, robustez y compatibilidad con el motor de auditoría y las reglas de seguridad ISO/IEC 27001:2022, sin requerir acceso a una cuenta real de AWS ni la configuración de credenciales vivas en el entorno local.

Para lograr este nivel de aislamiento y determinismo técnico se empleó `botocore.stub.Stubber`, la herramienta oficial provista por el SDK de AWS para simular el comportamiento de la capa de transporte y protocolo de Boto3. Esta herramienta valida rigurosamente los nombres de operación invocados, la estructura de parámetros (`expected_params`), y suministra respuestas canónicas o errores de servicio en secuencias controladas.

---

### 2. INSPECCIÓN INICIAL: STUBBER VS. MOCKS EN EL ADAPTADOR AWS IAM

Antes de la implementación de la Entrega 7.2.1, el proyecto disponía de:
- `test_aws_data_source.py`: Pruebas de unidad basadas en `unittest.mock.MagicMock`.
- `test_aws_ui_integration.py`: Pruebas de integración del flujo aplicativo y vistas PySide6 con componentes simulados.

#### 2.1 Comparativa de Enfoques de Prueba

| Característica | Mocks Tradicionales (`unittest.mock`) | Boto3 Stubber (`botocore.stub.Stubber`) |
| :--- | :--- | :--- |
| **Capa de interceptación** | Métodos arbitrarios en objetos Python | Capa cliente interna de `botocore.client.BaseClient` |
| **Validación de API AWS** | Permite cualquier método o firma sin validar esquema | Rechaza llamadas que no correspondan a operaciones reales de la API de IAM |
| **Verificación de parámetros** | Requiere aserciones manuales complejas | Valida automáticamente los parámetros contra los esquemas oficiales de Boto3 |
| **Simulación de errores de servicio** | Requiere instanciar manualmente objetos `ClientError` | Permite inyectar `add_client_error` con códigos AWS nativos (`AccessDenied`, etc.) |
| **Orden y secuencia de llamadas** | Generalmente no estricto | Estricto (requiere respetar el orden secuencial exacto de las operaciones API) |

#### 2.2 Inventario de Operaciones Boto3 y Cobertura

Se verificaron las siguientes operaciones Boto3 utilizadas por el adaptador:

| Operación Boto3 IAM | Finalidad Técnica en el Sistema | Cobertura Previa (Mocks) | Cobertura Entrega 7.2.1 (Stubber) |
| :--- | :--- | :---: | :---: |
| `list_users` | Enumeración de identidades de usuario IAM y cálculo de IDs deterministas | Sí | **Sí (Multi-página + parámetros)** |
| `list_groups_for_user` | Identificación de pertenencia a grupos para control de privilegios (IAM-001) | Sí | **Sí (Validación de UserName)** |
| `list_mfa_devices` | Verificación de dispositivos MFA activos para control 8.5 (IAM-004) | Sí | **Sí (Validación de UserName)** |
| `list_roles` | Enumeración de identidades de servicio y roles de acceso temporal | Sí | **Sí (Multi-página + filtrado SLR)** |
| `list_user_policies` | Enumeración de políticas integradas (*inline*) directas en usuarios | Sí | **Sí (Trazabilidad de origen)** |
| `get_user_policy` | Extracción del documento JSON de política integrada en usuario | Sí | **Sí (Control de errores e incompletas)** |
| `list_attached_user_policies` | Enumeración de políticas administradas adjuntas a usuarios | Sí | **Sí (Extracción de PolicyArn)** |
| `list_role_policies` | Enumeración de políticas integradas directas en roles IAM | Sí | **Sí (Trazabilidad de origen)** |
| `get_role_policy` | Extracción del documento JSON de política integrada en rol | Sí | **Sí (Normalización y validación)** |
| `list_attached_role_policies` | Enumeración de políticas administradas adjuntas a roles | Sí | **Sí (Extracción de PolicyArn)** |
| `list_group_policies` | Enumeración de políticas integradas asignadas a nivel de grupo | Sí | **Sí (Herencia de políticas)** |
| `get_group_policy` | Extracción de política integrada de grupo | Sí | **Sí (Normalización JSON)** |
| `list_attached_group_policies` | Enumeración de políticas administradas adjuntas a grupos | Sí | **Sí (Herencia y deduplicación)** |
| `get_policy` | Consulta de metadatos de política administrada y versión por defecto | Sí | **Sí (Extracción de DefaultVersionId)** |
| `get_policy_version` | Extracción del documento de la versión activa de política administrada | Sí | **Sí (Normalización para IAM-003)** |
| `list_access_keys` | Enumeración de credenciales programáticas activas por usuario | Sí | **Sí (Validación de estado Active)** |
| `get_access_key_last_used` | Fecha de uso reciente de credencial para inactividad (IAM-002) | Sí | **Sí (Discriminación contra contraseña)** |

---

### 3. PRUEBAS DE CONSULTAS AWS IAM MEDIANTE BOTO3 STUBBER

En la suite `tests/test_aws_adapter_stubber.py` se implementaron pruebas especializadas que cubren las consultas clave:

1. **`test_stubber_list_users_and_normalization`**:
   Valida la consulta de usuarios IAM, transformándolos al esquema canónico requerido por el motor: `resource_key`, `resource_type='IAM_USER'`, `path`, y mapeo de atributos de seguridad.
2. **`test_stubber_query_groups_and_membership`**:
   Valida la recuperación de los nombres de los grupos IAM a los que pertenece cada usuario, verificando el parámetro `UserName`.
3. **`test_stubber_query_mfa_devices_present_and_absent`**:
   Comprueba la discriminación entre usuarios con dispositivos virtuales/físicos MFA activos (`mfa_enabled = True`) y usuarios sin dispositivos asociados (`mfa_enabled = False`).
4. **`test_stubber_list_roles_and_trust_policies`**:
   Comprueba la consulta de roles IAM y la deserialización de sus documentos de política de confianza (`AssumeRolePolicyDocument`), garantizando que la estructura `Statement` quede normalizada.
5. **`test_stubber_query_inline_policies_user_and_role`**:
   Valida la extracción de políticas integradas (*inline*) directas, verificando que contengan los metadatos de trazabilidad `_source_type='user_inline'` y `_source_name`.
6. **`test_stubber_query_managed_policies_and_default_version`**:
   Valida el flujo en dos etapas requerido por Boto3: primero consultar `get_policy` para determinar el `DefaultVersionId` actual (ej. `v2`), y luego consultar `get_policy_version` para recuperar el documento JSON real.
7. **`test_stubber_query_group_inherited_policies`**:
   Valida la herencia de políticas desde los grupos hacia los usuarios miembros, verificando la anotación de `_group_name` y la deduplicación de políticas administradas idénticas compartidas.
8. **`test_stubber_query_last_access_information_dates`**:
   Comprueba el cálculo del atributo `last_access_days` evaluando tanto la fecha del último inicio de sesión en consola (`PasswordLastUsed`) como la última actividad de claves de acceso (`get_access_key_last_used`), seleccionando de forma conservadora el evento más reciente.

---

### 4. PRUEBAS DE PAGINACIÓN MULTI-PÁGINA Y RESPUESTAS DEFENSIVAS

1. **Paginación Multi-página de Usuarios (`test_stubber_pagination_multi_page_users`)**:
   Simula respuestas fraccionadas de AWS con `IsTruncated: True` y un token de continuación `Marker`. Verifica que el adaptador itere exhaustivamente por todas las páginas (`Marker="next_page_token_123"`), consolidando los recursos sin pérdida de datos ni duplicación de identidades.
2. **Paginación Multi-página de Roles (`test_stubber_pagination_multi_page_roles`)**:
   Valida la paginación multi-página para la entidad `list_roles` utilizando la infraestructura de paginación interna `_paginate_or_call`.
3. **Colecciones Vacías (`test_stubber_pagination_empty_responses`)**:
   Comprueba que cuentas con 0 usuarios o 0 roles devuelvan listas vacías `[]` de forma limpia y controlada, sin lanzar excepciones ni fallar en el motor de auditoría.

---

### 5. MANEJO DEFENSIVO DE ERRORES Y TIMEOUTS DE RED

Se comprobó la traducción de fallos de infraestructura a excepciones controladas de dominio, impidiendo la exposición de credenciales o trazas sensibles:

1. **Denegación de Permisos de Lectura (`test_stubber_error_access_denied_permission_error`)**:
   Inyección mediante `stubber.add_client_error("list_users", "AccessDenied")`. Valida la captura y conversión a `AWSIAMPermissionError` con mensaje claro y sin filtrar secretos.
2. **Token de Cliente Inválido (`test_stubber_error_invalid_client_token_id`)**:
   Inyección mediante `stubber.add_client_error("list_users", "InvalidClientTokenId")`. Valida la conversión directa a `AWSIAMAuthenticationError`.
3. **Ausencia o Incompletitud de Credenciales**:
   - `test_stubber_error_no_credentials_handling`: `botocore.exceptions.NoCredentialsError` -> `AWSIAMAuthenticationError`.
   - `test_stubber_error_partial_credentials_handling`: `botocore.exceptions.PartialCredentialsError` -> `AWSIAMAuthenticationError`.
4. **Conectividad y Timeouts de Red (`test_stubber_error_endpoint_connection_and_timeouts`)**:
   Se ampliaron las cláusulas defensivas en `AWSIAMDataSource._handle_exception` para mapear explícitamente:
   - `botocore.exceptions.EndpointConnectionError` -> `AWSIAMConnectionError`
   - `botocore.exceptions.ConnectTimeoutError` -> `AWSIAMConnectionError`
   - `botocore.exceptions.ReadTimeoutError` -> `AWSIAMConnectionError`
   - `botocore.exceptions.ConnectionClosedError` -> `AWSIAMConnectionError`
5. **Marcadores de Políticas Incompletas e Inaccesibles (`test_stubber_unretrievable_policy_generates_incomplete_marker_and_no_evaluable`)**:
   Si una política asignada a una entidad no puede recuperarse (ej. `get_user_policy` rechazada con `AccessDenied`), el adaptador genera un marcador técnico:
   ```python
   {
       "_source_type": "user_inline",
       "_incomplete_policy": True,
       "_error": "Documento de política integrada de usuario no recuperable o inválido",
       "Statement": None
   }
   ```
   Al ser evaluado por la regla `IAM-003` (Control ISO 5.18), este marcador induce un resultado estrictamente **"No evaluable"** con justificación técnica, impidiendo omitir silenciosamente la política y previniendo falsos positivos de conformidad.
6. **Manejo de Sintaxis JSON Malformada (`test_stubber_malformed_policy_document_handling`)**:
   Verifica que respuestas con documentos corruptos no admitidos sean capturados y normalizados como políticas incompletas no evaluables.

---

### 6. SEGURIDAD ESTRICTA DE SOLO LECTURA Y GARANTÍA DE AISLAMIENTO

1. **Bloqueo Activo de Mutaciones (`test_stubber_strict_read_only_blocks_forbidden_operations`)**:
   Se parametrizaron 23 operaciones de escritura y administración AWS IAM:
   `create_user`, `delete_user`, `update_user`, `put_user_policy`, `attach_user_policy`, `detach_user_policy`, `create_role`, `delete_role`, `update_role`, `put_role_policy`, `attach_role_policy`, `detach_role_policy`, `add_user_to_group`, `remove_user_from_group`, `create_group`, `delete_group`, `enable_mfa_device`, `deactivate_mfa_device`, `create_access_key`, `delete_access_key`, `update_access_key`, `tag_user`, `untag_user`.
   Todas son interceptadas y rechazadas preventivamente por `_validate_safe_operation`, lanzando `AWSIAMDataSourceError` antes de emitir cualquier solicitud a AWS.
2. **Inspección de Operaciones Despachadas (`test_stubber_actual_dispatched_calls_strictly_read_only`)**:
   Se verificó que el 100% de las llamadas realizadas durante una extracción completa pertenezcan estrictamente al conjunto constante inmutable `READ_ONLY_OPERATIONS`.
3. **Cero Llamadas Reales y Aislamiento de Credenciales**:
   Todas las pruebas operan con clientes instanciados sobre regiones ficticias (`us-east-1`) y credenciales de prueba (`dummy_key`, `dummy_secret`), siendo interceptadas antes de salir de la memoria del proceso local.

---

### 7. COMPATIBILIDAD INTEGRAL CON EL MOTOR DE AUDITORÍA Y LAS CUATRO REGLAS

Se verificó mediante `test_stubber_resources_evaluated_by_all_four_rules` que los recursos obtenidos por el adaptador se integren sin fisuras con el motor central `AuditEngine` y las cuatro reglas ISO/IEC 27001:2022:

- **Regla IAM-001 (Control 5.15 - Control de acceso):**
  Evalúa `C15-01` (grupos autorizados según perfil de referencia) y `C15-02` (políticas de confianza de roles).
- **Regla IAM-002 (Control 5.16 - Gestión de identidades / Inactividad):**
  Evalúa `C16-02` comparando `last_access_days` contra el umbral configurable (90 días).
- **Regla IAM-003 (Control 5.18 - Derechos de acceso privilegiados):**
  Evalúa `C18-01` analizando el documento de permisos JSON para detectar comodines peligrosos (`*`).
- **Regla IAM-004 (Control 8.5 - Autenticación segura):**
  Evalúa `C85-01` verificando la activación de MFA para usuarios y excluyendo técnicamente los roles de servicio.
- **Preservación del Simulador Local (`test_stubber_preserves_simulator_integrity`)**:
  Se comprobó que el dataset determinista de la fuente simulada produce idénticos resultados (10 recursos evaluados, 67 resultados, estados Conforme, Hallazgo y No evaluable equilibrados).

---

### 8. ARCHIVOS MODIFICADOS Y CREADOS

1. **`src/auditoria_iam/data_sources/aws/adapter.py`** (Modificado):
   - Mapeo de excepciones de timeout de red (`ConnectTimeoutError`, `ReadTimeoutError`, `ConnectionClosedError`) a `AWSIAMConnectionError`.
   - Protección defensiva con captura de `AWSIAMPermissionError` en `_get_user_policies`, `_get_role_policies`, `_get_group_policies` y `_get_managed_policy_document`, generando marcadores incompletos cuando una política individual no puede ser leída.
2. **`tests/test_aws_adapter_stubber.py`** (Creado):
   - Archivo con 44 pruebas unitarias y de integración parametrizadas utilizando `botocore.stub.Stubber` y fixtures de cliente desacopladas.
3. **`DOCUMENTACION_FASE_7_ENTREGA_2_1.md`** (Creado):
   - Documentación técnica exhaustiva de la entrega.

---

### 9. RESUMEN DE EJECUCIÓN Y VALIDACIÓN FINAL

```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\andre\Desktop\TESIS\sistema
configfile: pytest.ini
collected 286 items

tests/test_audit_engine.py ............................................ [ 15%]
tests/test_audit_models.py ............................................. [ 31%]
tests/test_aws_adapter_stubber.py ...................................... [ 46%]
tests/test_aws_data_source.py ............................               [ 56%]
tests/test_aws_ui_integration.py .......................                [ 64%]
tests/test_connection.py ....                                            [ 66%]
tests/test_dashboard.py .................                                [ 72%]
tests/test_dashboard_integration.py ............                         [ 76%]
tests/test_persistence.py .......................                        [ 84%]
tests/test_reports.py .................                                  [ 90%]
tests/test_repository.py ............                                    [ 94%]
tests/test_rule_iam_001.py ..........                                    [ 97%]
tests/test_rule_iam_002.py .....                                         [ 99%]
tests/test_rule_iam_003.py ......                                        [100%]
tests/test_rule_iam_004.py ...                                           [100%]
tests/test_settings.py ....                                              [100%]
tests/test_simulator.py ......                                           [100%]
tests/test_ui.py ..............                                          [100%]

============================= 286 passed in 10.39s =============================
```

- **Total de pruebas en el sistema:** 286 ejecutadas.
- **Pruebas aprobadas:** 286 (100%).
- **Pruebas fallidas:** 0.
- **Pruebas omitidas/deseleccionadas:** 0.
- **Código de salida de pytest:** `0`.

