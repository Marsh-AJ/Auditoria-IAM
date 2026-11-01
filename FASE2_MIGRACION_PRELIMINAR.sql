-- =============================================================================
-- PROYECTO: Modelo automatizado para la auditoría de gestión de identidades y
--           accesos en entornos de nube basado en el estándar ISO/IEC 27001
--           para UPHARVEN C.A.
-- FASE 2: CONSOLIDACIÓN DE LA BASE DE DATOS Y PERSISTENCIA
-- ENTREGA 1: SCRIPT DE MIGRACIÓN CONTROLADA (VERSIÓN 2.5 - REVISIÓN RIGUROSA)
-- ARCHIVO: FASE2_MIGRACION_PRELIMINAR.sql
-- ESTADO: VERSIÓN 2.5 — PENDIENTE DE REVISIÓN Y AUTORIZACIÓN DE EJECUCIÓN
--
-- ADVERTENCIAS TÉCNICAS Y RESTRICCIONES DE SEGURIDAD:
--   1. ESTE SCRIPT NO DEBE EJECUTARSE EN LA BASE DE DATOS REAL SIN AUTORIZACIÓN
--      EXPRESA Y SIN HABER COMPLETADO Y VERIFICADO UN RESPALDO PREVIO (mysqldump).
--   2. NO CONTIENE SENTENCIAS DROP TABLE, TRUNCATE NI DELETE.
--   3. NO MODIFICA NI ELIMINA LOS 14 HALLAZGOS Y 14 EVIDENCIAS HISTÓRICAS.
--   4. LAS SENTENCIAS DDL EN MYSQL EMITEN COMMITS IMPLÍCITOS. LA MIGRACIÓN
--      NO ES GLOBALMENTE ATÓMICA NI PUEDE REVERTIRSE AUTOMÁTICAMENTE ANTE UN
--      FALLO A MITAD DE PROCESO. POR ELLO, SE VALIDA EXHAUSTIVAMENTE EL ESTADO
--      INICIAL ANTES DE APLICAR CUALQUIER CAMBIO DDL.
-- =============================================================================

USE `auditoria_iam_upharven`;

-- -----------------------------------------------------------------------------
-- PASO PREVIO OBLIGATORIO: INSPECCIÓN INFORMATIVA DE RUTINA PREVIA
-- NOTA OPERATIVA: Consulta SELECT estándar independiente.
-- Si devuelve filas, el administrador DEBE detenerse e inspeccionar antes de continuar.
-- -----------------------------------------------------------------------------
SELECT 
    ROUTINE_SCHEMA, 
    ROUTINE_NAME, 
    ROUTINE_TYPE, 
    CREATED, 
    LAST_ALTERED
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = 'auditoria_iam_upharven'
  AND ROUTINE_NAME = 'sp_migrar_esquema_fase2';


-- -----------------------------------------------------------------------------
-- PROCEDIMIENTO ALMACENADO DE MIGRACIÓN CONTROLADA
-- -----------------------------------------------------------------------------
DELIMITER //

