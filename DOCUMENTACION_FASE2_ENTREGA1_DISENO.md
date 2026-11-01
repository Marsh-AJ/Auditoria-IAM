# DOCUMENTACIÓN TÉCNICA — FASE 2: ENTREGA 1 (VERSIÓN 2.5 REVISADA)
## DISEÑO Y PREPARACIÓN DE LA MIGRACIÓN DE BASE DE DATOS

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO/IEC 27001 para UPHARVEN C.A.  
**Fase:** Fase 2 — Consolidación de la base de datos y persistencia  
**Entrega:** Entrega 1 — Diseño y preparación de la migración de base de datos  
**Versión del documento:** 2.5 (Validación Real de Claves Primarias y Verificación de Índices)  
**Fecha:** 31 de octubre de 2026  
**Estado de aprobación:** **Versión 2.5 — pendiente de revisión y autorización de ejecución**  
**Autor:** Antigravity (Desarrollador Senior, Arquitecto de Software y Auditor de Código)  

---

## 1. Identificación y objetivo de la entrega

### 1.1. Objetivo de la entrega
Proporcionar el diseño técnico definitivo, riguroso y no destructivo para la ampliación del esquema relacional en MySQL Server 9.6 de la base de datos `auditoria_iam_upharven`. El propósito es dar soporte a los perfiles de acceso de referencia, el registro exhaustivo de resultados del motor (`Conforme`, `Hallazgo`, `No evaluable`) y la trazabilidad de evidencias, garantizando que **los 14 registros históricos en `findings`, los 14 registros históricos en `audit_evidence`, las cuatro identidades simuladas en `resources` y las cuatro reglas ISO/IEC 27001 (IAM-001 a IAM-004) permanezcan intactos e inalterados**.

Esta versión 2.5 perfecciona los siguientes aspectos técnicos:
1. **Validación real de las cinco claves primarias:** Se comprueba que `resources.id`, `audit_runs.id`, `audit_rules.id`, `findings.id` y `audit_evidence.id` existan, sean de tipo `BIGINT UNSIGNED`, formen parte de la `PRIMARY KEY` (`COLUMN_KEY = 'PRI'`) y posean el atributo `AUTO_INCREMENT`.
2. **Clarificación estricta de `audit_evidence.finding_id`:** Se documenta e inspecciona como una **clave foránea histórica** hacia `findings.id`, no como clave primaria.
3. **Comprobación previa de nombres de índices:** Se inspecciona en `information_schema.STATISTICS` que los nombres de índices a incorporar (`idx_findings_audit_result_id` y `idx_evidence_audit_result_id`) no preexistan en las tablas históricas, abortando de inmediato ante cualquier colisión previa.
4. **Precisión técnica y documental:** Se elimina cualquier afirmación que sugiera atomicidad global de la migración, describiéndola formalmente como una **creación controlada de estructuras sobre un estado inicial conocido**.
5. **Advertencia de commits implícitos:** Se enfatiza que las instrucciones DDL en MySQL emiten commits implícitos y no admiten reversión automática total mediante `ROLLBACK`.

**Declaración formal: En esta entrega NO se ha ejecutado ninguna sentencia SQL, no se ha conectado a MySQL ni se ha modificado la base de datos real.**

---

## 2. Estrategia de creación controlada sobre estado inicial conocido

### 2.1. Premisa técnica del estado inicial conocido
La migración no intenta gestionar estados parciales desconocidos ni aplicar parches automáticos sobre tablas intermedias. Su seguridad se fundamenta en validar que el entorno se encuentre estrictamente en el estado inicial previsto:
1. Las cinco tablas originales existen, operan bajo el motor de almacenamiento **InnoDB** y tienen sus claves primarias y relaciones históricas íntegras.
2. Ninguna de las cinco tablas nuevas (`access_profiles`, `profile_expected_groups`, `profile_expected_trust_principals`, `resource_access_profiles`, `audit_results`) existe en el esquema.
3. Ninguna de las columnas nuevas (`findings.audit_result_id`, `audit_evidence.audit_result_id`) existe en las tablas históricas.
4. Ninguno de los nombres de índices nuevos (`idx_findings_audit_result_id`, `idx_evidence_audit_result_id`) ni restricciones nuevas (`fk_findings_audit_result`, `fk_evidence_audit_result`, `chk_evidence_target`) existe previamente.
5. Si cualquiera de estos objetos preexiste, el procedimiento **aborta inmediatamente mediante `SIGNAL SQLSTATE '45000'`**, exigiendo intervención e inspección manual del administrador antes de aplicar cualquier sentencia DDL.

