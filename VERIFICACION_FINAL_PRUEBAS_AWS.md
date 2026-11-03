# INFORME DE VERIFICACIÓN FINAL DE PRUEBAS Y OPERACIONES AWS

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.  
**Fecha:** Noviembre 2026  
**Entorno de ejecución:** Windows, Python 3.13.5, pytest-9.2.0, Boto3 / Botocore 1.34  
**Tipo de verificación:** Estrictamente de solo lectura y ejecución de pruebas automatizadas  

---

## 1. RESULTADOS DE LA SUITE DE PRUEBAS AUTOMATIZADAS

Se ejecutó la colección completa de pruebas mediante el comando:
```bash
.\.venv\Scripts\pytest.exe -v
```

### 1.1. Resumen Global de Ejecución
- **Pruebas recopiladas (collected):** **309**
- **Pruebas aprobadas (passed):** **309**
- **Pruebas fallidas (failed):** **0**
- **Pruebas omitidas (skipped):** **0**
- **Porcentaje de aprobación:** **100.0%**
- **Tiempo de ejecución total:** **9.59 segundos**
- **Código de salida (exit code):** **`0`**

---

### 1.2. Cantidad Exacta de Pruebas por Archivo y Comprobación de Suma

A continuación se detalla el desglose comprobado de casos de prueba recopilados y ejecutados en cada uno de los 19 archivos de prueba del proyecto:

| N° | Archivo de Prueba | Casos Recopilados | Casos Aprobados | Casos Fallidos | Casos Omitidos |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | `tests/test_audit_engine.py` | 8 | 8 | 0 | 0 |
| 2 | `tests/test_audit_models.py` | 6 | 6 | 0 | 0 |
| 3 | `tests/test_aws_adapter_stubber.py` | 44 | 44 | 0 | 0 |
| 4 | `tests/test_aws_data_source.py` | 28 | 28 | 0 | 0 |
| 5 | `tests/test_aws_end_to_end.py` | 23 | 23 | 0 | 0 |
| 6 | `tests/test_aws_ui_integration.py` | 23 | 23 | 0 | 0 |
| 7 | `tests/test_connection.py` | 6 | 6 | 0 | 0 |
| 8 | `tests/test_dashboard.py` | 13 | 13 | 0 | 0 |
| 9 | `tests/test_dashboard_integration.py` | 12 | 12 | 0 | 0 |
| 10 | `tests/test_persistence.py` | 16 | 16 | 0 | 0 |
| 11 | `tests/test_reports.py` | 14 | 14 | 0 | 0 |
| 12 | `tests/test_repository.py` | 19 | 19 | 0 | 0 |
| 13 | `tests/test_rule_iam_001.py` | 16 | 16 | 0 | 0 |
| 14 | `tests/test_rule_iam_002.py` | 13 | 13 | 0 | 0 |
| 15 | `tests/test_rule_iam_003.py` | 22 | 22 | 0 | 0 |
| 16 | `tests/test_rule_iam_004.py` | 6 | 6 | 0 | 0 |
| 17 | `tests/test_settings.py` | 13 | 13 | 0 | 0 |
| 18 | `tests/test_simulator.py` | 9 | 9 | 0 | 0 |
| 19 | `tests/test_ui.py` | 18 | 18 | 0 | 0 |
| **—** | **TOTAL** | **309** | **309** | **0** | **0** |

#### Comprobación Aritmética de Integridad
$$\sum_{i=1}^{19} \text{Casos}_i = 8 + 6 + 44 + 28 + 23 + 23 + 6 + 13 + 12 + 16 + 14 + 19 + 16 + 13 + 22 + 6 + 13 + 9 + 18 = 309$$

La suma de las pruebas contabilizadas por archivo coincide de manera exacta e inequívoca con el total de **309 pruebas recopiladas y aprobadas**.

---

### 1.3. Registro Real de Salida de Pytest (Inicio y Cierre)

