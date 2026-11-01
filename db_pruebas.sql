-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: auditoria_iam_upharven
-- ------------------------------------------------------
-- Server version	9.6.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '255ec6f7-3471-11f1-8f03-54bf646cd2da:1-2330';

--
-- Table structure for table `audit_evidence`
--

DROP TABLE IF EXISTS `audit_evidence`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_evidence` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `finding_id` bigint unsigned NOT NULL,
  `evidence_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `evidence_detail` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `evidence_reference` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `captured_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_evidence_finding` (`finding_id`),
  CONSTRAINT `fk_evidence_finding` FOREIGN KEY (`finding_id`) REFERENCES `findings` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_evidence`
--

LOCK TABLES `audit_evidence` WRITE;
/*!40000 ALTER TABLE `audit_evidence` DISABLE KEYS */;
INSERT INTO `audit_evidence` VALUES (1,1,'matriz_permisos','No se encontró definición de alcance o lista de políticas en el perfil.','resource:ana.operaciones','2026-10-28 22:42:51'),(2,2,'atributos_identidad','Cuenta carlos.admin marcada con privilegios administrativos.','resource:carlos.admin','2026-10-28 22:42:51'),(3,3,'matriz_permisos','No se encontró definición de alcance o lista de políticas en el perfil.','resource:carlos.admin','2026-10-28 22:42:51'),(4,4,'auditoria_actividad','Última inactividad constatada: status=\'inactivo\', días_inactivo=120 (umbral=90).','resource:usuario.inactivo','2026-10-28 22:42:51'),(5,5,'matriz_permisos','No se encontró definición de alcance o lista de políticas en el perfil.','resource:usuario.inactivo','2026-10-28 22:42:51'),(6,6,'matriz_permisos','No se encontró definición de alcance o lista de políticas en el perfil.','resource:cuenta.sin_mfa','2026-10-28 22:42:51'),(7,7,'configuracion_mfa','Identidad cuenta.sin_mfa sin factor múltiple de autenticación activo.','resource:cuenta.sin_mfa','2026-10-28 22:42:51'),(8,8,'matriz_permisos','No se encontró definición de alcance o lista de políticas en el perfil.','resource:ana.operaciones','2026-10-28 22:44:15'),(9,9,'atributos_identidad','Cuenta carlos.admin marcada con privilegios administrativos.','resource:carlos.admin','2026-10-28 22:44:15'),(10,10,'matriz_permisos','No se encontró definición de alcance o lista de políticas en el perfil.','resource:carlos.admin','2026-10-28 22:44:15'),(11,11,'auditoria_actividad','Última inactividad constatada: status=\'inactivo\', días_inactivo=120 (umbral=90).','resource:usuario.inactivo','2026-10-28 22:44:15'),(12,12,'matriz_permisos','No se encontró definición de alcance o lista de políticas en el perfil.','resource:usuario.inactivo','2026-10-28 22:44:15'),(13,13,'matriz_permisos','No se encontró definición de alcance o lista de políticas en el perfil.','resource:cuenta.sin_mfa','2026-10-28 22:44:15'),(14,14,'configuracion_mfa','Identidad cuenta.sin_mfa sin factor múltiple de autenticación activo.','resource:cuenta.sin_mfa','2026-10-28 22:44:15');
/*!40000 ALTER TABLE `audit_evidence` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audit_rules`
--

DROP TABLE IF EXISTS `audit_rules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_rules` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `rule_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rule_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `iso_control` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `default_severity` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `rule_code` (`rule_code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_rules`
--

LOCK TABLES `audit_rules` WRITE;
/*!40000 ALTER TABLE `audit_rules` DISABLE KEYS */;
INSERT INTO `audit_rules` VALUES (1,'IAM-001','Revisión de privilegios elevados','Identifica identidades con permisos administrativos amplios que requieren revisión.','5.15','alta',1,'2026-10-28 20:43:21'),(2,'IAM-002','Revisión de identidades inactivas','Identifica cuentas que no registran actividad reciente y requieren revisión.','5.16','media',1,'2026-10-28 20:43:21'),(3,'IAM-003','Revisión de derechos de acceso','Identifica permisos asignados que podrían exceder las necesidades del usuario.','5.18','alta',1,'2026-10-28 20:43:21'),(4,'IAM-004','Revisión de autenticación segura','Comprueba los atributos de autenticación disponibles para determinar si requieren revisión.','8.5','alta',1,'2026-10-28 20:43:21');
/*!40000 ALTER TABLE `audit_rules` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audit_runs`
--