### 2.2. Diagrama de flujo del procedimiento `sp_migrar_esquema_fase2`

```
[ INICIO DEL PROCEDIMIENTO ]
    │
    ▼
[ FASE 1: Verificación de Prerrequisitos Base ]
  ├─ 5 tablas base existen con motor InnoDB ──────────────(Falla)──► ABORTA (SIGNAL 45000)
  ├─ 5 PKs reales validadas (PRI, BIGINT UNSIGNED, AUTO_INC) ──(Falla)──► ABORTA (SIGNAL 45000)
  ├─ audit_evidence.finding_id es BIGINT UNSIGNED ────────(Falla)──► ABORTA (SIGNAL 45000)
  ├─ FK histórica audit_evidence -> findings confirmada ──(Falla)──► ABORTA (SIGNAL 45000)
  └─ Umbrales mínimos volumétricos (14 y 14) confirmados ──(Falla)──► ABORTA (SIGNAL 45000)
    │ (Todo correcto)
    ▼
[ FASE 2: Comprobación de Ausencia de Objetos Nuevos ]
  ├─ 5 tablas nuevas NO existen ─────────────────────────(Existe)──► ABORTA (SIGNAL 45000)
  ├─ Columnas audit_result_id NO existen ────────────────(Existe)──► ABORTA (SIGNAL 45000)
  ├─ Restricciones nuevas NO existen ────────────────────(Existe)──► ABORTA (SIGNAL 45000)
  └─ Índices nuevos en históricas NO existen ────────────(Existe)──► ABORTA (SIGNAL 45000)
    │ (Estado inicial limpio confirmado)
    ▼
[ FASE 3: Creación de las Cinco Tablas Nuevas ]
  ├─ CREATE TABLE access_profiles
  ├─ CREATE TABLE profile_expected_groups
  ├─ CREATE TABLE profile_expected_trust_principals
  ├─ CREATE TABLE resource_access_profiles (is_active_flag virtual + UK)
  └─ CREATE TABLE audit_results
    │
    ▼
[ FASE 4: Adaptación de Tablas Históricas ]
  ├─ findings: ADD audit_result_id NULL + FK + Index
  └─ audit_evidence: MODIFY finding_id NULL (si aplica) + ADD audit_result_id NULL + FK + Index + CHECK
    │
    ▼
[ FIN EXITOSO DEL PROCEDIMIENTO ]
```

---

## 3. Matriz de validación real de claves primarias y relaciones históricas

| Tabla | Columna Validada | Rol en el Esquema | Propiedades Exactas Verificadas en Procedimiento | Comportamiento si no cumple |
| :--- | :--- | :--- | :--- | :--- |
| **`resources`** | `id` | **Clave Primaria** | `COLUMN_TYPE = 'bigint unsigned'`<br>`COLUMN_KEY = 'PRI'`<br>`EXTRA LIKE '%auto_increment%'` | `SIGNAL SQLSTATE '45000'` (Aborta) |
| **`audit_runs`** | `id` | **Clave Primaria** | `COLUMN_TYPE = 'bigint unsigned'`<br>`COLUMN_KEY = 'PRI'`<br>`EXTRA LIKE '%auto_increment%'` | `SIGNAL SQLSTATE '45000'` (Aborta) |
| **`audit_rules`** | `id` | **Clave Primaria** | `COLUMN_TYPE = 'bigint unsigned'`<br>`COLUMN_KEY = 'PRI'`<br>`EXTRA LIKE '%auto_increment%'` | `SIGNAL SQLSTATE '45000'` (Aborta) |
| **`findings`** | `id` | **Clave Primaria** | `COLUMN_TYPE = 'bigint unsigned'`<br>`COLUMN_KEY = 'PRI'`<br>`EXTRA LIKE '%auto_increment%'` | `SIGNAL SQLSTATE '45000'` (Aborta) |
| **`audit_evidence`** | `id` | **Clave Primaria** | `COLUMN_TYPE = 'bigint unsigned'`<br>`COLUMN_KEY = 'PRI'`<br>`EXTRA LIKE '%auto_increment%'` | `SIGNAL SQLSTATE '45000'` (Aborta) |
| **`audit_evidence`** | `finding_id` | **Clave Foránea Histórica** | `COLUMN_TYPE = 'bigint unsigned'`<br>Verificación en `KEY_COLUMN_USAGE` y `REFERENTIAL_CONSTRAINTS` apuntando a `findings(id)` | `SIGNAL SQLSTATE '45000'` (Aborta) |

