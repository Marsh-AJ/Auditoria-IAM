# DOCUMENTACIÓN TÉCNICA — FASE 1
## DIAGNÓSTICO Y ESTABILIZACIÓN DEL PROYECTO

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO/IEC 27001 para UPHARVEN C.A.  
**Fase:** Fase 1 — Diagnóstico y estabilización del proyecto  
**Versión del documento:** 1.0  
**Fecha:** 31 de octubre de 2026  
**Autor:** Antigravity (Arquitecto de Software y Auditor Técnico de Código)  

---

## 1. Identificación de la fase

### 1.1. Nombre de la fase
**Fase 1: Diagnóstico y estabilización del proyecto.**

### 1.2. Objetivo general
Realizar un diagnóstico técnico exhaustivo, empírico y no destructivo del estado real del repositorio del proyecto existente, evaluando su estructura física de archivos, dependencias, entorno de ejecución, persistencia en base de datos, lógica algorítmica, suite de pruebas y cumplimiento de restricciones de seguridad y alcance, con el fin de definir la línea base técnica necesaria para las fases posteriores de desarrollo.

### 1.3. Alcance de la fase
- Inspección estática del árbol de directorios y contenido de archivos de configuración, código fuente y metadatos.
- Identificación de dependencias instaladas y faltantes en el entorno virtual (`.venv`).
- Evaluación de los módulos existentes de conexión y repositorio de base de datos MySQL.
- Constatación del estado real de implementación de las cuatro reglas de auditoría vinculadas a ISO/IEC 27001:2022 (IAM-001, IAM-002, IAM-003, IAM-004) y del motor algorítmico.
- Revisión de la suite de pruebas automatizadas y scripts de verificación.
- Análisis de cumplimiento preliminar de las nueve restricciones obligatorias de seguridad y alcance.
- **Exclusiones de la fase:** No se realizaron modificaciones en archivos de código, no se alteró la base de datos, no se ejecutaron operaciones destructivas o de escritura, no se instalaron paquetes y no se realizó ninguna conexión con proveedores de nube externos (AWS).

### 1.4. Actividades realizadas
1. Mapeo recursivo del sistema de archivos del espacio de trabajo `C:\Users\andre\Desktop\TESIS\sistema`.
2. Inspección del archivo de entorno virtual `pyvenv.cfg` y verificación de la versión del intérprete de Python.
3. Auditoría de paquetes instalados en el entorno mediante consulta a `pip list`.
4. Análisis del estado y contenido del archivo de requerimientos (`requirements.txt`) y de configuración de exclusiones (`.gitignore`).
5. Inspección de los módulos de base de datos: `src/auditoria_iam/database/connection.py` y `src/auditoria_iam/database/repository.py`.
6. Inspección de scripts de prueba en la raíz: `test_connection.py` y `test_resources.py`.
7. Ejecución de la herramienta `pytest` para verificar la existencia y operatividad de pruebas unitarias.
8. Análisis de artefactos de compilación residuales (`.pyc`) y archivos de caché (`.pytest_cache` y `.egg-info`) para determinar el historial de desarrollo previo.
9. Verificación de seguridad de credenciales y variables de entorno (`.env`), garantizando la no divulgación de datos confidenciales.
10. Elaboración del informe de diagnóstico inicial y consolidación de la presente documentación técnica.

---

## 2. Descripción del entorno de desarrollo

El diagnóstico identificó las siguientes herramientas, versiones y configuraciones en la estación de trabajo:

### 2.1. Plataforma y componentes principales
- **Sistema Operativo:** Windows 11 Home / Pro (x86_64).
- **Entorno de Desarrollo Integrado (IDE):** Visual Studio Code (con configuración en espacio de trabajo local).
- **Intérprete Python:** Python versión **3.13.5** (64-bit), ubicado en la ruta del sistema `C:\Python313\python.exe`.
- **Entorno Virtual:** Ubicado en `C:\Users\andre\Desktop\TESIS\sistema\.venv`, configurado con `include-system-site-packages = false`.
- **Gestor de paquetes:** `pip` versión **25.1.1**.
- **Motor de Base de Datos:** MySQL Server versión **9.6** (puerto predeterminado 3306).
- **Herramienta administrativa de BD:** MySQL Workbench.