CREATE PROCEDURE `sp_migrar_esquema_fase2`()
sp_block: BEGIN
    DECLARE v_schema VARCHAR(64) DEFAULT 'auditoria_iam_upharven';
    DECLARE v_count INT DEFAULT 0;
    DECLARE v_col_type VARCHAR(64) DEFAULT '';
    DECLARE v_col_key VARCHAR(10) DEFAULT '';
    DECLARE v_extra VARCHAR(64) DEFAULT '';
    DECLARE v_is_null VARCHAR(10) DEFAULT '';

    -- Manejador de excepciones SQL generales
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1
            @sql_state = RETURNED_SQLSTATE,
            @errno = MYSQL_ERRNO,
            @text = MESSAGE_TEXT;
        RESIGNAL SET MESSAGE_TEXT = @text;
    END;

    -- =========================================================================
    -- FASE 1: VALIDACIÓN REAL DE PRERREQUISITOS DE LAS CINCO TABLAS ORIGINALES
    -- =========================================================================

    -- 1.1. Verificar presencia de las 5 tablas base del esquema original
    SELECT COUNT(*) INTO v_count
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = v_schema
      AND TABLE_NAME IN ('audit_runs', 'resources', 'audit_rules', 'findings', 'audit_evidence');

    IF v_count < 5 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: Faltan tablas base del esquema original (se esperaban 5).';
    END IF;

    -- 1.2. Verificar que las 5 tablas base utilicen motor InnoDB
    SET v_count = 0;
    SELECT COUNT(*) INTO v_count
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = v_schema
      AND TABLE_NAME IN ('audit_runs', 'resources', 'audit_rules', 'findings', 'audit_evidence')
      AND ENGINE = 'InnoDB';

    IF v_count < 5 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: Una o mas tablas base no utilizan el motor InnoDB.';
    END IF;

    -- 1.3. Validación real de las cinco claves primarias (PK, BIGINT UNSIGNED, AUTO_INCREMENT)
    -- (a) resources.id
    SET v_col_type = '', v_col_key = '', v_extra = '';
    SELECT COLUMN_TYPE, COLUMN_KEY, EXTRA INTO v_col_type, v_col_key, v_extra
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = v_schema AND TABLE_NAME = 'resources' AND COLUMN_NAME = 'id';
    IF v_col_type != 'bigint unsigned' OR v_col_key != 'PRI' OR v_extra NOT LIKE '%auto_increment%' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: resources.id no cumple como PK BIGINT UNSIGNED AUTO_INCREMENT.';
    END IF;

    -- (b) audit_runs.id
    SET v_col_type = '', v_col_key = '', v_extra = '';
    SELECT COLUMN_TYPE, COLUMN_KEY, EXTRA INTO v_col_type, v_col_key, v_extra
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = v_schema AND TABLE_NAME = 'audit_runs' AND COLUMN_NAME = 'id';
    IF v_col_type != 'bigint unsigned' OR v_col_key != 'PRI' OR v_extra NOT LIKE '%auto_increment%' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: audit_runs.id no cumple como PK BIGINT UNSIGNED AUTO_INCREMENT.';
    END IF;

    -- (c) audit_rules.id
    SET v_col_type = '', v_col_key = '', v_extra = '';
    SELECT COLUMN_TYPE, COLUMN_KEY, EXTRA INTO v_col_type, v_col_key, v_extra
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = v_schema AND TABLE_NAME = 'audit_rules' AND COLUMN_NAME = 'id';
    IF v_col_type != 'bigint unsigned' OR v_col_key != 'PRI' OR v_extra NOT LIKE '%auto_increment%' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: audit_rules.id no cumple como PK BIGINT UNSIGNED AUTO_INCREMENT.';
    END IF;

    -- (d) findings.id
    SET v_col_type = '', v_col_key = '', v_extra = '';
    SELECT COLUMN_TYPE, COLUMN_KEY, EXTRA INTO v_col_type, v_col_key, v_extra
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = v_schema AND TABLE_NAME = 'findings' AND COLUMN_NAME = 'id';
    IF v_col_type != 'bigint unsigned' OR v_col_key != 'PRI' OR v_extra NOT LIKE '%auto_increment%' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: findings.id no cumple como PK BIGINT UNSIGNED AUTO_INCREMENT.';
    END IF;

    -- (e) audit_evidence.id (Clave primaria real de audit_evidence)
    SET v_col_type = '', v_col_key = '', v_extra = '';
    SELECT COLUMN_TYPE, COLUMN_KEY, EXTRA INTO v_col_type, v_col_key, v_extra
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = v_schema AND TABLE_NAME = 'audit_evidence' AND COLUMN_NAME = 'id';
    IF v_col_type != 'bigint unsigned' OR v_col_key != 'PRI' OR v_extra NOT LIKE '%auto_increment%' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: audit_evidence.id no cumple como PK BIGINT UNSIGNED AUTO_INCREMENT.';
    END IF;

    -- 1.4. Validación de la columna finding_id en audit_evidence (Clave foránea histórica)
    SET v_col_type = '', v_col_key = '';
    SELECT COLUMN_TYPE, COLUMN_KEY INTO v_col_type, v_col_key
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = v_schema AND TABLE_NAME = 'audit_evidence' AND COLUMN_NAME = 'finding_id';
    IF v_col_type != 'bigint unsigned' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: audit_evidence.finding_id no es bigint unsigned.';
    END IF;

    -- 1.5. Validación de la clave foránea histórica audit_evidence.finding_id -> findings.id
    SET v_count = 0;
    SELECT COUNT(*) INTO v_count
    FROM information_schema.KEY_COLUMN_USAGE k
    JOIN information_schema.REFERENTIAL_CONSTRAINTS r
      ON k.CONSTRAINT_SCHEMA = r.CONSTRAINT_SCHEMA AND k.CONSTRAINT_NAME = r.CONSTRAINT_NAME
    WHERE k.CONSTRAINT_SCHEMA = v_schema
      AND k.TABLE_NAME = 'audit_evidence'
      AND k.COLUMN_NAME = 'finding_id'
      AND k.REFERENCED_TABLE_NAME = 'findings'
      AND k.REFERENCED_COLUMN_NAME = 'id';

    IF v_count = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: No se detecto la clave foranea historica de audit_evidence hacia findings(id).';
    END IF;

    -- 1.6. Umbrales volumétricos mínimos
    SELECT COUNT(*) INTO v_count FROM `findings`;
    IF v_count < 14 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: findings contiene menos de 14 registros historicos.';
    END IF;

    SELECT COUNT(*) INTO v_count FROM `audit_evidence`;
    IF v_count < 14 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: audit_evidence contiene menos de 14 registros historicos.';
    END IF;

    -- =========================================================================
    -- FASE 2: COMPROBACIÓN DE ESTADO INICIAL CONOCIDO (AUSENCIA DE NUEVOS OBJETOS)
    -- =========================================================================

    -- 2.1. Comprobar que las 5 tablas nuevas NO existan
    SET v_count = 0;
    SELECT COUNT(*) INTO v_count
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = v_schema
      AND TABLE_NAME IN ('access_profiles', 'profile_expected_groups', 
                         'profile_expected_trust_principals', 
                         'resource_access_profiles', 'audit_results');

    IF v_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: Se detectaron tablas nuevas preexistentes en el esquema.';
    END IF;

    -- 2.2. Comprobar que las nuevas columnas NO existan
    SET v_count = 0;
    SELECT COUNT(*) INTO v_count
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = v_schema
      AND ((TABLE_NAME = 'findings' AND COLUMN_NAME = 'audit_result_id')
        OR (TABLE_NAME = 'audit_evidence' AND COLUMN_NAME = 'audit_result_id'));

    IF v_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: Se detecto la columna audit_result_id preexistente en findings o audit_evidence.';
    END IF;

    -- 2.3. Comprobar que las nuevas restricciones NO existan
    SET v_count = 0;
    SELECT COUNT(*) INTO v_count
    FROM information_schema.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_SCHEMA = v_schema
      AND CONSTRAINT_NAME IN ('fk_findings_audit_result', 'fk_evidence_audit_result', 'chk_evidence_target');

    IF v_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: Se detectaron restricciones de Fase 2 preexistentes en el esquema.';
    END IF;

    -- 2.4. Comprobación previa de nombres de índices a agregar en tablas históricas
    SET v_count = 0;
    SELECT COUNT(*) INTO v_count
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = v_schema
      AND ((TABLE_NAME = 'findings' AND INDEX_NAME = 'idx_findings_audit_result_id')
        OR (TABLE_NAME = 'audit_evidence' AND INDEX_NAME = 'idx_evidence_audit_result_id'));

    IF v_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ABORTADO: Se detectaron nombres de indices de Fase 2 preexistentes en findings o audit_evidence.';
    END IF;

    -- =========================================================================
    -- FASE 3: CREACIÓN CONTROLADA DE LAS CINCO TABLAS NUEVAS
    -- =========================================================================

    -- 3.1. Tabla `access_profiles`
    CREATE TABLE `access_profiles` (
        `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        `profile_code` VARCHAR(50) NOT NULL,
        `profile_name` VARCHAR(150) NOT NULL,
        `identity_type` VARCHAR(20) NOT NULL,
        `version` VARCHAR(20) NOT NULL DEFAULT '1.0',
        `description` TEXT NULL,
        `status` VARCHAR(20) NOT NULL DEFAULT 'active',
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT `pk_access_profiles` PRIMARY KEY (`id`),
        CONSTRAINT `uk_access_profiles_code` UNIQUE (`profile_code`),
        CONSTRAINT `chk_access_profiles_identity_type` CHECK (`identity_type` IN ('user', 'role')),
        CONSTRAINT `chk_access_profiles_status` CHECK (`status` IN ('active', 'inactive', 'deprecated')),
        INDEX `idx_access_profiles_type_status` (`identity_type`, `status`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    -- 3.2. Tabla `profile_expected_groups` (Solo para perfiles 'user')
    CREATE TABLE `profile_expected_groups` (
        `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        `profile_id` BIGINT UNSIGNED NOT NULL,
        `group_name` VARCHAR(128) NOT NULL,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT `pk_profile_expected_groups` PRIMARY KEY (`id`),
        CONSTRAINT `fk_peg_profile` FOREIGN KEY (`profile_id`)
            REFERENCES `access_profiles` (`id`)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        CONSTRAINT `uk_profile_expected_group` UNIQUE (`profile_id`, `group_name`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    -- 3.3. Tabla `profile_expected_trust_principals` (Solo para perfiles 'role')
    CREATE TABLE `profile_expected_trust_principals` (
        `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        `profile_id` BIGINT UNSIGNED NOT NULL,
        `principal_type` VARCHAR(50) NOT NULL,
        `principal_identifier` VARCHAR(255) NOT NULL,
        `trust_action` VARCHAR(100) NOT NULL DEFAULT 'sts:AssumeRole',
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT `pk_profile_expected_trust_principals` PRIMARY KEY (`id`),
        CONSTRAINT `fk_petp_profile` FOREIGN KEY (`profile_id`)
            REFERENCES `access_profiles` (`id`)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        CONSTRAINT `uk_profile_principal_action` UNIQUE (`profile_id`, `principal_type`, `principal_identifier`, `trust_action`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    -- 3.4. Tabla `resource_access_profiles` (Historial y perfil activo único)
    CREATE TABLE `resource_access_profiles` (
        `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        `resource_id` BIGINT UNSIGNED NOT NULL,
        `profile_id` BIGINT UNSIGNED NOT NULL,
        `valid_from` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `valid_to` DATETIME NULL,
        `is_active_flag` TINYINT GENERATED ALWAYS AS (IF(`valid_to` IS NULL, 1, NULL)) VIRTUAL,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT `pk_resource_access_profiles` PRIMARY KEY (`id`),
        CONSTRAINT `fk_rap_resource` FOREIGN KEY (`resource_id`)
            REFERENCES `resources` (`id`)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        CONSTRAINT `fk_rap_profile` FOREIGN KEY (`profile_id`)
            REFERENCES `access_profiles` (`id`)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        CONSTRAINT `uk_resource_single_active_profile` UNIQUE (`resource_id`, `is_active_flag`),
        INDEX `idx_rap_profile_id` (`profile_id`),
        INDEX `idx_rap_validity` (`valid_from`, `valid_to`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    -- 3.5. Tabla `audit_results` (Resultados exhaustivos: Conforme, Hallazgo, No evaluable)
    CREATE TABLE `audit_results` (
        `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        `audit_run_id` BIGINT UNSIGNED NOT NULL,
        `resource_id` BIGINT UNSIGNED NOT NULL,
        `audit_rule_id` BIGINT UNSIGNED NOT NULL,
        `criterion_code` VARCHAR(50) NOT NULL,
        `result_status` VARCHAR(20) NOT NULL,
        `justification` TEXT NOT NULL,
        `profile_id` BIGINT UNSIGNED NULL,
        `details` JSON NULL,
        `evaluated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT `pk_audit_results` PRIMARY KEY (`id`),
        CONSTRAINT `fk_ar_run` FOREIGN KEY (`audit_run_id`)
            REFERENCES `audit_runs` (`id`)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        CONSTRAINT `fk_ar_resource` FOREIGN KEY (`resource_id`)
            REFERENCES `resources` (`id`)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        CONSTRAINT `fk_ar_rule` FOREIGN KEY (`audit_rule_id`)
            REFERENCES `audit_rules` (`id`)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        CONSTRAINT `fk_ar_profile` FOREIGN KEY (`profile_id`)
            REFERENCES `access_profiles` (`id`)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        CONSTRAINT `chk_ar_status` CHECK (`result_status` IN ('Conforme', 'Hallazgo', 'No evaluable')),
        CONSTRAINT `uk_audit_result_criterion` UNIQUE (`audit_run_id`, `resource_id`, `audit_rule_id`, `criterion_code`),
        INDEX `idx_ar_run_status` (`audit_run_id`, `result_status`),
        INDEX `idx_ar_resource_id` (`resource_id`),
        INDEX `idx_ar_rule_id` (`audit_rule_id`),
        INDEX `idx_ar_profile_id` (`profile_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    -- =========================================================================
    -- FASE 4: ADAPTACIÓN DE TABLAS HISTÓRICAS
    -- =========================================================================

    -- 4.1. Adaptación de `findings`
    ALTER TABLE `findings`
        ADD COLUMN `audit_result_id` BIGINT UNSIGNED NULL AFTER `audit_rule_id`,
        ADD CONSTRAINT `fk_findings_audit_result` FOREIGN KEY (`audit_result_id`)
            REFERENCES `audit_results` (`id`)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        ADD INDEX `idx_findings_audit_result_id` (`audit_result_id`);

    -- 4.2. Adaptación de `audit_evidence`
    SET v_is_null = '';
    SELECT IS_NULLABLE INTO v_is_null
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = v_schema AND TABLE_NAME = 'audit_evidence' AND COLUMN_NAME = 'finding_id';

    IF v_is_null = 'NO' THEN
        ALTER TABLE `audit_evidence` MODIFY COLUMN `finding_id` BIGINT UNSIGNED NULL;
    END IF;

    ALTER TABLE `audit_evidence`
        ADD COLUMN `audit_result_id` BIGINT UNSIGNED NULL AFTER `finding_id`,
        ADD CONSTRAINT `fk_evidence_audit_result` FOREIGN KEY (`audit_result_id`)
            REFERENCES `audit_results` (`id`)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        ADD INDEX `idx_evidence_audit_result_id` (`audit_result_id`),
        ADD CONSTRAINT `chk_evidence_target` CHECK (
            (`finding_id` IS NOT NULL AND `audit_result_id` IS NULL) OR
            (`finding_id` IS NULL AND `audit_result_id` IS NOT NULL)
        );

END sp_block //

DELIMITER ;


-- -----------------------------------------------------------------------------
-- PROTOCOLO DE EJECUCIÓN FUTURA Y LIMPIEZA
-- NOTA OPERATIVA:
--   1. Este script define el procedimiento sp_migrar_esquema_fase2.
--   2. Requiere privilegio CREATE ROUTINE para su compilación.
--   3. Cuando sea formalmente autorizado, se ejecuta mediante:
--        CALL `sp_migrar_esquema_fase2`();
--      (Requiere privilegio EXECUTE).
--   4. Se ejecutan las consultas de validación de integridad histórica.
--   5. Tras validar el éxito, se ejecuta la limpieza manual:
--        DROP PROCEDURE IF EXISTS `sp_migrar_esquema_fase2`;
--      (Requiere privilegio ALTER ROUTINE).
-- =============================================================================