DROP TABLE IF EXISTS `audit_runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_runs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `execution_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `source_type` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'iniciada',
  `total_findings` int unsigned NOT NULL DEFAULT '0',
  `summary` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_runs`
--

LOCK TABLES `audit_runs` WRITE;
/*!40000 ALTER TABLE `audit_runs` DISABLE KEYS */;
INSERT INTO `audit_runs` VALUES (3,'2026-10-28 22:42:51','simulacion','COMPLETED',7,'Auditoría concluida con éxito. Recursos evaluados: 4. Hallazgos detectados: 7 (FAIL: 1, WARNING: 2, INDETERMINATE: 4, PASS: 9).','2026-10-28 22:42:51'),(4,'2026-10-28 22:44:15','simulacion','COMPLETED',7,'Auditoría concluida con éxito. Recursos evaluados: 4. Hallazgos detectados: 7 (FAIL: 1, WARNING: 2, INDETERMINATE: 4, PASS: 9).','2026-10-28 22:44:15');
/*!40000 ALTER TABLE `audit_runs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `findings`
--

DROP TABLE IF EXISTS `findings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `findings` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `audit_run_id` bigint unsigned NOT NULL,
  `resource_id` bigint unsigned NOT NULL,
  `audit_rule_id` bigint unsigned NOT NULL,
  `result_status` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `severity` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `finding_title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `recommendation` text COLLATE utf8mb4_unicode_ci,
  `observed_value` text COLLATE utf8mb4_unicode_ci,
  `detected_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_findings_run` (`audit_run_id`),
  KEY `idx_findings_resource` (`resource_id`),
  KEY `idx_findings_rule` (`audit_rule_id`),
  CONSTRAINT `fk_findings_resource` FOREIGN KEY (`resource_id`) REFERENCES `resources` (`id`),
  CONSTRAINT `fk_findings_rule` FOREIGN KEY (`audit_rule_id`) REFERENCES `audit_rules` (`id`),
  CONSTRAINT `fk_findings_run` FOREIGN KEY (`audit_run_id`) REFERENCES `audit_runs` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `findings`
--