### 2.2. Estado de dependencias de software

| Paquete / Herramienta | Versión Instalada | Estado en Entorno | Propósito en el Proyecto |
| :--- | :---: | :---: | :--- |
| `auditoria-iam` | 0.1.0 | **Instalado** (Modo Editable `-e`) | Paquete raíz del proyecto desarrollado |
| `mysql-connector-python` | 26.10.0 | **Instalado** | Driver oficial de conexión entre Python y MySQL Server |
| `python-dotenv` | 1.2.4 | **Instalado** | Carga de variables de entorno seguras desde archivo `.env` |
| `pytest` | 9.2.0 | **Instalado** | Framework para la ejecución de pruebas unitarias y de integración |
| `colorama` | 0.4.6 | **Instalado** | Soporte de colores en terminal Windows |
| `iniconfig` | 2.3.1 | **Instalado** | Manejador de configuración para pytest |
| `packaging` | 26.3 | **Instalado** | Utilidades de empaquetado de software |
| `pluggy` | 1.7.0 | **Instalado** | Mecanismo de plugins de pytest |
| `Pygments` | 2.21.0 | **Instalado** | Resaltador de sintaxis |
| `boto3` | *No instalado* | **Pendiente de instalación** | SDK oficial de AWS para consultar metadatos de IAM (GET/LIST) |
| `PySide6` | *No instalado* | **Pendiente de instalación** | Framework GUI para la interfaz gráfica de escritorio basada en Qt |

### 2.3. Observaciones del entorno
- El archivo `requirements.txt` se encuentra presente en la raíz del proyecto, pero su tamaño es de **0 bytes** (vacío).
- El entorno virtual contiene las librerías esenciales para persistencia (`mysql-connector-python`) y pruebas (`pytest`), pero carece aún de las librerías necesarias para la integración futura con AWS (`boto3`) y la interfaz visual (`PySide6`).

---

## 3. Estructura actual del proyecto

### 3.1. Árbol físico de directorios y archivos

```text
C:\Users\andre\Desktop\TESIS\sistema/
│
├── .env                                       # Archivo de variables de entorno (credenciales y host DB)
├── .gitignore                                 # Reglas de exclusión de Git (.venv, .env, caches)
├── README.md                                  # Archivo de documentación general (0 bytes, vacío)
├── requirements.txt                           # Archivo de requerimientos pip (0 bytes, vacío)
├── test_connection.py                         # Script interactivo de prueba de conexión a MySQL (583 bytes)
├── test_resources.py                          # Script interactivo de consulta a la tabla resources (574 bytes)
│
├── data/                                      # Directorio destinado a archivos auxiliares de datos (vacío)
├── reports/                                   # Directorio destinado a informes generados por auditoría (vacío)
│
├── tests/
│   ├── __init__.py                            # Inicializador de paquete de pruebas (0 bytes)
│   └── __pycache__/                           # Artefactos .pyc de ejecuciones de prueba históricas
│       ├── test_audit_rules.cpython-313-pytest-9.2.0.pyc
│       ├── test_audit_rules_unittest.cpython-313.pyc
│       └── __init__.cpython-313.pyc
│
└── src/
    ├── auditoria_iam.egg-info/                # Metadatos del empaquetado editable de auditoria-iam
    │   ├── PKG-INFO
    │   ├── SOURCES.txt
    │   ├── requires.txt
    │   └── top_level.txt
    │
    └── auditoria_iam/                         # Paquete principal de la aplicación
        ├── __init__.py                        # Inicializador del paquete (0 bytes)
        ├── application/
        │   ├── __init__.py                    # Inicializador de capa de aplicación (0 bytes)
        │   └── __pycache__/                   # Bytecode residual (cli.cpython-313.pyc)
        ├── audit/
        │   ├── __init__.py                    # Inicializador del motor de auditoría (0 bytes)
        │   ├── __pycache__/                   # Bytecode residual (engine.cpython-313.pyc, models.cpython-313.pyc)
        │   └── rules/
        │       ├── __init__.py                # Inicializador del submódulo de reglas (0 bytes)
        │       └── __pycache__/               # Bytecode residual (base.cpython-313.pyc, iam_001 a iam_004 .pyc)
        ├── config/
        │   ├── __init__.py                    # Inicializador de módulo de configuración (0 bytes)
        │   └── __pycache__/                   # Bytecode residual (settings.cpython-313.pyc)
        ├── database/
        │   ├── __init__.py                    # Inicializador de módulo de persistencia (0 bytes)
        │   ├── connection.py                  # Función get_connection(user, password) (276 bytes)
        │   └── repository.py                  # Función get_resources(user, password, source_type) (755 bytes)
        ├── data_sources/
        │   ├── __init__.py                    # Inicializador del módulo de fuentes de datos (0 bytes)
        │   ├── aws/
        │   │   └── __init__.py                # Inicializador de conector AWS (0 bytes)
        │   └── simulator/
        │       └── __init__.py                # Inicializador del simulador (0 bytes)
        ├── reports/
        │   └── __init__.py                    # Inicializador de generación de reportes (0 bytes)
        └── ui/
            └── __init__.py                    # Inicializador de interfaz PySide6 (0 bytes)
```

