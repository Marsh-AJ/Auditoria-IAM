# INFORME DE CORRECCIONES TÉCNICAS — FASE 2: ENTREGA 1
## VERSIÓN 2.5: VALIDACIÓN REAL DE CLAVES PRIMARIAS Y VERIFICACIÓN DE ÍNDICES

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO/IEC 27001 para UPHARVEN C.A.  
**Fase:** Fase 2 — Consolidación de la base de datos y persistencia  
**Entrega:** Entrega 1 — Diseño y preparación de la migración de base de datos  
**Documento:** Informe de Cambios y Correcciones v2.5  
**Fecha:** 31 de octubre de 2026  
**Estado:** **Versión 2.5 — pendiente de revisión y autorización de ejecución**  
**Autor:** Antigravity (Desarrollador Senior, Arquitecto de Software y Auditor de Código)  

---

## 1. Resumen ejecutivo de la iteración

La versión 2.5 perfecciona los aspectos de validación estructural y rigor documental de la migración para la Fase 2, consolidando la estrategia de **creación controlada sobre un estado inicial conocido** sin introducir rediseños ni tablas adicionales:

1. **Validación real de las 5 claves primarias:** Se comprueba explícitamente en el catálogo que `resources.id`, `audit_runs.id`, `audit_rules.id`, `findings.id` y `audit_evidence.id` existan, sean de tipo `BIGINT UNSIGNED`, posean la restricción `COLUMN_KEY = 'PRI'` (clave primaria) y el atributo `EXTRA LIKE '%auto_increment%'`.
2. **Clarificación formal de `audit_evidence.finding_id`:** Se ratifica e inspecciona como una **clave foránea histórica** hacia `findings.id`, descartando cualquier confusión que la considere clave primaria de `audit_evidence`. Se mantiene la validación de la FK histórica en `information_schema.KEY_COLUMN_USAGE` y `REFERENTIAL_CONSTRAINTS`.
3. **Comprobación previa de nombres de índices:** Se verifica en `information_schema.STATISTICS` que los índices a incorporar (`idx_findings_audit_result_id` y `idx_evidence_audit_result_id`) no preexistan en las tablas históricas, abortando de inmediato antes de emitir cualquier DDL.
4. **Precisión documental y ausencia de atomicidad global:** Se eliminaron términos como "atómico", describiendo la migración como una creación controlada de estructuras y advirtiendo expresamente sobre los commits implícitos del DDL en MySQL.
5. **Transparencia en el estado de pruebas:** Se declara de forma explícita que la prueba experimental en MySQL Server 9.6 queda **pendiente de verificación en una copia clonada**, debido al aislamiento de red del sandbox.

---

## 2. Detalle de observaciones técnicas resueltas

### Observación 1: Validación real de las cinco claves primarias
- **Situación en v2.4:** Se comprobaba el tipo de dato de algunas columnas, pero no se demostraba fehacientemente que formaran parte de la clave primaria ni que tuvieran el atributo `auto_increment`.
- **Resolución en v2.5:** Se programaron comprobaciones secuenciales e independientes en `information_schema.COLUMNS` para:
  - `resources.id`
  - `audit_runs.id`
  - `audit_rules.id`
  - `findings.id`
  - `audit_evidence.id`
  Para cada una se exige: `COLUMN_TYPE = 'bigint unsigned'`, `COLUMN_KEY = 'PRI'` y `EXTRA LIKE '%auto_increment%'`. Si alguna no cumple, aborta con `SIGNAL SQLSTATE '45000'`.
  Adicionalmente, se valida de forma independiente que `audit_evidence.finding_id` sea `bigint unsigned` y mantenga su clave foránea histórica hacia `findings.id`.