---

## 4. Diseño aprobado de tablas y reglas de integridad

### 4.1. Tablas nuevas
1. **`access_profiles`:** Catálogo de perfiles autorizados (`profile_code` único, `identity_type` restringido a `'user'` o `'role'`, `status` restringido a `'active'`, `'inactive'`, `'deprecated'`).
2. **`profile_expected_groups`:** Grupos esperados para perfiles de tipo `'user'` (`uk_profile_expected_group` compuesto sobre `(profile_id, group_name)` y FK con `ON DELETE RESTRICT ON UPDATE CASCADE`).
3. **`profile_expected_trust_principals`:** Entidades de confianza para perfiles de tipo `'role'` (`uk_profile_principal_action` compuesto sobre `(profile_id, principal_type, principal_identifier, trust_action)` y FK hacia `access_profiles`).
4. **`resource_access_profiles`:** Historial de asignaciones. Incorpora la columna generada virtual `is_active_flag TINYINT GENERATED ALWAYS AS (IF(valid_to IS NULL, 1, NULL)) VIRTUAL` y la restricción `UNIQUE uk_resource_single_active_profile (resource_id, is_active_flag)`. Impide físicamente tener más de un perfil activo (`valid_to IS NULL`), permitiendo múltiples asignaciones históricas pasadas (`valid_to IS NOT NULL`).
5. **`audit_results`:** Almacén unificado de todas las evaluaciones algorítmicas con estados estrictos `'Conforme'`, `'Hallazgo'` y `'No evaluable'`, FKs hacia `audit_runs`, `resources`, `audit_rules` y `access_profiles`, y restricción UNIQUE sobre `(audit_run_id, resource_id, audit_rule_id, criterion_code)`.

### 4.2. Adaptación no destructiva de tablas históricas
1. **`findings`:** Se agrega la columna `audit_result_id BIGINT UNSIGNED NULL`, FK hacia `audit_results(id)` con `RESTRICT`/`CASCADE` e índice `idx_findings_audit_result_id`. Los 14 registros históricos conservan `audit_result_id = NULL`.
2. **`audit_evidence`:** Se modifica `finding_id` a nullable únicamente si actualmente es `NOT NULL` (preservando la clave foránea histórica hacia `findings`), se agrega `audit_result_id BIGINT UNSIGNED NULL`, FK hacia `audit_results(id)`, índice `idx_evidence_audit_result_id` y restricción CHECK de exclusión mutua estricta:
   ```sql
   CONSTRAINT `chk_evidence_target` CHECK (
       (`finding_id` IS NOT NULL AND `audit_result_id` IS NULL) OR
       (`finding_id` IS NULL AND `audit_result_id` IS NOT NULL)
   )
   ```

---

## 5. Protocolo de auditoría y preservación de datos históricos

### 5.1. Distinción metodológica de comprobaciones
- **Comprobaciones automáticas del procedimiento:** Verifican existencia de tablas, motor InnoDB, tipos de claves primarias, presencia de clave foránea histórica y umbral volumétrico mínimo (`COUNT(*) >= 14`).
- **Comprobaciones manuales previas y posteriores:** Cotejo cualitativo fila por fila de los 14 hallazgos y 14 evidencias antes y después de la migración para verificar identificadores, marcas de tiempo y relaciones.
- **Pruebas pendientes en copia:** Verificación experimental previa del procedimiento en una copia de MySQL Server 9.6.

### 5.2. Consultas para el cotejo previo y posterior a la migración