### 3.2. Diferenciación estricta entre código fuente disponible y artefactos compilados
Un resultado crucial del diagnóstico técnico es que **no existen archivos de código fuente `.py` editables** para las reglas de auditoría (`IAM-001` a `IAM-004`), el motor (`engine.py`), los modelos de datos (`models.py`), la configuración centralizada (`settings.py`) ni la suite formal de pruebas unitarias (`test_audit_rules.py`).

Dichos módulos subsisten exclusivamente en forma de **archivos de bytecode compilado (`.pyc`)** generados en una sesión de compilación previa (28 de octubre de 2026). Por principio de integridad arquitectónica y seguridad de mantenimiento, el bytecode compilado **no es código fuente disponible**; por tanto, los módulos correspondientes deben clasificarse formalmente como **pendientes de desarrollo y materialización en código fuente** en las fases que correspondan.

---

## 4. Diagnóstico de la base de datos

### 4.1. Información general de la base de datos
- **Motor:** MySQL Server 9.6.
- **Nombre del Esquema (Database):** `auditoria_iam_upharven`.
- **Modo de conexión:** TCP/IP sobre host local `127.0.0.1`, puerto `3306`.

### 4.2. Tablas definidas en el modelo
A partir del modelo arquitectónico y las especificaciones técnicas del proyecto, el esquema está compuesto por cinco tablas relacionales:

1. **`audit_runs` (Ejecuciones de auditoría):**
   - *Propósito:* Almacenar el encabezado de cada sesión de auditoría ejecutada (fecha/hora de inicio, fecha/hora de fin, usuario ejecutor, ámbito evaluado y resumen global de resultados).
2. **`resources` (Recursos e Identidades evaluadas):**
   - *Propósito:* Registrar el inventario de identidades sujetas a auditoría (usuarios IAM, roles). Almacena clave única del recurso (`resource_key`), tipo (`resource_type`), nombre visible (`display_name`), origen (`source_type`, e.g., 'simulacion'), estado (`resource_status`) y atributos en formato serializado JSON (`attributes`).
3. **`audit_rules` (Catálogo de reglas de auditoría):**
   - *Propósito:* Catálogo maestro de reglas algorítmicas soportadas por el sistema (código `IAM-xxx`, control ISO/IEC 27001 asociado, nombre, descripción, severidad por defecto y estado activo/inactivo).
4. **`findings` (Hallazgos detectados):**
   - *Propósito:* Almacenar cada no conformidad o hallazgo técnico generado tras la evaluación de una regla contra una identidad específica, vinculando la ejecución (`audit_run_id`), el recurso (`resource_id`) y la regla (`rule_id`).