### Observación 2: Comprobación previa de nombres de índices
- **Situación en v2.4:** Solo se comprobaban los nombres de las restricciones (`FOREIGN KEY`), omitiendo la inspección previa de nombres de índices en tablas históricas.
- **Resolución en v2.5:** Se incorporó en la Fase 2 del procedimiento la consulta a `information_schema.STATISTICS` para verificar que `idx_findings_audit_result_id` (en `findings`) e `idx_evidence_audit_result_id` (en `audit_evidence`) no existan. Si alguno existe, el procedimiento aborta inmediatamente antes de alterar tablas.

### Observación 3: Corrección de precisión documental sobre atomicidad
- **Situación en v2.4:** Se empleaban expresiones como "creación atómica de tablas nuevas", lo que podía inducir a error respecto al comportamiento transaccional del DDL en MySQL.
- **Resolución en v2.5:** Se sustituyó dicha terminología por **"creación controlada de estructuras sobre un estado inicial conocido"**. Se mantuvo y reforzó la advertencia de que las instrucciones DDL en MySQL emiten commits implícitos y no permiten una reversión automática total vía `ROLLBACK`.

### Observación 4: Conservación estricta del diseño aprobado v2.4
- **Resolución en v2.5:** Se mantuvieron intactas las estructuras aprobadas: `access_profiles`, `profile_expected_groups`, `profile_expected_trust_principals`, `resource_access_profiles` (con `is_active_flag` virtual y UNIQUE), `audit_results`, la columna `audit_result_id` nullable en `findings` y `audit_evidence`, y la restricción `chk_evidence_target` de exclusión mutua estricta. Los 14 hallazgos y 14 evidencias históricas no se convierten ni se modifican.

### Observación 5: Validación del SQL y estado experimental
- **Situación en v2.4:** No se explicitaba el estado de la prueba sintáctica en MySQL Server 9.6.
- **Resolución en v2.5:** Se entrega `FASE2_MIGRACION_PRELIMINAR.sql` como archivo SQL puro. Se declara expresamente en la documentación que la validación experimental y sintáctica en MySQL Server 9.6 está **pendiente de ejecución en una instancia clonada de prueba**, sin inventar resultados no realizados en el sandbox.

---

## 3. Estado de verificación de criterios de aceptación

- [x] Comprobación explícita de `COLUMN_KEY = 'PRI'` y `AUTO_INCREMENT` para las 5 claves primarias reales.
- [x] Tratamiento estricto de `audit_evidence.finding_id` como clave foránea histórica hacia `findings.id`.
- [x] Comprobación previa de no existencia de `idx_findings_audit_result_id` e `idx_evidence_audit_result_id` en `information_schema.STATISTICS`.
- [x] Eliminación de afirmaciones de atomicidad global en la documentación.
- [x] Conservación íntegra de las 5 tablas nuevas y 2 adaptadas aprobadas.
- [x] Conservación inalterada de los 14 hallazgos y 14 evidencias históricas con `audit_result_id IS NULL`.
- [x] Archivo SQL entregado en formato nativo sin formato markdown incrustado.
- [x] Ninguna sentencia SQL ha sido ejecutada en la base de datos real.

---

## 4. Estado documental final

Los tres archivos de la entrega quedan formalmente actualizados y sincronizados en la raíz del proyecto:
1. 📄 **[`FASE2_MIGRACION_PRELIMINAR.sql`](file:///C:/Users/andre/Desktop/TESIS/sistema/FASE2_MIGRACION_PRELIMINAR.sql)** — Versión 2.5 (SQL Puro).
2. 📄 **[`DOCUMENTACION_FASE2_ENTREGA1_DISENO.md`](file:///C:/Users/andre/Desktop/TESIS/sistema/DOCUMENTACION_FASE2_ENTREGA1_DISENO.md)** — Versión 2.5.
3. 📄 **[`INFORME_CORRECCIONES_V2.5.md`](file:///C:/Users/andre/Desktop/TESIS/sistema/INFORME_CORRECCIONES_V2.5.md)** — Presente informe.

**Estado obligatorio:**  
**Versión 2.5 — pendiente de revisión y autorización de ejecución.**