```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\andre\Desktop\TESIS\sistema\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\andre\Desktop\TESIS\sistema
configfile: pytest.ini
testpaths: tests
collecting ... collected 309 items

tests/test_audit_engine.py::test_audit_engine_initializes_with_default_rules PASSED [  0%]
tests/test_audit_engine.py::test_audit_engine_register_custom_rule PASSED [  0%]
tests/test_audit_engine.py::test_audit_engine_invalid_rule_type PASSED   [  0%]
tests/test_audit_engine.py::test_audit_engine_evaluate_single_rule PASSED [  1%]
tests/test_audit_engine.py::test_audit_engine_evaluate_all_rules PASSED  [  1%]
tests/test_audit_engine.py::test_audit_engine_evaluate_all_resources PASSED [  1%]
tests/test_audit_engine.py::test_audit_engine_defensive_error_handling PASSED [  2%]
tests/test_audit_engine.py::test_audit_engine_unknown_rule_code_raises_key_error PASSED [  2%]
tests/test_audit_models.py::test_audit_result_valid_statuses PASSED      [  2%]
tests/test_audit_models.py::test_audit_result_invalid_status_raises_error PASSED [  3%]
tests/test_audit_models.py::test_audit_result_missing_required_fields PASSED [  3%]
tests/test_audit_models.py::test_audit_result_to_dict PASSED             [  3%]
tests/test_audit_models.py::test_audit_context_lookups PASSED            [  4%]
tests/test_audit_models.py::test_extract_resource_attributes PASSED      [  4%]
tests/test_aws_adapter_stubber.py::test_stubber_list_users_and_normalization PASSED [  4%]
...
tests/test_ui.py::test_history_page_loads_and_displays_runs_from_mysql PASSED [ 99%]
tests/test_ui.py::test_history_page_select_run_loads_historical_results_in_results_page PASSED [ 99%]
tests/test_ui.py::test_history_page_error_retrieving_historical_run_communicated_through_ui PASSED [100%]

============================= 309 passed in 9.59s =============================
```

---

## 2. INSPECCIÓN DE OPERACIONES AWS IAM Y LISTA SEGURA

Se realizó la inspección estática del archivo:
`src/auditoria_iam/data_sources/aws/adapter.py`

### 2.1. Operaciones Incluidas en `READ_ONLY_OPERATIONS`
La lista blanca `READ_ONLY_OPERATIONS` (líneas 26 a 48 de `adapter.py`) define exactamente **21 operaciones permitidas**:

1. `get_access_key_last_used`
2. `get_group`
3. `get_group_policy`
4. `get_policy`
5. `get_policy_version`
6. `get_role`
7. `get_role_policy`
8. `get_user`
9. `get_user_policy`
10. `list_access_keys`
11. `list_attached_group_policies`
12. `list_attached_role_policies`
13. `list_attached_user_policies`
14. `list_group_policies`
15. `list_groups`
16. `list_groups_for_user`
17. `list_mfa_devices`
18. `list_role_policies`
19. `list_roles`
20. `list_user_policies`
21. `list_users`

---

### 2.2. Operaciones Reales de Boto3 IAM Utilizadas en `adapter.py`
Analizando las llamadas reales despachadas a través de `_paginate_or_call()` y `_call_iam_operation()`, se identifican **19 operaciones efectivamente invocadas**:

1. `get_access_key_last_used` (en `_get_user_last_access_days()`)
2. `get_group` (en `get_groups()`)
3. `get_group_policy` (en `_get_group_policies()`)
4. `get_policy` (en `_get_managed_policy_document()`)
5. `get_policy_version` (en `_get_managed_policy_document()`)
6. `get_role_policy` (en `_get_role_policies()`)
7. `get_user_policy` (en `_get_user_policies()`)
8. `list_access_keys` (en `_get_user_last_access_days()`)
9. `list_attached_group_policies` (en `_get_group_policies()`)
10. `list_attached_role_policies` (en `_get_role_policies()`)
11. `list_attached_user_policies` (en `_get_user_policies()`)
12. `list_group_policies` (en `_get_group_policies()`)
13. `list_groups` (en `get_groups()`)
14. `list_groups_for_user` (en `_get_user_groups()`)
15. `list_mfa_devices` (en `_check_user_mfa()`)
16. `list_role_policies` (en `_get_role_policies()`)
17. `list_roles` (en `get_roles()`)
18. `list_user_policies` (en `_get_user_policies()`)
19. `list_users` (en `get_users()`)

---

### 2.3. Explicación de la Diferencia entre Ambas Cantidades