5. **`audit_evidence` (Evidencias técnicas):**
   - *Propósito:* Registro inmutable de pruebas técnicas que sustentan cada hallazgo (datos extraídos, valor observado vs. valor esperado, justificación algorítmica).

### 4.3. Registros históricos constatados
- En la tabla **`findings`** existen **14 registros históricos**.
- En la tabla **`audit_evidence`** existen **14 registros históricos**.
- **Directriz de preservación:** Ambos conjuntos de registros históricos corresponden a ejecuciones previas de auditoría y **deben conservarse íntegramente**. Queda terminantemente prohibido ejecutar sentencias `TRUNCATE`, `DROP` o `DELETE` que comprometan estos datos.

### 4.4. Recursos simulados en la base de datos
La tabla `resources` contiene cuatro identidades simuladas representativas con `source_type = 'simulacion'`:
- `ana.operaciones`: Usuario operativo activo, sin privilegios administrativos, último acceso hace 2 días, MFA habilitado.
- `carlos.admin`: Usuario administrador activo, con privilegios administrativos elevados, último acceso hace 1 día, MFA habilitado.
- `usuario.inactivo`: Cuenta inactiva, sin privilegios administrativos, último acceso registrado hace 120 días, MFA habilitado.
- `cuenta.sin_mfa`: Cuenta operativa activa, sin privilegios administrativos, último acceso hace 5 días, sin autenticación multifactor (MFA deshabilitado).

> [!IMPORTANT]
> **Aclaración sobre datos simulados:** Toda la información cargada en la tabla `resources` corresponde a un conjunto de prueba generado con propósitos académicos y de laboratorio. UPHARVEN C.A. autorizó el uso institucional de su denominación para este proyecto de titulación, pero **no proporcionó acceso a su infraestructura productiva ni divulgó información interna**. Los datos simulados no representan bajo ninguna circunstancia configuraciones o vulnerabilidades reales de UPHARVEN C.A.

### 4.5. Relaciones, restricciones y estado de verificación
- Las relaciones entre las tablas están diseñadas mediante claves foráneas (`FOREIGN KEY`) que vinculan `findings` con `audit_runs`, `resources` y `audit_rules`, así como `audit_evidence` con `findings`.
- **Estado de validación:** Debido a las políticas de aislamiento de red del entorno de ejecución sandboxed (error `WSAEACCES 10013`), la comprobación de los esquemas DDL exactos de llaves foráneas y la consulta directa de las 5 tablas quedan catalogadas como **pendientes de validación en tiempo de ejecución con conexión abierta a MySQL**.

---

## 5. Diagnóstico del código fuente

### 5.1. Módulo de conexión: `src/auditoria_iam/database/connection.py`
- **Estado:** Existente (276 bytes).
- **Contenido verificado:**
  ```python
  import mysql.connector

  def get_connection(user, password):
      connection = mysql.connector.connect(
          host="127.0.0.1",
          port=3306,
          user=user,
          password=password,
          database="auditoria_iam_upharven"
      )
      return connection
  ```
- **Evaluación técnica:**
  - *Positivo:* No contiene credenciales codificadas en duro (hardcoded).
  - *Deficiencia:* No utiliza la librería `python-dotenv` ni lee las variables del archivo `.env` existente. Fuerza a que cualquier módulo que requiera persistencia deba transportar manualmente `user` y `password` en texto claro. Carece de control de excepciones (`mysql.connector.Error`) y de configuración de tiempos de espera (`connection_timeout`).

### 5.2. Módulo de repositorio: `src/auditoria_iam/database/repository.py`
- **Estado:** Existente (755 bytes).
- **Contenido verificado:** Implementa `get_resources(user, password, source_type="simulacion")`.
- **Evaluación técnica:**
  - *Positivo:* Implementa consulta parametrizada (`WHERE source_type = %s`, pasando `(source_type,)`), protegiendo la base de datos contra inyecciones SQL.
  - *Positivo:* Garantiza la liberación de recursos de base de datos mediante un bloque formal `try ... finally` donde se invoca `cursor.close()` y `connection.close()`.
  - *Incompleto:* Únicamente implementa la lectura de recursos (`SELECT ... FROM resources`). No cuenta con métodos para consultar `audit_rules` ni para persistir registros en `audit_runs`, `findings` o `audit_evidence`.