LOCK TABLES `findings` WRITE;
/*!40000 ALTER TABLE `findings` DISABLE KEYS */;
INSERT INTO `findings` VALUES (1,3,1,3,'INDETERMINATE','INFORMATIVA','Sin datos suficientes sobre el alcance de permisos','La identidad \'Ana - Operaciones\' no define la granularidad o alcance de permisos asignados.','Documentar la matriz de roles y permisos asociados al recurso.','permission_scope=None','2026-10-28 22:42:51'),(2,3,2,1,'WARNING','ALTA','Identidad con privilegios administrativos amplios requiere revisión periódica','La identidad \'Carlos - Administrador\' posee privilegios elevados asignados. Conforme al control 5.15 de ISO/IEC 27001:2022, la asignación de derechos de acceso privilegiado debe restringirse y reevaluarse con periodicidad formal.','Validar la justificación de negocio para el rol administrativo, constatar la vigencia del requerimiento y asegurar que se aplique el principio de menor privilegio.','admin_privileges=True','2026-10-28 22:42:51'),(3,3,2,3,'INDETERMINATE','INFORMATIVA','Sin datos suficientes sobre el alcance de permisos','La identidad \'Carlos - Administrador\' no define la granularidad o alcance de permisos asignados.','Documentar la matriz de roles y permisos asociados al recurso.','permission_scope=None','2026-10-28 22:42:51'),(4,3,3,2,'WARNING','MEDIA','Identidad inactiva o sin uso reciente requiere revisión de ciclo de vida','La identidad \'Usuario Inactivo\' se encuentra inactiva o supera los 90 días sin actividad registrada (status=\'inactivo\', días_inactivo=120 (umbral=90)). El control 5.16 de ISO/IEC 27001:2022 requiere gestionar el ciclo de vida completo de las identidades, suspendiendo o revocando accesos obsoletos.','Verificar con talento humano o el líder de área si el titular aún pertenece a la organización. De no requerir el acceso, proceder a deshabilitar preventivamente la cuenta.','status=\'inactivo\', días_inactivo=120 (umbral=90)','2026-10-28 22:42:51'),(5,3,3,3,'INDETERMINATE','INFORMATIVA','Sin datos suficientes sobre el alcance de permisos','La identidad \'Usuario Inactivo\' no define la granularidad o alcance de permisos asignados.','Documentar la matriz de roles y permisos asociados al recurso.','permission_scope=None','2026-10-28 22:42:51'),(6,3,4,3,'INDETERMINATE','INFORMATIVA','Sin datos suficientes sobre el alcance de permisos','La identidad \'Cuenta sin MFA\' no define la granularidad o alcance de permisos asignados.','Documentar la matriz de roles y permisos asociados al recurso.','permission_scope=None','2026-10-28 22:42:51'),(7,3,4,4,'FAIL','ALTA','Ausencia de autenticación de factor múltiple (MFA)','La identidad \'Cuenta sin MFA\' tiene la autenticación multifactor desactivada (mfa_enabled=False). El control 8.5 de ISO/IEC 27001:2022 estipula que los sistemas deben implementar mecanismos de autenticación segura y autenticación multifactor para proteger accesos críticos en la nube.','Exigir el enrolamiento mandatorio de MFA (aplicación TOTP o llave física FIDO2/WebAuthn) antes de permitir futuros accesos a la plataforma.','mfa_enabled=False','2026-10-28 22:42:51'),(8,4,1,3,'INDETERMINATE','INFORMATIVA','Sin datos suficientes sobre el alcance de permisos','La identidad \'Ana - Operaciones\' no define la granularidad o alcance de permisos asignados.','Documentar la matriz de roles y permisos asociados al recurso.','permission_scope=None','2026-10-28 22:44:15'),(9,4,2,1,'WARNING','ALTA','Identidad con privilegios administrativos amplios requiere revisión periódica','La identidad \'Carlos - Administrador\' posee privilegios elevados asignados. Conforme al control 5.15 de ISO/IEC 27001:2022, la asignación de derechos de acceso privilegiado debe restringirse y reevaluarse con periodicidad formal.','Validar la justificación de negocio para el rol administrativo, constatar la vigencia del requerimiento y asegurar que se aplique el principio de menor privilegio.','admin_privileges=True','2026-10-28 22:44:15'),(10,4,2,3,'INDETERMINATE','INFORMATIVA','Sin datos suficientes sobre el alcance de permisos','La identidad \'Carlos - Administrador\' no define la granularidad o alcance de permisos asignados.','Documentar la matriz de roles y permisos asociados al recurso.','permission_scope=None','2026-10-28 22:44:15'),(11,4,3,2,'WARNING','MEDIA','Identidad inactiva o sin uso reciente requiere revisión de ciclo de vida','La identidad \'Usuario Inactivo\' se encuentra inactiva o supera los 90 días sin actividad registrada (status=\'inactivo\', días_inactivo=120 (umbral=90)). El control 5.16 de ISO/IEC 27001:2022 requiere gestionar el ciclo de vida completo de las identidades, suspendiendo o revocando accesos obsoletos.','Verificar con talento humano o el líder de área si el titular aún pertenece a la organización. De no requerir el acceso, proceder a deshabilitar preventivamente la cuenta.','status=\'inactivo\', días_inactivo=120 (umbral=90)','2026-10-28 22:44:15'),(12,4,3,3,'INDETERMINATE','INFORMATIVA','Sin datos suficientes sobre el alcance de permisos','La identidad \'Usuario Inactivo\' no define la granularidad o alcance de permisos asignados.','Documentar la matriz de roles y permisos asociados al recurso.','permission_scope=None','2026-10-28 22:44:15'),(13,4,4,3,'INDETERMINATE','INFORMATIVA','Sin datos suficientes sobre el alcance de permisos','La identidad \'Cuenta sin MFA\' no define la granularidad o alcance de permisos asignados.','Documentar la matriz de roles y permisos asociados al recurso.','permission_scope=None','2026-10-28 22:44:15'),(14,4,4,4,'FAIL','ALTA','Ausencia de autenticación de factor múltiple (MFA)','La identidad \'Cuenta sin MFA\' tiene la autenticación multifactor desactivada (mfa_enabled=False). El control 8.5 de ISO/IEC 27001:2022 estipula que los sistemas deben implementar mecanismos de autenticación segura y autenticación multifactor para proteger accesos críticos en la nube.','Exigir el enrolamiento mandatorio de MFA (aplicación TOTP o llave física FIDO2/WebAuthn) antes de permitir futuros accesos a la plataforma.','mfa_enabled=False','2026-10-28 22:44:15');
/*!40000 ALTER TABLE `findings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `resources`
--

DROP TABLE IF EXISTS `resources`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `resources` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `resource_key` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `resource_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `display_name` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `source_type` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'simulacion',
  `resource_status` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'activo',
  `attributes` json DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_resource_key_source` (`resource_key`,`source_type`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `resources`
--

LOCK TABLES `resources` WRITE;
/*!40000 ALTER TABLE `resources` DISABLE KEYS */;
INSERT INTO `resources` VALUES (1,'ana.operaciones','iam_user','Ana - Operaciones','simulacion','activo','{\"role\": \"operaciones\", \"mfa_enabled\": true, \"admin_privileges\": false, \"permissions_scope\": \"limitado\", \"last_activity_days\": 2}','2026-10-28 20:48:48','2026-10-28 20:48:48'),(2,'carlos.admin','iam_user','Carlos - Administrador','simulacion','activo','{\"role\": \"administrador\", \"mfa_enabled\": true, \"admin_privileges\": true, \"permissions_scope\": \"amplio\", \"last_activity_days\": 1}','2026-10-28 20:48:48','2026-10-28 20:48:48'),(3,'usuario.inactivo','iam_user','Usuario Inactivo','simulacion','inactivo','{\"role\": \"operaciones\", \"mfa_enabled\": true, \"admin_privileges\": false, \"permissions_scope\": \"limitado\", \"last_activity_days\": 120}','2026-10-28 20:48:48','2026-10-28 20:48:48'),(4,'cuenta.sin_mfa','iam_user','Cuenta sin MFA','simulacion','activo','{\"role\": \"operaciones\", \"mfa_enabled\": false, \"admin_privileges\": false, \"permissions_scope\": \"limitado\", \"last_activity_days\": 5}','2026-10-28 20:48:48','2026-10-28 20:48:48');
/*!40000 ALTER TABLE `resources` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-31  1:30:02