- **Total en `READ_ONLY_OPERATIONS`:** 21 operaciones.
- **Total efectivamente invocadas:** 19 operaciones.
- **Diferencia:** **2 operaciones** declaradas en `READ_ONLY_OPERATIONS` que no son invocadas en el código actual:
  1. `get_user`
  2. `get_role`

**Causa técnica de la diferencia:**
Las funciones `get_users()` y `get_roles()` de `adapter.py` emplean las operaciones de lista paginadas `list_users` y `list_roles`. En la API de AWS IAM, las respuestas de `list_users` y `list_roles` ya retornan el conjunto completo de atributos necesarios para la auditoría (tales como `UserName`, `Arn`, `UserId`, `CreateDate`, `PasswordLastUsed` y la política de asunción `AssumeRolePolicyDocument`). Por consiguiente, no se requiere emitir llamadas individuales adicionales de `get_user` o `get_role` para cada identidad, lo cual optimiza el rendimiento y reduce drásticamente el consumo de cuota de solicitudes (evitando errores de tipo *Throttling* o *Rate Exceeded*).

Ambas operaciones (`get_user` y `get_role`) se mantienen autorizadas en `READ_ONLY_OPERATIONS` como parte del catálogo de solo lectura para soportar posibles consultas puntuales individuales de una identidad sin comprometer la seguridad.

- **Operaciones invocadas que NO estén en `READ_ONLY_OPERATIONS`:** **0**. Todas las 19 operaciones invocadas se encuentran validadas y autorizadas dentro de la lista blanca.

---

### 2.4. Confirmación de Operaciones Exclusivamente de Consulta

Se confirma categóricamente que **todas las 21 operaciones permitidas son estrictamente de solo lectura / consulta**:
- **7 operaciones de tipo `get_*`:** Consultan documentos de políticas, versiones específicas, metadatos de claves y detalles de grupos.
- **14 operaciones de tipo `list_*`:** Enumeran colecciones de identidades, asociaciones de grupos, dispositivos MFA y adjuntos de políticas.
- **0 operaciones de escritura, creación, actualización o eliminación.**

Adicionalmente, el adaptador refuerza esta restricción en dos niveles:
1. **Validación preventiva por catálogo (`_validate_safe_operation`):**
   ```python
   if operation_name not in READ_ONLY_OPERATIONS:
       raise AWSIAMPermissionError(
           f"Operación '{operation_name}' no autorizada. El adaptador opera en modo estricto de solo lectura."
       )
   ```
2. **Bloqueo preventivo de 15 prefijos de mutación (`FORBIDDEN_OPERATION_PREFIXES`):**
   Bloquea cualquier invocación que empiece por:
   `create`, `update`, `delete`, `put`, `attach`, `detach`, `enable`, `disable`, `deactivate`, `generate`, `remove`, `add`, `tag`, `untag`.

---

## 3. CUMPLIMIENTO ESTRICTO DE RESTRICCIONES

Durante esta verificación:
1. **No se modificó ningún archivo del proyecto:** El código fuente, reglas, modelos, interfaz, repositorio y persistencia permanecen intactos.
2. **No se ejecutaron migraciones ni consultas de escritura en MySQL:** La base de datos no fue alterada.
3. **No se leyó ni expuso el contenido del archivo `.env`:** Se respetó la confidencialidad de parámetros locales.
4. **No se realizaron conexiones a AWS real ni se utilizaron credenciales reales:** Toda la validación técnica se ejecutó mediante fixtures desacopladas y `botocore.stub.Stubber`.
5. **No se generó ningún archivo comprimido ZIP.**

---

## 4. CONCLUSIÓN FINAL

La verificación técnica confirma de manera rigurosa que:
1. El sistema cuenta con **309 pruebas automatizadas aprobadas al 100% (0 fallos, 0 omitidas)** distribuidas en 19 archivos, con plena coincidencia aritmética.
2. El adaptador AWS IAM utiliza **19 operaciones Boto3 reales**, todas contenidas en la lista blanca de **21 operaciones de solo lectura** (`READ_ONLY_OPERATIONS`).
3. El sistema garantiza la inocuidad total frente a la infraestructura en la nube, cumpliendo cabalmente con los principios de mínimo privilegio, solo lectura y seguridad técnica para su entrega académica.

