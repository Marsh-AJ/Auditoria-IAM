# DOCUMENTACIÓN TÉCNICA — FASE 2: ENTREGA 2
## CONFIGURACIÓN CENTRALIZADA Y CAPA DE ACCESO A DATOS (REPOSITORIO DE CONSULTAS)

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO/IEC 27001 para UPHARVEN C.A.  
**Fase:** Fase 2 — Adaptación de la Persistencia y Capa de Datos  
**Entrega:** Entrega 2 — Configuración y Capa de Acceso a Datos  
**Fecha:** 1 de noviembre de 2026  
**Entorno de desarrollo:** Python 3.13.5 | MySQL Server 9.6 | Windows  
**Base de datos de pruebas:** `auditoria_iam_upharven_pruebas`  
**Base de datos de producción/original:** `auditoria_iam_upharven`  

---

## 1. OBJETIVO DE LA ENTREGA

El objetivo fundamental de esta segunda entrega de la Fase 2 es desacoplar, robustecer y estandarizar la capa de persistencia y configuración del prototipo de auditoría técnica IAM, garantizando una arquitectura modular, defensiva y segura sin alterar el esquema ni los registros de las bases de datos.

Específicamente, los objetivos técnicos alcanzados son:
1. **Configuración centralizada y tipada (`settings.py`):** Carga y validación rigurosa de parámetros de conexión mediante `python-dotenv` y `dataclasses`, evitando sobrescritura global de variables del entorno (`override=False`), eliminando valores fijos sensibles en código y permitiendo alternar entre la base de datos original (`auditoria_iam_upharven`) y la de pruebas (`auditoria_iam_upharven_pruebas`) sin alterar el código fuente.
2. **Gestión de conexiones y transacciones defensivas (`connection.py`):** Implementación de context managers (`get_db_cursor` y `get_db_transaction`) para el control seguro de cursores y transacciones ACID, con rollback automático ante excepciones, liberación determinista de recursos y mensajes de error controlados que no revelan credenciales, detalles internos del motor ni trazas del servidor.
3. **Capa de repositorio de solo lectura (`repository.py`):** Desarrollo de 18 funciones de consulta especializadas y parametrizadas para cubrir la totalidad de las 10 tablas del modelo relacional adaptado (recursos, reglas, perfiles de acceso autorizados, ejecuciones de auditoría, resultados granulares, hallazgos y evidencias asociadas).
4. **Verificación unitaria automatizada con dobles de prueba (100% aislada de red):** Batería de 38 pruebas unitarias automatizadas con `pytest` y `unittest.mock`, verificando configuración, manejo defensivo de excepciones, context managers y confirmando mediante análisis estático de código (AST) la ausencia absoluta de sentencias de escritura (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`). No se realizaron conexiones en vivo ni alteraciones sobre las bases de datos reales.

---

## 2. INVENTARIO DE ARCHIVOS

### 2.1. Archivos Revisados
- `src/auditoria_iam/database/connection.py` (inspección de control de excepciones y desacoplamiento de conexión).
- `src/auditoria_iam/database/repository.py` (inspección de consultas SQL de solo lectura y parametrización).
- `.env` (inspección no destructiva de parámetros de entorno).

### 2.2. Archivos Creados
- `src/auditoria_iam/config/settings.py`: Módulo de configuración tipada, validación de variables de entorno y selección dinámica de bases de datos.
- `src/auditoria_iam/config/__init__.py`: Exportación del paquete de configuración.
- `tests/test_settings.py`: 8 pruebas unitarias automatizadas sobre validación de variables, puertos, timeouts y sobreescrituras.
- `tests/test_connection.py`: 6 pruebas unitarias automatizadas sobre conexión, context managers de lectura y transaccionales, y manejo seguro de excepciones sin divulgar credenciales ni mensajes internos.
- `tests/test_repository.py`: 24 pruebas unitarias automatizadas sobre las 18 funciones del repositorio, cobertura de tablas adaptadas, parametrización y verificación estática AST contra sentencias DDL/DML de escritura.
- `DOCUMENTACION_FASE2_ENTREGA2.md`: Documento técnico formal de la entrega.

### 2.3. Archivos Modificados
- `src/auditoria_iam/database/connection.py`: Refactorización completa orientada a objetos de configuración, context managers defensivos y mensajes de excepción controlados sin filtración de credenciales o trazas de la base de datos.
- `src/auditoria_iam/database/repository.py`: Refactorización y ampliación completa a 18 funciones de consulta de solo lectura para las 10 tablas del sistema.
- `src/auditoria_iam/database/__init__.py`: Exportación unificada de funciones de conexión y repositorio.

---

## 3. CONFIGURACIÓN CENTRALIZADA (`settings.py`)

### 3.1. Arquitectura del Módulo
El módulo `src/auditoria_iam/config/settings.py` implementa la clase inmutable de datos `DatabaseSettings`:

```python
@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    name: str
    user: str
    password: str
    timeout: int = 10
```

### 3.2. Variables de Entorno y Validación
La carga de configuración se realiza mediante la función `get_database_settings(db_name_override=None, env_file_path=None)`:
- Invoca `dotenv.load_dotenv(override=False)` para no sobrescribir globalmente variables de entorno del sistema operativo.
- **Validación obligatoria:** Verifica que `DB_HOST`, `DB_NAME`, `DB_USER` y `DB_PASSWORD` existan y no sean cadenas vacías o en blanco. En caso de ausencia, levanta una excepción `ValueError` descriptiva sin imprimir valores.
- **Sin valores fijos predeterminados en código:** El nombre de la base de datos se deriva de `DB_NAME` en `.env` o del parámetro `db_name_override`; no se asume una base de datos por defecto si la variable está ausente.
- **Validación de puerto (`DB_PORT`):** Se valida estrictamente en el rango de red `1 <= port <= 65535`.
- **Validación de timeout (`DB_CONNECT_TIMEOUT`):** Se valida como entero positivo `> 0` segundos (por defecto: 10 segundos).

### 3.3. Selección de la Base de Datos de Pruebas
Para operar sobre `auditoria_iam_upharven_pruebas` sin alterar los scripts ni el código fuente, el sistema ofrece dos mecanismos no invasivos:
1. **Sobreescritura en tiempo de ejecución (Parámetro):**
   ```python
   settings = get_database_settings(db_name_override="auditoria_iam_upharven_pruebas")
   ```
2. **Aislamiento por variable de entorno:**
   Configurar `DB_NAME=auditoria_iam_upharven_pruebas` en el archivo `.env` o en la sesión de terminal (`$env:DB_NAME="auditoria_iam_upharven_pruebas"`).

---

## 4. CONEXIÓN MYSQL Y GESTIÓN DEFENSIVA DE TRANSACCIONES (`connection.py`)

### 4.1. Conexión Segura (`get_connection`)
La función `get_connection(...)` admite opcionalmente una instancia de `DatabaseSettings`, un nombre de base de datos para sobreescritura (`db_name`), o argumentos individuales (`user`, `password`, etc.) para preservar compatibilidad con scripts interactivos anteriores.

**Protección contra Filtración de Errores y Credenciales:**
Los bloques de captura de excepciones en `get_connection()` utilizan mensajes controlados y genéricos que identifican la ubicación de red pero jamás propagan `exc.msg`, detalles de autenticación del usuario, contraseñas ni cadenas internas del motor:
```python
    except mysql.connector.Error:
        raise RuntimeError(
            f"Error al conectar con la base de datos MySQL en {cfg.host}:{cfg.port}/{cfg.name}. "
            "Verifique los parámetros de red y autenticación."
        ) from None
    except Exception:
        raise RuntimeError(
            f"Fallo no esperado al intentar conectar con la base de datos MySQL en {cfg.host}:{cfg.port}/{cfg.name}."
        ) from None
```
El uso de `from None` suprime el encadenamiento de excepciones internas de bajo nivel, impidiendo la exposición de trazas sensibles en logs o interfaces de usuario.

### 4.2. Context Manager de Lectura (`get_db_cursor`)
Diseñado para consultas `SELECT` de auditoría:
```python
@contextmanager
def get_db_cursor(dictionary: bool = True, db_name: Optional[str] = None, settings: Optional[DatabaseSettings] = None):
    # Obtiene conexión y cursor (dictionary=True por defecto)
    # Entrega el cursor en el bloque with
    # En bloque finally garantiza: cursor.close() y connection.close()
```
- No ejecuta `commit`.
- Cierre defensivo garantizado incluso si ocurre un fallo al instanciar el cursor.

### 4.3. Context Manager Transaccional (`get_db_transaction`)
Diseñado para futuras operaciones atómicas de escritura (Fase 3):
```python
@contextmanager
def get_db_transaction(dictionary: bool = True, db_name: Optional[str] = None, settings: Optional[DatabaseSettings] = None):
    # Inicia conexión y cursor
    # Si el bloque with finaliza con éxito -> connection.commit()
    # Si ocurre una excepción -> connection.rollback() y re-eleva la excepción
    # En bloque finally garantiza: cursor.close() y connection.close()
```

---

## 5. CAPA DE REPOSITORIO DE DATOS (`repository.py`)

El repositorio proporciona **18 funciones de solo lectura**, estructuradas de manera modular y organizadas según el dominio del modelo relacional. Todas utilizan consultas parametrizadas con marcadores `%s`, evitando cualquier vector de inyección SQL.

### 5.1. Módulo de Recursos IAM (`resources`)
1. `get_resources(user: Optional[str] = None, password: Optional[str] = None, source_type: str = "simulacion", db_name: Optional[str] = None) -> List[Dict[str, Any]]`:  
   Obtiene identidades y recursos registrados filtrados por tipo de origen (`source_type`, por defecto `"simulacion"`). Admite parámetros de compatibilidad interactiva (`user`, `password`).
2. `get_resource_by_id(resource_id: int, db_name: Optional[str] = None) -> Optional[Dict[str, Any]]`:  
   Consulta la información detallada de un recurso por su clave primaria `resources.id`.
3. `get_resource_by_key(resource_key: str, source_type: str = "simulacion", db_name: Optional[str] = None) -> Optional[Dict[str, Any]]`:  
   Busca un recurso por su clave única (`resource_key`) y tipo de fuente (`source_type`).

### 5.2. Módulo de Reglas de Auditoría (`audit_rules`)
4. `get_active_rules(db_name: Optional[str] = None) -> List[Dict[str, Any]]`:  
   Recupera las reglas de auditoría actualmente activas (`WHERE is_active = 1`) en `audit_rules`.
5. `get_rule_by_code(rule_code: str, db_name: Optional[str] = None) -> Optional[Dict[str, Any]]`:  
   Consulta una regla por su identificador formal de catálogo `audit_rules.rule_code` (ej. `'IAM-001'`).
6. `get_rule_by_id(rule_id: int, db_name: Optional[str] = None) -> Optional[Dict[str, Any]]`:  
   Consulta una regla por su clave primaria `audit_rules.id`.

### 5.3. Módulo de Perfiles de Acceso Autorizados (Nuevas Tablas Fase 2)
7. `get_active_profiles(identity_type: Optional[str] = None, db_name: Optional[str] = None) -> List[Dict[str, Any]]`:  
   Consulta perfiles de acceso vigentes (`status = 'active'`) en `access_profiles`, con filtro opcional por tipo de identidad (`identity_type`: `'user'` o `'role'`).
8. `get_profile_by_code(profile_code: str, db_name: Optional[str] = None) -> Optional[Dict[str, Any]]`:  
   Obtiene un perfil de acceso por su código nemotécnico `access_profiles.profile_code`.
9. `get_profile_by_id(profile_id: int, db_name: Optional[str] = None) -> Optional[Dict[str, Any]]`:  
   Obtiene un perfil de acceso por su clave primaria `access_profiles.id`.
10. `get_resource_active_profile(resource_id: int, db_name: Optional[str] = None) -> Optional[Dict[str, Any]]`:  
    Consulta la asignación vigente de perfil para un recurso en `resource_access_profiles` (`valid_to IS NULL`), realizando `JOIN` con `access_profiles`.
11. `get_profile_expected_groups(profile_id: int, db_name: Optional[str] = None) -> List[Dict[str, Any]]`:  
    Consulta los nombres de grupos IAM esperados y autorizados para un perfil en `profile_expected_groups`.
12. `get_profile_expected_trust_principals(profile_id: int, db_name: Optional[str] = None) -> List[Dict[str, Any]]`:  
    Consulta las entidades y acciones de confianza autorizadas para un perfil de rol en `profile_expected_trust_principals`.

### 5.4. Módulo de Ejecuciones, Resultados, Hallazgos y Evidencias
13. `get_audit_runs(limit: int = 50, db_name: Optional[str] = None) -> List[Dict[str, Any]]`:  
    Recupera el historial de ejecuciones de auditoría en orden cronológico descendente (`audit_runs`), acotado por el parámetro `limit`.
14. `get_audit_run_by_id(run_id: int, db_name: Optional[str] = None) -> Optional[Dict[str, Any]]`:  
    Obtiene el encabezado y estado de una ejecución de auditoría por su clave primaria `audit_runs.id`.
15. `get_audit_results_by_run(audit_run_id: int, result_status: Optional[str] = None, db_name: Optional[str] = None) -> List[Dict[str, Any]]`:  
    Consulta los resultados detallados de una ejecución en `audit_results` (con `JOIN` a `resources` y `audit_rules`), con filtro opcional por estado (`result_status`: `'Conforme'`, `'Hallazgo'`, `'No evaluable'`).
16. `get_findings_by_run(audit_run_id: int, db_name: Optional[str] = None) -> List[Dict[str, Any]]`:  
    Consulta los hallazgos registrados en una ejecución (`findings` con `JOIN` a `resources` y `audit_rules` vinculados por `audit_run_id`).
17. `get_evidence_by_finding(finding_id: int, db_name: Optional[str] = None) -> List[Dict[str, Any]]`:  
    Recupera los registros de evidencia técnica (`audit_evidence`) vinculados a un hallazgo (`finding_id`).
18. `get_evidence_by_audit_result(audit_result_id: int, db_name: Optional[str] = None) -> List[Dict[str, Any]]`:  
    Recupera las evidencias vinculadas directamente a una evaluación (`audit_results.id`).

---

## 6. PRUEBAS AUTOMATIZADAS Y RESULTADOS

Se diseñó una suite de pruebas unitarias automatizadas con `pytest` y `unittest.mock`. Se declara de forma expresa que **todas las pruebas se ejecutaron mediante dobles de prueba (mocks)**, en un entorno de ejecución aislado de red, sin establecer conexiones reales de socket ni interactuar con el servidor MySQL Server local.

### 6.1. Resumen de Ejecución
- **Comando:** `pytest tests -v`
- **Total de pruebas:** 38
- **Aprobadas:** 38 (100%)
- **Fallidas:** 0
- **Tiempo de ejecución:** 1.14 segundos

### 6.2. Detalle por Suite

| Suite de Prueba | Casos | Aspectos Validados | Resultado |
|---|:---:|---|:---:|
| `tests/test_settings.py` | 8 | Carga de variables de entorno, sobreescritura de `db_name_override`, validación de campos obligatorios faltantes (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`), validación de rangos numéricos de `DB_PORT` (cero, negativos, > 65535, alfanuméricos) y `DB_CONNECT_TIMEOUT` (<= 0). | APROBADO (8/8) |
| `tests/test_connection.py` | 6 | Conexión con parámetros válidos, context manager `get_db_cursor` (cierre garantizado de cursor y conexión), context manager `get_db_transaction` (commit ante éxito y rollback ante excepción), mensajes de error controlados sin divulgar credenciales ni mensajes internos del motor, y liberación defensiva ante fallos en `conn.cursor()`. | APROBADO (6/6) |
| `tests/test_repository.py` | 24 | Cobertura de las 18 consultas de repositorio, verificación de consultas vacías, verificación de compatibilidad con firmas previas (`user`, `password`), aserción de consultas parametrizadas con `%s` en lugar de concatenaciones, e inspección estática del árbol sintáctico (AST) de `repository.py` comprobando ausencia total de sentencias de escritura (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`). | APROBADO (24/24) |

---

## 7. DEPENDENCIAS UTILIZADAS

Las librerías requeridas se encuentran instaladas en el entorno virtual (`.venv`):
- **`mysql-connector-python` (versión 9.x):** Conector oficial para MySQL, utilizado para la gestión de conexiones de socket, cursores de diccionario y transacciones.
- **`python-dotenv`:** Carga y parseo seguro de variables de entorno desde el archivo `.env`.
- **`pytest`:** Marco de ejecución de pruebas unitarias automatizadas y análisis de regresión.
- **Librería estándar de Python:** `dataclasses`, `contextlib`, `os`, `re`, `ast`, `typing`, `unittest.mock`.

---

## 8. INCIDENCIAS ENCONTRADAS Y RESOLUCIÓN

1. **Protección de errores y sanitización de excepciones en `connection.py`:**
   - *Incidencia:* La captura de excepciones en `get_connection()` incorporaba `{exc.msg}` y `{exc}`, lo que podía divulgar detalles internos del servidor o mensajes de denegación de acceso.
   - *Solución:* Se sustituyeron por mensajes controlados estandarizados que no divulgan detalles internos ni trazas, suprimiendo el encadenamiento de excepciones con `from None`.
2. **Carga no invasiva de configuración en `settings.py`:**
   - *Incidencia:* El uso potencial de `override=True` en `load_dotenv()` podía sobrescribir variables de entorno del sistema operativo.
   - *Solución:* Se fijó `override=False` garantizando que no se muten variables globales existentes.
3. **Consistencia de inventario y firmas del repositorio:**
   - *Incidencia:* La documentación preliminar referenciaba 16 funciones con firmas aproximadas.
   - *Solución:* Se actualizó la documentación a las 18 funciones reales con sus tipos, parámetros exactos y filtros implementados en el código.

---

## 9. LIMITACIONES ACTUALES Y ALCANCE PENDIENTE

1. **Solo lectura:** La capa de repositorio implementada en esta Entrega 2 contiene intencionalmente operaciones exclusivas de lectura (`SELECT`). La persistencia transaccional de nuevas corridas (`INSERT INTO audit_runs`, `audit_results`, `findings`, `audit_evidence`) forma parte del alcance de la **Fase 3: Motor de Auditoría y Detección de No Conformidades**.
2. **Integración con AWS:** No se ejecutan llamadas a AWS IAM mediante `boto3` en esta entrega; el repositorio se enfoca estrictamente en la persistencia local en MySQL.
3. **Interfaz gráfica:** La integración con la GUI PySide6 se abordará en su fase respectiva una vez estabilizado el motor de reglas y la generación de reportes.

---

## 10. DECLARACIÓN EXPRESA DE INTEGRIDAD DE DATOS

> **DECLARACIÓN FORMAL:**  
> Se certifica de manera categórica que durante el diseño, implementación, corrección y verificación de la presente **Entrega 2 de la Fase 2**, **NO se ejecutó ninguna sentencia DDL ni DML de modificación** (`CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `INSERT`, `UPDATE`, `DELETE`) sobre el servidor MySQL real.  
> Los esquemas y los registros de las bases de datos `auditoria_iam_upharven` (base de datos original) y `auditoria_iam_upharven_pruebas` (base de datos de pruebas) se mantienen intactos e inalterados.
