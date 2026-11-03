-- =============================================================================
-- PROYECTO: Modelo automatizado para la auditoría de gestión de identidades y
--           accesos en entornos de nube basado en el estándar ISO 27001
--           para UPHARVEN C.A.
-- ARCHIVO: init_database_upharven.sql
-- DESCRIPCIÓN: Script SQL consolidado para la inicialización y despliegue del
--              esquema relacional completo (10 tablas) y datos de catálogo base.
-- MOTOR: MySQL Server 8.0 / 9.6 (InnoDB, utf8mb4, utf8mb4_unicode_ci)
-- NOTA: Este script reúne la estructura final verificada en el código fuente.
--       NO debe ejecutarse automáticamente sin autorización del administrador.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `auditoria_iam_upharven`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `auditoria_iam_upharven`;

SET FOREIGN_KEY_CHECKS = 0;

-- =============================================================================
-- 1. TABLA: audit_runs (Maestro de Ejecuciones de Auditoría)
-- =============================================================================
DROP TABLE IF EXISTS `audit_runs`;
CREATE TABLE `audit_runs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `execution_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `source_type` VARCHAR(30) COLLATE utf8mb4_unicode_ci NOT NULL,
    `status` VARCHAR(30) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'iniciada',
    `total_findings` INT UNSIGNED NOT NULL DEFAULT 0,
    `summary` TEXT COLLATE utf8mb4_unicode_ci NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 2. TABLA: resources (Catálogo de Identidades y Recursos Auditados)