### 5.3. Módulo de configuración: `src/auditoria_iam/config/`
- **Estado:** Incompleto / No implementado en código fuente.
- **Diagnóstico:** Solo existe el archivo `__init__.py` vacío (0 bytes). Aunque en `__pycache__` se identifica un archivo `settings.cpython-313.pyc`, no hay código fuente `.py` activo. El archivo `.env` existe en la raíz, pero ningún módulo del sistema lo está consumiendo actualmente.

### 5.4. Motor de auditoría y modelos: `src/auditoria_iam/audit/`
- **Estado:** Incompleto / No implementado en código fuente.
- **Diagnóstico:** `models.py` y `engine.py` no existen como archivos `.py`. En la arquitectura previa se proyectaron clases de datos (`Resource`, `RuleEvaluation`, `FindingRecord`, `FindingStatus`, `SeverityLevel`), pero actualmente la capa carece de archivos editables.

### 5.5. Reglas de auditoría: `src/auditoria_iam/audit/rules/`
- **Estado:** No implementadas en código fuente.
- **Diagnóstico detallado por regla:**
  - **IAM-001 (ISO/IEC 27001:2022 Control 5.15 - Access Control):** No existe archivo `.py`. Requiere evaluar privilegios elevados administrativos (`admin_privileges=True` o políticas con acciones `*` sobre recursos `*`).
  - **IAM-002 (ISO/IEC 27001:2022 Control 5.16 - Identity Management):** No existe archivo `.py`. Requiere evaluar inactividad de cuentas mediante umbrales temporales (e.g. >90 días de inactividad).
  - **IAM-003 (ISO/IEC 27001:2022 Control 5.18 - Access Rights):** No existe archivo `.py`. Requiere evaluar alcance de permisos y políticas excesivamente permisivas.
  - **IAM-004 (ISO/IEC 27001:2022 Control 8.5 - Secure Authentication):** No existe archivo `.py`. Requiere evaluar el estado del factor de autenticación multifactor (`mfa_enabled`).
  - **Clase Base (`base.py`):** No existe en código fuente `.py`.

### 5.6. Fuentes de datos: `src/auditoria_iam/data_sources/`
- **Simulador (`simulator/`):** Contiene únicamente `__init__.py` (0 bytes). No hay generador algorítmico de identidades sintéticas; la simulación reposa exclusivamente en los registros existentes de la tabla `resources`.
- **Conector AWS (`aws/`):** Contiene únicamente `__init__.py` (0 bytes). No existe implementación de Boto3.

### 5.7. Capa de presentación / Interfaz gráfica: `src/auditoria_iam/ui/`
- **Estado:** No implementada. Solo existe `__init__.py` (0 bytes). La interfaz de escritorio basada en PySide6 corresponde a fases posteriores del proyecto.

### 5.8. Pruebas automatizadas y de verificación
- **`test_connection.py` (raíz):** Script manual que solicita credenciales mediante `input()` y `getpass()`, invocando `get_connection()`. Es de solo lectura, pero no es ejecutable de forma automatizada ni desatendida.
- **`test_resources.py` (raíz):** Script manual que solicita credenciales interactivas y despliega los recursos simulados por terminal. Es de solo lectura.
- **Directorio `tests/`:** Solo contiene `__init__.py` (0 bytes). La ejecución de `pytest tests` recolecta **0 pruebas**, confirmando que no existen pruebas unitarias activas en código fuente.

---

## 6. Arquitectura identificada

### 6.1. Arquitectura modular prevista

El sistema concibe un diseño arquitectónico por capas claramente desacopladas:

```
[ Capa de Presentación (PySide6 Desktop UI) ]
                     │
[ Capa de Aplicación (Application / Coordinador de Casos de Uso) ]
                     │
┌────────────────────┴────────────────────────────────┐
│                                                     │
▼                                                     ▼
[ Motor de Auditoría (Audit Engine) ]    [ Fuentes de Datos (Data Sources) ]
  ├── Evaluador de Reglas (Rules)          ├── Simulador Local (Simulator)
  └── Modelos de Dominio (Models)          └── Conector AWS IAM (Boto3 Read-Only)
                     │
                     ▼
        [ Capa de Persistencia (Database) ]
          ├── Conexión y Pool (Connection)
          └── Repositorio CRUD (Repository)
                     │
                     ▼
           [ MySQL Server 9.6 ]
```

### 6.2. Estado real de los componentes arquitectónicos

| Componente Arquitectónico | Estado de Implementación | Observación Técnica |
| :--- | :---: | :--- |
| **Interfaz de Escritorio (UI)** | **No iniciada** | Carpeta creada, pendiente de implementación en PySide6. |
| **Lógica de Aplicación (Application)** | **No iniciada** | Carpeta creada, sin controladores ni orquestadores de caso de uso. |
| **Motor de Auditoría (Engine)** | **Pendiente de materialización** | No existe código fuente `.py`; solo compilado residual. |
| **Reglas de Auditoría (Rules)** | **Pendiente de materialización** | No existen archivos de reglas en código fuente. |
| **Fuente de Datos Simulada** | **Parcial / Indirecta** | Depende estrictamente de la tabla `resources` en MySQL. |
| **Fuente de Datos AWS** | **No iniciada** | Carpeta vacía, SDK Boto3 no instalado. |
| **Capa de Persistencia** | **Funcional Básica** | `connection.py` y `repository.py` operativos para lectura de `resources`. |
| **Configuración Centralizada** | **Pendiente de integración** | Archivo `.env` presente pero desacoplado del código. |
| **Generación de Reportes** | **No iniciada** | Carpeta vacía, reservada para fases de reportería. |

> [!NOTE]
> La presencia de la estructura de carpetas no debe interpretarse como funcionalidad desarrollada. La arquitectura modular es conceptualmente correcta y adecuada, pero requiere la restitución progresiva de sus capas de código fuente.

---

## 7. Restricciones y controles de seguridad

En concordancia con los principios rectores del proyecto, se evaluaron las nueve restricciones obligatorias de seguridad y alcance:

| N° | Restricción Obligatoria | Estado de Verificación | Justificación y Evidencia Técnica |
| :---: | :--- | :---: | :--- |
| **1** | Boto3 con operaciones exclusivas de solo lectura (GET/LIST). Prohibición de escritura, remediación o mutación en AWS. | **Sin incumplimientos detectados** *(Pendiente de validación funcional en integración)* | El directorio `src/auditoria_iam/data_sources/aws` está vacío. No hay llamadas ni importaciones de Boto3 en el código actual. |
| **2** | Exclusión del control 8.2 y funciones de superadministrador, break-glass o elevación dinámica de privilegios. | **Sin incumplimientos detectados** | No existe código, modelo ni regla asociada a gestión de cuentas break-glass o control 8.2. |
| **3** | Exclusión de auditoría de ciclo de vida de secretos estáticos (antigüedad de access keys, rotación global de claves). | **Sin incumplimientos detectados** | No hay lógica que evalúe campos de rotación de credenciales (`access_key_last_rotated`, `password_next_rotation`). |
| **4** | Exclusión de auditoría del plano de datos (S3 ACLs, DynamoDB, KMS, Macie, cifrado en reposo). | **Sin incumplimientos detectados** | El repositorio y el modelo de datos están orientados exclusivamente a identidades y políticas de IAM. |
| **5** | Exclusión del plano de cómputo y sistemas operativos (SSM Run Command, Session Manager, binarios en EC2). | **Sin incumplimientos detectados** | No hay referencias a cómputo ni inspección de sistemas operativos. |
| **6** | No implementación de eventos continuos, CloudTrail en tiempo real ni SIEM/IDS/IPS. Solo consulta de metadatos puntuales de último uso. | **Sin incumplimientos detectados** | La consulta de base de datos solo accede a metadatos de atributos estáticos y puntual de último uso. |
| **7** | Análisis de políticas JSON técnicas de IAM, no de documentos corporativos normativos. | **Sin incumplimientos detectados** | El modelo de datos evalúa la estructura de atributos JSON asociados a recursos. |
| **8** | Exclusión de cláusulas de gestión 4 a 10 de ISO/IEC 27001. Evaluación limitada a controles técnicos seleccionados. | **Sin incumplimientos detectados** | El catálogo del sistema se limita exclusivamente a controles técnicos del Anexo A (5.15, 5.16, 5.18, 8.5). |
| **9** | Exclusión de perímetro de red e infraestructura perimetral (VPC, Security Groups, NACLs, Route53, WAF). | **Sin incumplimientos detectados** | El alcance del sistema está circunscrito al perímetro lógico de identidades en IAM. |