#### 1. Auditoría de los 14 hallazgos históricos (`findings`)
```sql
SELECT 
    id,
    audit_run_id,
    resource_id,
    audit_rule_id,
    result_status,
    severity,
    finding_title,
    description,
    recommendation,
    observed_value,
    detected_at
FROM findings
ORDER BY id;
```
*Criterio de éxito post-migración:* Los 14 registros deben arrojar exactamente los mismos valores en todos sus campos originales. La nueva columna `audit_result_id` debe ser estrictamente `NULL` en los 14 registros.

#### 2. Auditoría de las 14 evidencias históricas (`audit_evidence`)
```sql
SELECT 
    ae.id,
    ae.finding_id,
    ae.evidence_type,
    ae.evidence_detail,
    ae.evidence_reference,
    ae.captured_at,
    f.id AS finding_verificado
FROM audit_evidence ae
JOIN findings f ON ae.finding_id = f.id
ORDER BY ae.id;
```
*Criterio de éxito post-migración:* Las 14 evidencias deben conservar su `finding_id` original apuntando a su hallazgo histórico correspondiente. La nueva columna `audit_result_id` debe ser estrictamente `NULL` en las 14 filas.

#### 3. Verificación de exclusión mutua estricta en el catálogo
```sql
-- Debe retornar exactamente 0 registros anómalos
SELECT COUNT(*) AS filas_invalidas
FROM audit_evidence
WHERE NOT (
    (finding_id IS NOT NULL AND audit_result_id IS NULL)
    OR
    (finding_id IS NULL AND audit_result_id IS NOT NULL)
);
```

---

## 6. Propuesta técnica para Python: Gestión defensiva de conexiones

### 6.1. Definición rigurosa de contextos
- **`get_db_cursor()`:** Contexto destinado conceptualmente a consultas de lectura en la capa de software. No emite `connection.commit()` automático. *Aclaración:* no impone un bloqueo físico a nivel de motor de base de datos contra sentencias de escritura, sino que establece la convención arquitectónica para persistencia limpia.
- **`get_db_transaction()`:** Contexto destinado a transacciones de escritura. Emite `connection.commit()` al concluir con éxito y `connection.rollback()` ante cualquier excepción.

### 6.2. Código propuesto con cierre defensivo
```python
"""
Módulo de Conexión y Persistencia Defensiva para MySQL Server 9.6.
Aplica cierre defensivo de conexión ante cualquier fallo durante cursor().
"""
from contextlib import contextmanager
import mysql.connector
from src.auditoria_iam.config.settings import db_settings

def get_raw_connection(settings=None):
    cfg = settings or db_settings
    try:
        return mysql.connector.connect(
            host=cfg.host,
            port=cfg.port,
            database=cfg.name,
            user=cfg.user,
            password=cfg.password,
            connection_timeout=cfg.timeout,
            autocommit=False
        )
    except Exception as exc:
        # Mensaje seguro que oculta contraseñas y detalles sensibles de red
        raise RuntimeError(
            f"No se pudo establecer conexión con la base de datos en {cfg.host}:{cfg.port}/{cfg.name}. "
            f"Verifique la disponibilidad del servicio y la validez de las credenciales en .env."
        ) from None

@contextmanager
def get_db_cursor(dictionary=True):
    """
    Gestor de contexto destinado a consultas de lectura.
    Garantiza el cierre defensivo de la conexión incluso si falla connection.cursor().
    """
    connection = get_raw_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=dictionary)
        yield cursor
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        try:
            connection.close()
        except Exception:
            pass

@contextmanager
def get_db_transaction(dictionary=True):
    """
    Gestor de contexto para transacciones de escritura.
    Ejecuta commit en éxito y rollback obligatorio ante cualquier excepción.
    """
    connection = get_raw_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=dictionary)
        yield cursor
        connection.commit()
    except Exception:
        try:
            connection.rollback()
        except Exception:
            pass
        raise
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        try:
            connection.close()
        except Exception:
            pass
```

---

## 7. Riesgos de ejecución DDL, privilegios y pruebas pendientes