-- =============================================================================
DROP TABLE IF EXISTS `resources`;
CREATE TABLE `resources` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `resource_key` VARCHAR(150) COLLATE utf8mb4_unicode_ci NOT NULL,
    `resource_type` VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL,
    `display_name` VARCHAR(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `source_type` VARCHAR(30) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'simulacion',
    `resource_status` VARCHAR(30) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'activo',
    `attributes` JSON DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_resource_key_source` (`resource_key`, `source_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 3. TABLA: audit_rules (Catálogo de Reglas Técnicas y Controles ISO 27001)
-- =============================================================================
DROP TABLE IF EXISTS `audit_rules`;
CREATE TABLE `audit_rules` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `rule_code` VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL,
    `rule_name` VARCHAR(150) COLLATE utf8mb4_unicode_ci NOT NULL,
    `description` TEXT COLLATE utf8mb4_unicode_ci NOT NULL,
    `iso_control` VARCHAR(20) COLLATE utf8mb4_unicode_ci NOT NULL,
    `default_severity` VARCHAR(20) COLLATE utf8mb4_unicode_ci NOT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `rule_code` (`rule_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 4. TABLA: access_profiles (Perfiles de Acceso Formales de Referencia)
-- =============================================================================
DROP TABLE IF EXISTS `access_profiles`;
CREATE TABLE `access_profiles` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `profile_code` VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL,
    `profile_name` VARCHAR(150) COLLATE utf8mb4_unicode_ci NOT NULL,
    `identity_type` VARCHAR(20) COLLATE utf8mb4_unicode_ci NOT NULL,
    `version` VARCHAR(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '1.0',
    `description` TEXT COLLATE utf8mb4_unicode_ci NULL,
    `status` VARCHAR(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_access_profiles_code` (`profile_code`),
    CONSTRAINT `chk_access_profiles_identity_type` CHECK (`identity_type` IN ('user', 'role')),
    CONSTRAINT `chk_access_profiles_status` CHECK (`status` IN ('active', 'inactive', 'deprecated')),
    INDEX `idx_access_profiles_type_status` (`identity_type`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 5. TABLA: profile_expected_groups (Grupos Autorizados para Perfiles de Usuario)
-- =============================================================================
DROP TABLE IF EXISTS `profile_expected_groups`;
CREATE TABLE `profile_expected_groups` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `profile_id` BIGINT UNSIGNED NOT NULL,
    `group_name` VARCHAR(128) COLLATE utf8mb4_unicode_ci NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_peg_profile` FOREIGN KEY (`profile_id`)
        REFERENCES `access_profiles` (`id`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY `uk_profile_expected_group` (`profile_id`, `group_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 6. TABLA: profile_expected_trust_principals (Entidades de Confianza para Roles)
-- =============================================================================
DROP TABLE IF EXISTS `profile_expected_trust_principals`;
CREATE TABLE `profile_expected_trust_principals` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `profile_id` BIGINT UNSIGNED NOT NULL,
    `principal_type` VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL,
    `principal_identifier` VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL,
    `trust_action` VARCHAR(100) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'sts:AssumeRole',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_petp_profile` FOREIGN KEY (`profile_id`)
        REFERENCES `access_profiles` (`id`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY `uk_profile_principal_action` (`profile_id`, `principal_type`, `principal_identifier`, `trust_action`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 7. TABLA: resource_access_profiles (Asignación y Vigencia de Perfiles)
-- =============================================================================
DROP TABLE IF EXISTS `resource_access_profiles`;
CREATE TABLE `resource_access_profiles` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `resource_id` BIGINT UNSIGNED NOT NULL,
    `profile_id` BIGINT UNSIGNED NOT NULL,
    `valid_from` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `valid_to` DATETIME NULL,
    `is_active_flag` TINYINT GENERATED ALWAYS AS (IF(`valid_to` IS NULL, 1, NULL)) VIRTUAL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_rap_resource` FOREIGN KEY (`resource_id`)
        REFERENCES `resources` (`id`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_rap_profile` FOREIGN KEY (`profile_id`)
        REFERENCES `access_profiles` (`id`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY `uk_resource_single_active_profile` (`resource_id`, `is_active_flag`),
    INDEX `idx_rap_profile_id` (`profile_id`),
    INDEX `idx_rap_validity` (`valid_from`, `valid_to`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 8. TABLA: audit_results (Resultados Exhaustivos por Criterio de Auditoría)
-- =============================================================================
DROP TABLE IF EXISTS `audit_results`;
CREATE TABLE `audit_results` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `audit_run_id` BIGINT UNSIGNED NOT NULL,
    `resource_id` BIGINT UNSIGNED NOT NULL,
    `audit_rule_id` BIGINT UNSIGNED NOT NULL,
    `criterion_code` VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL,
    `result_status` VARCHAR(20) COLLATE utf8mb4_unicode_ci NOT NULL,
    `justification` TEXT COLLATE utf8mb4_unicode_ci NOT NULL,
    `profile_id` BIGINT UNSIGNED NULL,
    `details` JSON NULL,
    `evaluated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
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
    UNIQUE KEY `uk_audit_result_criterion` (`audit_run_id`, `resource_id`, `audit_rule_id`, `criterion_code`),
    INDEX `idx_ar_run_status` (`audit_run_id`, `result_status`),
    INDEX `idx_ar_resource_id` (`resource_id`),
    INDEX `idx_ar_rule_id` (`audit_rule_id`),
    INDEX `idx_ar_profile_id` (`profile_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 9. TABLA: findings (Hallazgos Formales de Incumplimiento de Seguridad)
-- =============================================================================
DROP TABLE IF EXISTS `findings`;
CREATE TABLE `findings` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `audit_run_id` BIGINT UNSIGNED NOT NULL,
    `resource_id` BIGINT UNSIGNED NOT NULL,
    `audit_rule_id` BIGINT UNSIGNED NOT NULL,
    `audit_result_id` BIGINT UNSIGNED NULL,
    `result_status` VARCHAR(30) COLLATE utf8mb4_unicode_ci NOT NULL,
    `severity` VARCHAR(20) COLLATE utf8mb4_unicode_ci NOT NULL,
    `finding_title` VARCHAR(200) COLLATE utf8mb4_unicode_ci NOT NULL,
    `description` TEXT COLLATE utf8mb4_unicode_ci NOT NULL,
    `recommendation` TEXT COLLATE utf8mb4_unicode_ci NULL,
    `observed_value` TEXT COLLATE utf8mb4_unicode_ci NULL,
    `detected_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_findings_run` FOREIGN KEY (`audit_run_id`)
        REFERENCES `audit_runs` (`id`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_findings_resource` FOREIGN KEY (`resource_id`)
        REFERENCES `resources` (`id`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_findings_rule` FOREIGN KEY (`audit_rule_id`)
        REFERENCES `audit_rules` (`id`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_findings_audit_result` FOREIGN KEY (`audit_result_id`)
        REFERENCES `audit_results` (`id`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX `idx_findings_run` (`audit_run_id`),
    INDEX `idx_findings_resource` (`resource_id`),
    INDEX `idx_findings_rule` (`audit_rule_id`),
    INDEX `idx_findings_audit_result_id` (`audit_result_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 10. TABLA: audit_evidence (Evidencias Técnicas de Soporte a Hallazgos)
-- =============================================================================
DROP TABLE IF EXISTS `audit_evidence`;
CREATE TABLE `audit_evidence` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `finding_id` BIGINT UNSIGNED NULL,
    `audit_result_id` BIGINT UNSIGNED NULL,
    `evidence_type` VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL,
    `evidence_detail` TEXT COLLATE utf8mb4_unicode_ci NOT NULL,
    `evidence_reference` VARCHAR(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `captured_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_evidence_finding` FOREIGN KEY (`finding_id`)
        REFERENCES `findings` (`id`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_evidence_audit_result` FOREIGN KEY (`audit_result_id`)
        REFERENCES `audit_results` (`id`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `chk_evidence_target` CHECK (
        (`finding_id` IS NOT NULL AND `audit_result_id` IS NULL) OR
        (`finding_id` IS NULL AND `audit_result_id` IS NOT NULL)
    ),
    INDEX `idx_evidence_finding` (`finding_id`),
    INDEX `idx_evidence_audit_result_id` (`audit_result_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- DATOS INICIALES DE CATÁLOGO: Reglas de Auditoría ISO/IEC 27001:2022
-- =============================================================================
INSERT INTO `audit_rules` (`id`, `rule_code`, `rule_name`, `description`, `iso_control`, `default_severity`, `is_active`, `created_at`)
VALUES
    (1, 'IAM-001', 'Control de acceso a identidades según perfil autorizado', 'Inspecciona la correspondencia de pertenencia a grupos en usuarios y relaciones de confianza en roles.', '5.15', 'alta', 1, CURRENT_TIMESTAMP),
    (2, 'IAM-002', 'Gestión del ciclo de vida y estado de actividad de identidades', 'Evalúa el estado de vigencia y la inactividad de credenciales frente al umbral operativo de 90 días.', '5.16', 'media', 1, CURRENT_TIMESTAMP),
    (3, 'IAM-003', 'Control de derechos de acceso y prevención de privilegios excesivos', 'Inspecciona políticas JSON de IAM para detectar comodines globales y privilegios administrativos excesivos.', '5.18', 'alta', 1, CURRENT_TIMESTAMP),
    (4, 'IAM-004', 'Autenticación segura y obligatoriedad de MFA en identidades', 'Comprueba la activación obligatoria de factor múltiple de autenticación (MFA) en identidades de usuario.', '8.5', 'alta', 1, CURRENT_TIMESTAMP)
ON DUPLICATE KEY UPDATE
    `rule_name` = VALUES(`rule_name`),
    `description` = VALUES(`description`),
    `iso_control` = VALUES(`iso_control`),
    `default_severity` = VALUES(`default_severity`),
    `is_active` = VALUES(`is_active`);

-- Fin del script de inicialización