---

## 8. Problemas y observaciones identificadas

### 8.1. Problemas comprobados
1. **Ausencia de código fuente para el motor de reglas y modelos:**
   - *Detalle:* Las carpetas `src/auditoria_iam/audit/` y `src/auditoria_iam/audit/rules/` no poseen archivos `.py`. El sistema carece de la implementación editable de `IAM-001`, `IAM-002`, `IAM-003` e `IAM-004`.
   - *Impacto:* Bloqueo directo para la ejecución de auditorías automatizadas hasta que se implementen formalmente en la Fase 3.
2. **Falta de automatización en la suite de pruebas (`tests/`):**
   - *Detalle:* El directorio `tests/` carece de archivos de prueba unitaria ejecutables por `pytest`. Los scripts `test_connection.py` y `test_resources.py` requieren intervención humana manual por consola (`input`/`getpass`).
   - *Impacto:* Imposibilidad de realizar pruebas de integración continua o validaciones algorítmicas sin interacción de usuario.
3. **Desacoplamiento entre `.env` y el módulo de conexión:**
   - *Detalle:* `connection.py` no hace lectura del archivo de variables de entorno `.env` a pesar de que la librería `python-dotenv` está instalada.
   - *Impacto:* Obliga al paso manual de credenciales como argumentos de funciones, incrementando la fragilidad del código.
4. **Archivo de requerimientos desactualizado:**
   - *Detalle:* `requirements.txt` tiene tamaño de 0 bytes, dificultando la replicabilidad controlada del entorno en otros equipos.

### 8.2. Limitaciones técnicas y riesgos
- **Dependencia de la base de datos para la simulación:** Al no existir un generador sintético en `simulator/`, cualquier prueba algorítmica depende forzosamente de que MySQL Server esté activo y contenga datos precargados.
- **Riesgo de pérdida de registros históricos:** Existen 14 hallazgos y 14 evidencias históricas que deben ser estrictamente respetadas durante el desarrollo de nuevas consultas de persistencia en la Fase 2.

### 8.3. Recomendaciones técnicas
- Implementar en la Fase 2 un módulo `settings.py` que cargue la configuración de MySQL desde `.env` mediante dataclasses o tipos seguros.
- Restituir en la Fase 3 la clase base `BaseAuditRule` y las cuatro reglas con soporte estricto para los estados funcionales: `Conforme`, `Hallazgo` (diferencia que requiere revisión humana) y `No evaluable` (atributos incompletos).
- Implementar pruebas unitarias desacopladas de la base de datos utilizando mocks y diccionarios de prueba en memoria.

---

## 9. Decisiones técnicas establecidas

A partir del diagnóstico y los lineamientos del proyecto de titulación, quedan formalmente ratificadas las siguientes decisiones técnicas:

1. **Tipo de aplicación:** Aplicación de escritorio nativa orientada a analistas y auditores de seguridad.
2. **Tecnologías base:** Lenguaje Python 3.13.5, driver `mysql-connector-python`, SDK `boto3` para inspección en nube y `PySide6` para la interfaz gráfica.
3. **Gestión de persistencia:** Base de datos relacional MySQL Server 9.6 para garantizar integridad referencial mediante claves foráneas y trazabilidad inmutable de evidencias y hallazgos.
4. **Modalidad de ejecución:** Soporte para ejecución manual interactiva y ejecución programada por lotes (batch audit).
5. **Salidas del sistema:** Visualización de resultados en panel interactivo de escritorio y generación de informes estructurados exportables (reportes ejecutivos y técnicos).
6. **Enfoque de desarrollo:** Prototipo evolutivo modular basado en código limpio, sin reconstrucción destructiva de la arquitectura base.
7. **Tratamiento de datos:** Uso riguroso de identidades y políticas simuladas con fines de investigación académica, sin comprometer datos reales de UPHARVEN C.A.
8. **Alcance de cumplimiento:** Evaluación algorítmica circunscrita a los cuatro controles técnicos seleccionados de ISO/IEC 27001:2022:
   - Control 5.15 — Access control.
   - Control 5.16 — Identity management.
   - Control 5.18 — Access rights.
   - Control 8.5 — Secure authentication.
9. **Interpretación de resultados:** Un resultado de "Hallazgo" representa una diferencia técnica observable que amerita evaluación humana calificada; el sistema es una herramienta de soporte a la auditoría, no un certificador automático de la norma ISO/IEC 27001.

---

## 10. Resultado y cierre de la fase

### 10.1. Resultado general del diagnóstico
La Fase 1 concluye de manera **satisfactoria en su carácter de diagnóstico técnico**. Se logró determinar con total precisión el estado del proyecto, verificando la viabilidad de la arquitectura modular y detectando las brechas exactas entre los módulos implementados y los pendientes de desarrollo.

### 10.2. Estado de preparación del proyecto
- El proyecto **NO está terminado** ni se encuentra en estado de producción.
- La base de datos **cuenta con la estructura y datos históricos**, pero su integración en código Python está limitada a la lectura de la tabla `resources`.
- La arquitectura base es sólida y **no requiere sustitución ni reconstrucción**.

### 10.3. Aspectos que quedan pendientes para fases posteriores
- **Fase 2:** Integración segura de `.env`, ampliación del repositorio para soportar la persistencia de ejecuciones, reglas, hallazgos y evidencias sin afectar los 14 registros históricos.
- **Fase 3:** Implementación en código fuente de las cuatro reglas de auditoría (IAM-001 a IAM-004), la clase base y el motor algorítmico desacoplado.
- **Fase 4:** Construcción del simulador autónomo de identidades y roles IAM.
- **Fase 5:** Creación de la suite formal de pruebas unitarias automatizadas.
- **Fase 6:** Integración de solo lectura con AWS mediante Boto3.
- **Fase 7:** Desarrollo de la interfaz gráfica PySide6 y panel de control.
- **Fase 8:** Módulo de reportes y consolidación final.

### 10.4. Justificación del paso a la Fase 2
Habiéndose cumplido todos los objetivos de diagnóstico estático, verificación de dependencias, auditoría de seguridad y delimitación de alcance sin alterar archivos persistentes ni datos de MySQL, el proyecto cuenta con el sustento técnico y metodológico necesario para proceder a la **Fase 2: Consolidación de la base de datos y persistencia**.

---

## Control documental

- **Nombre del documento:** `DOCUMENTACION_FASE_1_DIAGNOSTICO.md`
- **Fase a la que pertenece:** Fase 1 — Diagnóstico y estabilización del proyecto
- **Versión documental:** 1.0
- **Estado del documento:** Documentación técnica formal elaborada y aprobada
- **Fecha de elaboración:** 31 de octubre de 2026
- **Relación con la documentación general del proyecto:** Este documento constituye el primer hito formal de la serie de especificaciones técnicas del proyecto de titulación. Servirá de insumo directo y referencia obligatoria para las especificaciones de la Fase 2 (Persistencia) y el posterior Resumen Ejecutivo Consolidado.