### 7.1. Naturaleza DDL y ausencia de atomicidad global
En MySQL, las instrucciones DDL (`CREATE TABLE`, `ALTER TABLE`) emiten **commits implícitos**. Por consiguiente:
- La migración **no es globalmente atómica**.
- Si ocurre una desconexión o fallo a mitad del procedimiento, **no es posible realizar un ROLLBACK automático total**.
- El esquema podría quedar en un estado parcialmente migrado.
- **Mitigación obligatoria:** Antes de ejecutar el procedimiento, se debe generar un respaldo lógico completo con `mysqldump`:
  ```powershell
  mysqldump -h 127.0.0.1 -P 3306 -u root -p --routines --triggers --single-transaction auditoria_iam_upharven > respaldo_fase2_previo_migracion.sql
  ```
  En caso de interrupción catastrófica, la restauración se realiza mediante:
  ```powershell
  mysql -h 127.0.0.1 -P 3306 -u root -p auditoria_iam_upharven < respaldo_fase2_previo_migracion.sql
  ```

### 7.2. Matriz de privilegios requeridos en MySQL Server 9.6
Para la ejecución segura del ciclo de migración, el usuario configurado en `.env` debe disponer de los siguientes privilegios en el esquema `auditoria_iam_upharven`:
1. `SELECT`, `INSERT`, `UPDATE` en las tablas del esquema.
2. `CREATE`, `ALTER` sobre tablas del esquema.
3. `CREATE ROUTINE` para compilar el procedimiento almacenado.
4. `EXECUTE` para ejecutar el procedimiento vía `CALL sp_migrar_esquema_fase2()`.
5. `ALTER ROUTINE` para ejecutar la limpieza posterior vía `DROP PROCEDURE IF EXISTS sp_migrar_esquema_fase2`.

### 7.3. Pruebas pendientes en una copia de MySQL Server 9.6
- **Estado de prueba experimental:** Debido a las restricciones de aislamiento del entorno de desarrollo sandboxed (error WSAEACCES 10013 en socket local), **la compatibilidad experimental y sintáctica del archivo SQL en MySQL Server 9.6 queda expresamente catalogada como pendiente de prueba en una instancia clonada**. No se afirma compatibilidad empírica que no haya sido ejecutada.
- **Puntos específicos a comprobar en copia:**
  1. Comprobar que `ALTER TABLE audit_evidence MODIFY COLUMN finding_id BIGINT UNSIGNED NULL` no degrade índices existentes ni altere el estado de la clave foránea histórica en InnoDB.
  2. Comprobar que la sintaxis de columna generada virtual `is_active_flag` sea aceptada sin advertencias por el optimizador de consultas de MySQL Server 9.6.

---

## 8. Inventario de archivos de la entrega

1. **[`FASE2_MIGRACION_PRELIMINAR.sql`](file:///C:/Users/andre/Desktop/TESIS/sistema/FASE2_MIGRACION_PRELIMINAR.sql):**
   - Script SQL formal versión 2.5 (archivo SQL puro, sin markdown ni caracteres de escape).
   - Estado: **Sin ejecutar**.
2. **[`DOCUMENTACION_FASE2_ENTREGA1_DISENO.md`](file:///C:/Users/andre/Desktop/TESIS/sistema/DOCUMENTACION_FASE2_ENTREGA1_DISENO.md):**
   - Presente memoria técnica versión 2.5 actualizada.
3. **[`INFORME_CORRECCIONES_V2.5.md`](file:///C:/Users/andre/Desktop/TESIS/sistema/INFORME_CORRECCIONES_V2.5.md):**
   - Documento que resume las observaciones resueltas en esta iteración.

---

## 9. Declaración formal de no ejecución y estado del documento

> [!IMPORTANT]
> **DECLARACIÓN DE NO EJECUCIÓN:**  
> Se certifica formalmente que:
> - **NO** se ejecutó ninguna sentencia SQL en el servidor MySQL Server 9.6.
> - **NO** se alteraron tablas, procedimientos ni registros de la base de datos `auditoria_iam_upharven`.
> - **NO** se modificaron archivos de código fuente dentro de `src/`.
> - **NO** se alteró el archivo `.env`.
> - Los 14 registros históricos de `findings` y 14 de `audit_evidence` permanecen protegidos e intactos.

**Estado final obligatorio:**  
**Versión 2.5 — pendiente de revisión y autorización de ejecución.**
