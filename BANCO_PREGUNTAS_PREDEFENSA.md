# BANCO DE PREGUNTAS Y RESPUESTAS PARA LA PREDEFENSA DE TESIS
## Modelo Automatizado para la Auditoría de Gestión de Identidades y Accesos en Entornos de Nube Basado en el Estándar ISO/IEC 27001 para UPHARVEN C.A.

**Documento:** Banco Maestro de Preguntas y Respuestas de Defensa Oral  
**Destinataria:** Autora del Trabajo Especial de Grado  
**Objetivo:** Proporcionar un repertorio exhaustivo de preguntas probables del jurado calificador con respuestas fundamentadas estrictamente en la arquitectura, código fuente, base de datos y resultados verificados del prototipo.  
**Fecha:** Noviembre 2026  
**Versión del Prototipo:** 1.0.0  

---

## ÍNDICE GENERAL

1. [SECCIÓN 1: Preguntas Generales sobre el Proyecto](#sección-1-preguntas-generales-sobre-el-proyecto)
2. [SECCIÓN 2: Preguntas Difíciles sobre AWS y Seguridad en la Nube](#sección-2-preguntas-difíciles-sobre-aws-y-seguridad-en-la-nube)
3. [SECCIÓN 3: Preguntas sobre el Estándar ISO/IEC 27001:2022](#sección-3-preguntas-sobre-el-estándar-isoiec-270012022)
4. [SECCIÓN 4: Preguntas Técnicas y de Arquitectura de Software](#sección-4-preguntas-técnicas-y-de-arquitectura-de-software)
5. [SECCIÓN 5: Preguntas sobre Resultados, Métricas y Pruebas Automatizadas](#sección-5-preguntas-sobre-resultados-métricas-y-pruebas-automatizadas)
6. [SECCIÓN 6: Preguntas sobre Metodología de Desarrollo](#sección-6-preguntas-sobre-metodología-de-desarrollo)
7. [SECCIÓN 7: Preguntas Incómodas, Críticas y Manejo de Objeciones](#sección-7-preguntas-incómodas-críticas-y-manejo-de-objeciones)
8. [SECCIÓN 8: Preguntas Rápidas de Conceptos (Glosario Defensivo)](#sección-8-preguntas-rápidas-de-conceptos-glosario-defensivo)
9. [SECCIÓN 9: Simulación de Jurado Evaluador (Rondas de Alta Presión)](#sección-9-simulación-de-jurado-evaluador-rondas-de-alta-presión)

---

## GUÍA DE USO PARA LA AUTORA ANTES DE DEFENDER

> [!IMPORTANT]
> **Estructura mental para responder ante el jurado:**
> 1. **La Idea Principal primero (10 segundos):** Da una respuesta directa, afirmativa o clarificadora. No des rodeos ni titubees.
> 2. **El Fundamento Técnico (20-30 segundos):** Explica el *por qué* basado en la ingeniería del software (menciona componentes, clases, patrones o estándares).
> 3. **El Límite del Alcance (10 segundos):** Si la pregunta busca que admitas algo que no hiciste, delimita honestamente el alcance de tu tesis de grado sin disculparte; la delimitación rigurosa demuestra madurez académica.

---

## SECCIÓN 1. PREGUNTAS GENERALES SOBRE EL PROYECTO

### 1.1. ¿Cuál es el objetivo general de la investigación?
- **Idea principal:** El objetivo es diseñar y desarrollar un modelo automatizado para la auditoría de gestión de identidades y accesos (IAM) en entornos de nube pública (específicamente AWS), basado en controles seleccionados del estándar ISO/IEC 27001:2022 para UPHARVEN C.A.
- **Fundamento técnico:** La meta no era crear una herramienta comercial genérica, sino resolver la brecha metodológica y técnica que enfrenta una empresa en modernización: traducir requerimientos normativos de seguridad de la información en algoritmos deterministas de evaluación sobre configuraciones de nube, persistiendo evidencias inmutables para la toma de decisiones.

### 1.2. ¿Qué problema concreto busca resolver este sistema?
- **Idea principal:** Resuelve la vulnerabilidad, ineficiencia y falta de trazabilidad asociadas a las auditorías manuales de identidades y accesos en la nube.
- **Fundamento técnico:** En plataformas como AWS, el crecimiento de identidades (usuarios, roles, claves de acceso) provoca la proliferación de permisos excesivos (uso del comodín `*`), acumulación de credenciales inactivas por más de 90 días, ausencia de MFA y asignación de grupos no autorizados. Revisar esto manualmente en la consola web de AWS es lento, subjetivo, propenso a omisiones humanas y carece de un registro histórico centralizado.

### 1.3. ¿Por qué se eligió este tema de grado?
- **Idea principal:** Porque en la computación en la nube el perímetro tradicional de red ha desaparecido; la identidad es el nuevo perímetro de seguridad.
- **Fundamento técnico:** Según reportes internacionales de la industria (como Gartner y CSA), más del 80% de las brechas de seguridad en la nube involucran credenciales comprometidas o privilegios excesivos. Abordar IAM desde la óptica formal de ISO/IEC 27001:2022 aporta rigor de ingeniería de software a una necesidad real y crítica de la infraestructura moderna.

### 1.4. ¿Cuál es el aporte específico o valor agregado del prototipo desarrollado?
- **Idea principal:** El aporte principal es un **motor algorítmico determinista y desacoplado** que evalúa cuatro controles normativos de ISO 27001, complementado con una arquitectura relacional de 10 tablas que garantiza la inmutabilidad histórica de las evidencias.
- **Fundamento técnico:** A diferencia de scripts ad-hoc que imprimen texto por consola, este sistema implementa una arquitectura en 4 capas, gestiona un estado riguroso de `No evaluable` para prevenir falsos conformes, persiste transaccionalmente cada evaluación en MySQL y genera reportes ejecutivos en PDF, Excel y CSV listos para auditorías de cumplimiento.

### 1.5. ¿Quiénes serían los usuarios directos de esta aplicación?
- **Idea principal:** Oficiales de Seguridad de la Información (CISO), auditores internos de TI y administradores de sistemas o DevOps de la organización.
- **Fundamento técnico:** El sistema fue diseñado con una interfaz gráfica intuitiva en PySide6 que no exige conocimientos de programación en Python. Permite al oficial de seguridad ejecutar auditorías con un clic, filtrar hallazgos por severidad o recurso, consultar métricas en un dashboard interactivo y exportar informes ejecutivos formales.

### 1.6. ¿Qué diferencias sustanciales existen entre una auditoría manual tradicional y la propuesta automatizada?
- **Idea principal:** La auditoría automatizada aporta velocidad, exhaustividad matemática, determinismo y trazabilidad transaccional inmutable.
- **Fundamento técnico:** 
  - *Tiempo:* Una auditoría manual de 10 identidades y decenas de políticas puede tardar horas o días; el sistema la ejecuta en menos de 2 segundos.
  - *Determinismo:* La inspección manual es susceptible al cansancio o criterio dispar del auditor humano; el motor algorítmico evalúa exactamente las mismas reglas lógicas ante los mismos datos.
  - *Evidencia:* En lo manual se toman capturas de pantalla dispersas; el prototipo almacena los documentos JSON originales y las trazas en bases de datos relacionales normalizadas.

---

## SECCIÓN 2. PREGUNTAS DIFÍCILES SOBRE AWS Y SEGURIDAD EN LA NUBE

### 2.1. Si AWS ya cuenta con herramientas nativas de auditoría, ¿por qué desarrollaste este sistema?
- **Idea principal:** Reconocemos plenamente que AWS ofrece herramientas potentes como IAM Access Analyzer, AWS Config y Security Hub. Sin embargo, este prototipo no pretende competir con ellas a nivel de infraestructura global, sino resolver una necesidad metodológica local: **alineación normativa directa con ISO 27001 y control de soberanía de datos para UPHARVEN C.A.**
- **Fundamento técnico:** Las herramientas nativas de AWS:
  1. Están dispersas entre distintos servicios de cobro recurrente por recurso analizado (AWS Config cobra por regla y por configuración registrada).
  2. No ofrecen una correlación directa y nativa contra la nomenclatura de controles de ISO/IEC 27001:2022 orientada al perfil de la empresa.
  3. No permiten comparar los recursos de la nube contra una **línea base local de perfiles autorizados** definida por las políticas internas de recursos humanos de UPHARVEN C.A.
  Nuestro sistema unifica esta lógica en una herramienta de escritorio sin costo operativo adicional y con almacenamiento en una base de datos interna.

### 2.2. ¿Qué diferencia existe entre tu sistema e IAM Access Analyzer?
- **Idea principal:** IAM Access Analyzer se enfoca en el análisis formal de políticas para detectar accesos externos y evaluar condiciones matemáticas de acceso público o entre cuentas. Nuestro sistema audita el cumplimiento normativo interno de buenas prácticas organizacionales.
- **Fundamento técnico:** IAM Access Analyzer no audita si un usuario local tiene más de 90 días inactivo, ni si pertenece a grupos de soporte autorizados por el departamento de TI de UPHARVEN, ni si tiene MFA habilitado en consola con claves de acceso activas simultáneas. Nuestro sistema audita el ciclo de vida de la identidad y la adhesión a la línea base organizacional.

### 2.3. ¿Por qué utilizaste el SDK oficial Boto3 en lugar de consultar la API REST directamente o usar AWS CLI?
- **Idea principal:** Porque Boto3 es el SDK oficial, tipado y mantenido por AWS para Python, lo que asegura máxima estabilidad, gestión idiomática de credenciales y tratamiento nativo de excepciones de red y paginación.
- **Fundamento técnico:** Consumir la API REST directamente requeriría implementar manualmente el algoritmo complejo de firma criptográfica *AWS Signature Version 4* en cada petición HTTP. Por otro lado, invocar AWS CLI mediante subprocesos del sistema operativo introduciría sobrecarga de procesos externos, fragilidad al parsear texto y dependencia de binarios instalados en la máquina cliente.

### 2.4. ¿Cómo funciona el sistema si no se contó con una cuenta real de AWS de UPHARVEN C.A.?
- **Idea principal:** El sistema implementa el patrón de diseño *Adaptador* mediante la clase abstracta `DataSource`, lo que desacopló completamente la lógica de auditoría del origen de los datos.
- **Fundamento técnico:** Desarrollamos dos adaptadores complementarios:
  1. `SimulatorDataSource`: Carga un escenario sintético realista de 10 recursos (usuarios y roles) con políticas JSON complejas y perfiles autorizados, permitiendo verificar de extremo a extremo la lógica de negocio y la interfaz.
  2. `AWSIAMDataSource`: Implementa las 17 operaciones reales de Boto3 para conectarse a AWS. Su funcionamiento se validó exhaustivamente de forma automatizada mediante la herramienta `botocore.stub.Stubber`.

### 2.5. ¿Cómo demuestras rigurosamente que el adaptador AWS funciona si no te conectaste en vivo durante la defensa?
- **Idea principal:** Lo demuestro mediante la suite de 44 pruebas unitarias de `tests/test_aws_adapter_stubber.py`, utilizando la herramienta oficial de AWS `botocore.stub.Stubber`.
- **Fundamento técnico:** `Stubber` intercepta las llamadas internas a nivel del cliente HTTP de Boto3 y compara la llamada real contra las especificaciones formales de los servicios de AWS. Si el adaptador construye un parámetro mal formado o procesa incorrectamente una respuesta paginada (`Marker`, `IsTruncated`), la prueba falla inmediatamente. Las 44 pruebas pasaron con 100% de éxito, demostrando que el código respeta con precisión milimétrica la API de AWS IAM.

### 2.6. ¿El sistema modifica permisos, borra recursos o realiza remediación en la nube?
- **Idea principal:** **No, categóricamente no.** El sistema se adhiere de forma estricta a un principio de diseño de **solo lectura e inocuidad operativa**.
- **Fundamento técnico:** El adaptador solo ejecuta métodos que inician con `get_*` o `list_*`. No existe una sola línea de código que invoque métodos de modificación (`create_*`, `delete_*`, `put_*`, `attach_*`, `detach_*`). Una herramienta de auditoría independiente nunca debe alterar el entorno auditado para evitar caídas de servicios productivos o destrucción accidental de datos.

### 2.7. ¿Por qué no utilizaste servicios gestionados como AWS Config o AWS Security Hub?
- **Idea principal:** Porque el objetivo de una tesis de ingeniería informática es modelar e implementar la lógica algorítmica de auditoría, persistencia e interfaz, no meramente contratar o configurar servicios de terceros en la nube.
- **Fundamento técnico:** Utilizar Security Hub hubiera convertido la investigación en una simple tarea de configuración de consola en la nube. Además, AWS Config y Security Hub implican costos recurrentes mensuales en dólares y requieren que la organización otorgue permisos amplios a servicios de AWS para rastrear eventos, lo cual muchas pequeñas y medianas empresas no pueden costear ni autorizar legalmente.

### 2.8. ¿Qué sucedería si AWS devuelve información incompleta, vacía o con errores de permisos?
- **Idea principal:** El sistema no colapsa ni genera fallos silenciosos: captura las excepciones tipadas de Boto3 y emite estados de evaluación transparentes.
- **Fundamento técnico:** 
  - Si faltan credenciales o permisos en la cuenta (`ClientError: AccessDenied`), el adaptador lo atrapa y propaga un error descriptivo al usuario en la interfaz.
  - Si un recurso carece de datos suficientes para evaluar un criterio (por ejemplo, un usuario sin metadatos de último acceso), el motor emite el estado **`No evaluable`**, evitando asumir que el recurso está conforme.

---

## SECCIÓN 3. PREGUNTAS SOBRE EL ESTÁNDAR ISO/IEC 27001:2022

### 3.1. ¿Por qué seleccionaste específicamente esos cuatro controles del estándar?
- **Idea principal:** Porque representan el núcleo técnico crítico y auditable de la gestión de identidades y accesos según el Anexo A de ISO/IEC 27001:2022.
- **Fundamento técnico:** El Anexo A contiene 93 controles agrupados en 4 temas (Organizacionales, Personas, Físicos y Tecnológicos). Muchos de ellos son puramente procedimentales (como políticas de recursos humanos o concientización). Se seleccionaron cuatro controles que poseen correlación técnica directa con parámetros verificables en AWS IAM:
  - **A.5.15:** Control de acceso y perfiles autorizados.
  - **A.5.16:** Gestión de identidades y credenciales inactivas.
  - **A.5.18:** Derechos de acceso privilegiados y menor privilegio.
  - **A.8.5:** Autenticación segura y robusta (MFA y claves de acceso).

### 3.2. ¿Qué relación técnica tiene cada uno de los cuatro controles con la gestión de IAM?
- **Idea principal:** Cada control fue traducido a una regla algorítmica con criterios matemáticos claros:
  1. **IAM-001 (Control 5.15):** Verifica que los grupos asignados al usuario y los *principals* de confianza del rol coincidan exactamente con la línea base organizacional.
  2. **IAM-002 (Control 5.16):** Evalúa las fechas `PasswordLastUsed` y `AccessKeyLastUsed`; si superan el umbral paramétrico de 90 días, detecta una credencial inactiva que debe revocarse.
  3. **IAM-003 (Control 5.18):** Inspecciona los documentos de política JSON buscando el comodín global (`Action: *` y `Resource: *`), políticas administradas de superusuario (`AdministratorAccess`) o permisos sensibles de escalamiento (`iam:*`, `sts:AssumeRole`).
  4. **IAM-004 (Control 8.5):** Comprueba que los usuarios con acceso a la consola tengan MFA activo y que ningún usuario tenga más de dos claves de acceso activas ni claves sin rotar.

### 3.3. ¿El sistema certifica formalmente el cumplimiento de la norma ISO/IEC 27001?
- **Idea principal:** **No.** El sistema es una herramienta de apoyo técnico a la auditoría; la certificación formal solo puede otorgarla un ente acreditador externo mediante una auditoría integral del SGSI.
- **Fundamento técnico:** ISO/IEC 27001 es un estándar holístico de gestión de seguridad de la información que evalúa políticas organizacionales, procesos de negocio, cultura, análisis de riesgos y controles físicos. Nuestro prototipo evalúa la conformidad técnica de cuatro controles tecnológicos específicos dentro del alcance de IAM en la nube.

### 3.4. ¿Un hallazgo detectado por el motor significa necesariamente un incumplimiento normativo formal?
- **Idea principal:** Significa una **no conformidad técnica** respecto a la regla algorítmica y la línea base configurada, la cual debe ser analizada por el auditor de seguridad.
- **Fundamento técnico:** En auditorías reales, puede existir una excepción formal aprobada por el comité de seguridad (por ejemplo, una cuenta de servicio de emergencia que no utiliza MFA). El sistema señala el hallazgo con su severidad y evidencia para que el auditor verifique si cuenta con justificación o si constituye una brecha que amerita tratamiento de riesgo.

### 3.5. ¿Por qué no se evaluaron todos los 93 controles del Anexo A de la norma?
- **Idea principal:** Porque la gran mayoría de los controles de ISO 27001 no pertenecen al ámbito de IAM ni son técnicamente auditables mediante APIs de nube.
- **Fundamento técnico:** Controles como el 7.1 (Seguridad física perimetral), 6.3 (Concienciación en seguridad de la información) o 5.4 (Responsabilidades de la dirección) son organizacionales y procedimentales. Enfocarse en los 4 controles fundamentales de IAM permitió profundizar en la inspección sintáctica de políticas JSON, matrices de perfiles y estados de credenciales con alto rigor ingenieril.

### 3.6. ¿Qué significa exactamente que un control o evaluación resulte en estado "No evaluable"?
- **Idea principal:** Significa que por la naturaleza del recurso o por ausencia de datos en el origen, la regla no puede emitir un juicio definitivo de Conforme ni de Hallazgo.
- **Fundamento técnico:** Es una salvaguarda esencial para evitar el sesgo de "falso conforme". Por ejemplo, un rol de IAM no tiene contraseñas ni dispositivos MFA físicos; al evaluar la regla IAM-004 sobre un rol, el sistema determina técnicamente `No evaluable`. Asumir que estaba "Conforme" engañaría a la gerencia, y clasificarlo como "Hallazgo" generaría una falsa alarma.

---

## SECCIÓN 4. PREGUNTAS TÉCNICAS Y DE ARQUITECTURA DE SOFTWARE

### 4.1. ¿Por qué se seleccionó Python 3.13 como lenguaje de desarrollo?
- **Idea principal:** Por su ecosistema nativo líder en seguridad en la nube, madurez en procesamiento de estructuras de datos complejas (JSON) y soporte oficial de Boto3.
- **Fundamento técnico:** Python es el estándar de facto para herramientas de ciberseguridad y DevOps. Su tipado dinámico enriquecido con type hints modernos en Python 3.13, sumado a bibliotecas de primer nivel como PySide6, Boto3, ReportLab y OpenPyXL, permitió construir una solución cohesiva sin fricciones entre capas.

### 4.2. ¿Por qué se implementó como una aplicación de escritorio con PySide6 y no como una plataforma web?
- **Idea principal:** Por estrictas razones de **seguridad de credenciales, soberanía de datos y menor superficie de ataque**.
- **Fundamento técnico:** Una aplicación web requiere desplegar un backend con puertos de red expuestos, gestión de sesiones HTTP, certificados TLS y almacenamiento de credenciales de AWS en servidores web compartidos, introduciendo riesgos de inyección y fuga de claves. Una aplicación de escritorio opera localmente: las credenciales temporales permanecen en la memoria volátil de la estación del auditor y los datos residen en su base de datos corporativa controlada.

### 4.3. ¿Por qué se eligió MySQL Server y no SQLite o una base de datos NoSQL?
- **Idea principal:** Porque se requería concurrencia multiusuario, soporte estricto de transacciones ACID y restricciones relacionales avanzadas que garanticen la inmutabilidad de los hallazgos.
- **Fundamento técnico:** SQLite carece de tipos de datos estrictos y bloquea todo el archivo ante escrituras concurrentes. Una base NoSQL carece de restricciones de integridad referencial. MySQL Server bajo el motor **InnoDB** nos permitió implementar claves foráneas en cascada, columnas virtuales generadas con restricciones UNIQUE compuestas (como evitar que una identidad tenga dos perfiles activos) y aislamiento transaccional seguro con `get_db_transaction()`.

### 4.4. ¿Qué función cumple Boto3 dentro de la arquitectura?
- **Idea principal:** Cumple el rol de conector de bajo nivel en la capa de infraestructura para interactuar con la API pública de AWS IAM.
- **Fundamento técnico:** Boto3 se encapsula dentro de `AWSIAMDataSource` y `IAMAdapter`. Se encarga de instanciar clientes de bajo nivel con credenciales seguras, procesar paginadores mediante `get_paginator()` y deserializar las respuestas XML de la API de AWS en estructuras nativas de Python (diccionarios y listas) listas para ser normalizadas por los modelos de dominio.

### 4.5. ¿Qué es exactamente el motor de auditoría (`AuditEngine`) y qué patrón de diseño sigue?
- **Idea principal:** Es el componente central de la capa de dominio encargado de orquestar la evaluación algorítmica de todas las identidades contra el catálogo de reglas.
- **Fundamento técnico:** Sigue el patrón de diseño **Estrategia (Strategy Pattern)**: cada regla de auditoría (`iam001.py` a `iam004.py`) implementa una interfaz común (`evaluate(resource, context)`), permitiendo al motor iterar de forma polimórfica y desacoplada sobre las identidades sin conocer la lógica interna de cada regla.

### 4.6. ¿Cómo se ejecutan y evalúan las cuatro reglas en el código?
- **Idea principal:** El motor recibe la lista de recursos normalizados (`ResourceRecord`), los perfiles de acceso y los parámetros de configuración; luego evalúa cada recurso frente a cada regla mediante métodos de evaluación deterministas.
- **Fundamento técnico:** Cada regla analiza atributos específicos:
  - `IAM001`: Compara conjuntos (`set`) de grupos asignados vs esperados.
  - `IAM002`: Calcula la diferencia en días entre la fecha de corte y la fecha de uso (`(now - last_used).days > 90`).
  - `IAM003`: Recorre los bloques `Statement` de cada política JSON, validando coincidencias de comodines en `Action` y `Resource`.
  - `IAM004`: Verifica indicadores booleanos de MFA y cuenta la cantidad de `AccessKeys` con estado `Active`.
  Cada regla retorna una estructura `RuleEvaluationResult` con su estado, severidad y mensaje de evidencia.

### 4.7. ¿Qué información exacta se almacena en la base de datos relacional?
- **Idea principal:** Se almacenan el catálogo normativo, las líneas base de perfiles, los metadatos de las identidades y el registro histórico completo de ejecuciones, evaluaciones y hallazgos.
- **Fundamento técnico:** La base de datos consta de **10 tablas**:
  1. `audit_rules`: Catálogo de controles ISO y severidad.
  2. `access_profiles`: Definición de cargos y perfiles organizacionales.
  3. `profile_expected_groups`: Grupos permitidos por perfil.
  4. `profile_expected_trust_principals`: Entidades autorizadas para asumir roles.
  5. `resources`: Inventario de usuarios y roles con sus atributos JSON.
  6. `resource_access_profiles`: Vinculación de recursos a perfiles.
  7. `audit_runs`: Registro de cabecera de la auditoría (fecha, fuente, resumen).
  8. `audit_results`: Detalle granular de las 67 evaluaciones individuales.
  9. `findings`: Registro específico de los 6 hallazgos.
  10. `audit_evidence`: Trazas técnicas y volcados de respaldo vinculados por clave foránea.

### 4.8. ¿Cómo se generan los informes técnicos y ejecutivos (PDF, Excel, CSV)?
- **Idea principal:** Se generan a través del módulo de reportes utilizando bibliotecas nativas de procesamiento de documentos a partir de los datos consolidados en memoria y base de datos.
- **Fundamento técnico:**
  - **PDF:** Desarrollado con **ReportLab**, genera un diseño visual profesional con paleta de colores corporativa, encabezados, tablas de resumen ejecutivo, desglose de hallazgos y numeración de páginas mediante un canvas personalizado de dos pasadas (`NumberedCanvas`).
  - **Excel:** Construido con **OpenPyXL**, genera un libro con múltiples hojas de cálculo (Resumen, Hallazgos, Todas las Evaluaciones e Inventario) con filtros automáticos, anchos de columna ajustados y estilos en celdas de encabezado.
  - **CSV:** Genera un archivo tabular delimitado por comas y codificado en `utf-8-sig` para fácil importación en herramientas de inteligencia de negocios como Power BI.

### 4.9. ¿Cómo se garantiza a nivel arquitectónico que una auditoría nunca modifique recursos en AWS?
- **Idea principal:** Se garantiza mediante la combinación de un diseño de código estrictamente consultivo y una lista blanca explícita de operaciones de solo lectura.
- **Fundamento técnico:** En `adapter.py` se definió la tupla inmutable `READ_ONLY_OPERATIONS` con 19 operaciones autorizadas de Boto3. No existe ningún método en todo el código base que invoque primitivas de escritura o borrado. Además, las buenas prácticas del sistema exigen que las credenciales de AWS otorgadas al auditor tengan asignada la política administrada `SecurityAudit` o `ReadOnlyAccess`, garantizando que AWS rechazaría cualquier mutación a nivel de infraestructura.

### 4.10. ¿Qué significa que las operaciones de AWS sean de solo lectura?
- **Idea principal:** Significa que las llamadas a la API se limitan exclusivamente a consultar metadatos y documentos existentes (`get_*` y `list_*`), sin alterar el estado de las configuraciones en la nube.
- **Fundamento técnico:** Operaciones como `list_users()`, `get_access_key_last_used()` o `get_role_policy()` únicamente leen y devuelven representaciones en memoria. No generan cambios en las políticas de seguridad ni interrumpen las sesiones activas de los usuarios en producción.

---

## SECCIÓN 5. PREGUNTAS SOBRE RESULTADOS, MÉTRICAS Y PRUEBAS AUTOMATIZADAS

### 5.1. ¿Cómo se obtuvieron las 67 evaluaciones del simulador y cómo se calcula esa cifra?
- **Idea principal:** Las 67 evaluaciones resultan de evaluar los 10 recursos del simulador contra los criterios aplicables de las 4 reglas del motor de auditoría.
- **Fundamento técnico:** Cada regla contiene uno o más criterios de evaluación:
  - `IAM-001`: 2 criterios (C15-01 para grupos y C15-02 para confianza de roles).
  - `IAM-002`: 2 criterios (C16-01 para contraseña y C16-02 para access keys).
  - `IAM-003`: 3 criterios (C18-01 comodín `*`, C18-02 `AdministratorAccess`, C18-03 permisos sensibles).
  - `IAM-004`: 2 criterios (C85-01 MFA en consola y C85-02 rotación de claves).
  Al ejecutarse sobre los 7 usuarios y 3 roles, el motor genera exactamente 67 registros de evaluación granular en la tabla `audit_results`.

### 5.2. ¿Qué representan exactamente los 36 resultados Conforme?
- **Idea principal:** Representan el **53,73%** de las evaluaciones donde las configuraciones del recurso analizado cumplieron satisfactoriamente con la regla y los perfiles autorizados.
- **Fundamento técnico:** Por ejemplo, usuarios con MFA activo, usuarios que pertenecen exclusivamente a los grupos autorizados para su cargo, o credenciales que han sido utilizadas recientemente dentro del límite de 90 días.

### 5.3. ¿Por qué existen 25 resultados clasificados como No evaluable en la simulación?
- **Idea principal:** Representan el **37,31%** de las evaluaciones y corresponden a criterios que no aplican técnicamente a un tipo de recurso determinado.
- **Fundamento técnico:** Por ejemplo, los roles de IAM no inician sesión mediante contraseñas ni portan dispositivos MFA físicos (son identidades asumidas temporalmente por servicios o aplicaciones). Por ende, evaluar los criterios de MFA o contraseñas sobre un rol da como resultado legítimo `No evaluable`.

### 5.4. ¿Qué representan los seis hallazgos detectados y cuáles son en detalle?
- **Idea principal:** Representan el **8,96%** de las evaluaciones y corresponden a desviaciones de seguridad deliberadamente inyectadas en el escenario simulado para validar el poder de detección del motor.
- **Fundamento técnico:** Los 6 hallazgos corresponden a:
  1. `carlos.soporte` (IAM-001): Asignación no autorizada del grupo `SeguridadTI`.
  2. `carlos.soporte` (IAM-003): Política en línea con permisos irrestrictos de superusuario (`Action: *` y `Resource: *`).
  3. `usuario.inactivo` (IAM-002): Credencial de acceso sin utilizar durante 120 días (superando el umbral de 90 días).
  4. `cuenta.sin_mfa` (IAM-004): Usuario con acceso a la consola de AWS sin autenticación multifactor configurada.
  5. `usuario.grupos_discrepantes` (IAM-001): Grupos discordantes respecto a su perfil (posee `AuditoriaInterna` y `Finanzas`, careciendo de los requeridos).
  6. `rol.discrepante` (IAM-001): Política de confianza mal configurada (permite ser asumido por `lambda.amazonaws.com` en lugar de `ec2.amazonaws.com`).

### 5.5. ¿Cómo verificaste empíricamente que las cuatro reglas algorítmicas funcionan sin fallas?
- **Idea principal:** Mediante pruebas unitarias automatizadas exhaustivas con datos sintéticos controlados, cubriendo casos válidos, casos inválidos, casos borde y excepciones.
- **Fundamento técnico:** En el directorio `tests/` existen suites independientes para cada regla (`test_rule_iam_001.py` con 16 pruebas, `test_rule_iam_002.py` con 13 pruebas, `test_rule_iam_003.py` con 22 pruebas y `test_rule_iam_004.py` con 6 pruebas). Estas 57 pruebas dedicadas verifican que ante cualquier combinación de datos, la regla devuelva exactamente el estado y severidad esperados.

### 5.6. ¿Qué significan las 309 pruebas automatizadas aprobadas y cómo se distribuyen?
- **Idea principal:** Significa que todo el sistema (adaptadores, reglas, motor, persistencia en base de datos, generación de reportes e interfaz gráfica) cuenta con una cobertura integral de pruebas que se ejecutan automáticamente en 9,59 segundos con 100% de éxito.
- **Fundamento técnico:** Se distribuyen en 19 archivos de prueba cubriendo:
  - Adaptador AWS y Stubber: 44 pruebas.
  - Orígenes de datos y flujos End-to-End: 51 pruebas.
  - Motor de reglas y modelos de dominio: 71 pruebas.
  - Base de datos, repositorio y persistencia: 41 pruebas.
  - Interfaz de usuario (UI), Dashboard y navegación: 66 pruebas.
  - Generación de reportes (PDF, Excel, CSV) y ajustes: 27 pruebas.
  - Conexión y simulador: 15 pruebas.

### 5.7. ¿Las pruebas con Stubber equivalen a una auditoría real en AWS?
- **Idea principal:** **No equivalen a una auditoría sobre infraestructura real**, pero garantizan matemáticamente que el adaptador cliente se comunica e interactúa con la API de AWS de forma correcta.
- **Fundamento técnico:** `Stubber` valida el contrato de interfaz: asegura que el adaptador genera las peticiones con los tipos de datos exactos exigidos por AWS y procesa las respuestas oficiales sin colapsar. La auditoría real requeriría credenciales de una cuenta activa con recursos desplegados; Stubber valida la corrección técnica del software sin generar tráfico externo ni costos en nube.

### 5.8. ¿Qué limitaciones tiene la estrategia de validación técnica implementada?
- **Idea principal:** La principal limitación es que la validación se realizó en entornos sintéticos y aislados, sin medir la latencia de red real de AWS ni entornos masivos con miles de identidades concurrentes.
- **Fundamento técnico:** En una cuenta empresarial con 5.000 usuarios, Boto3 podría enfrentar cuotas de limitación de tasa de peticiones (*API Throttling*). Aunque nuestro adaptador maneja paginadores, no implementa un algoritmo de retroceso exponencial (*exponential backoff*) avanzado para mitigar throttling masivo en cuentas gigantescas.

---

## SECCIÓN 6. PREGUNTAS SOBRE METODOLOGÍA DE DESARROLLO

### 6.1. ¿Por qué seleccionaste la Metodología de Desarrollo por Prototipos?
- **Idea principal:** Porque los proyectos de investigación que integran estándares normativos con APIs de nube presentan incertidumbre técnica inicial que requiere validaciones empíricas tempranas antes de construir la solución definitiva.
- **Fundamento técnico:** El modelo de prototipado evolutivo permite construir incrementos funcionales rápidos, someterlos a pruebas rigurosas, detectar inconsistencias en la interpretación de los controles y refinar la arquitectura por capas de forma progresiva sin comprometer la base del sistema.

### 6.2. ¿Cómo aplicaste concretamente esa metodología a lo largo de la investigación?
- **Idea principal:** Se aplicó mediante un ciclo estructurado de 7 fases incrementales donde cada fase culminó con código funcional, pruebas automatizadas y documentación técnica formal.
- **Fundamento técnico:** No se construyó la interfaz hasta que el motor de dominio y las reglas estuvieron plenamente probados. Cada componente se validó de forma aislada antes de integrarse al flujo principal, permitiendo refactorizaciones seguras guiadas por pruebas unitarias.

### 6.3. ¿Cuáles fueron las 7 fases de desarrollo del proyecto?
- **Idea principal:** Las fases abarcaron desde el diagnóstico normativo inicial hasta el cierre formal del sistema:
  1. **Fase 1: Diagnóstico y Especificación:** Definición de controles ISO y mapeo de atributos IAM.
  2. **Fase 2: Modelo Relacional y Persistencia:** Creación del esquema MySQL de 10 tablas y repositorio.
  3. **Fase 3: Motor Algorítmico y Reglas:** Implementación de las 4 reglas (IAM-001 a IAM-004) y el `AuditEngine`.
  4. **Fase 4: Fuentes de Datos y Simulación:** Creación del escenario sintético determinista (`SimulatorDataSource`).
  5. **Fase 5: Interfaz de Usuario e Integración:** Construcción de la aplicación de escritorio en PySide6 y flujo transaccional.
  6. **Fase 6: Dashboard y Reportes:** Módulo de analítica visual y exportación a PDF, Excel y CSV.
  7. **Fase 7: Adaptador AWS y Cierre:** Implementación del cliente Boto3, validación con Stubber y paquete de entrega.

### 6.4. ¿Cómo evolucionó el sistema desde sus primeros scripts hasta la versión final?
- **Idea principal:** Evolucionó de una colección de scripts aislados de análisis sintáctico a una aplicación modular de escritorio con arquitectura en capas desacopladas, inmutabilidad relacional y suite de 309 pruebas.
- **Fundamento técnico:** En las primeras fases los resultados se emitían por terminal. En la versión final, el sistema desacopló el motor de la persistencia, introdujo el manejo estricto de claves naturales en MySQL, implementó un canal asíncrono para no congelar la GUI durante auditorías y estandarizó un formato de reporte ejecutivo.

### 6.5. ¿Qué ventajas prácticas tuvo trabajar mediante prototipos frente a un modelo en cascada tradicional?
- **Idea principal:** Permitió identificar errores conceptuales en etapas tempranas sin necesidad de reescribir todo el software.
- **Fundamento técnico:** En un modelo en cascada, si la interpretación del control 5.15 sobre comodines en políticas JSON hubiera tenido un error de lógica, se habría detectado al final del proyecto tras haber construido la base de datos y la interfaz. Con prototipos, la regla se validó con pruebas unitarias en la Fase 3 mucho antes de diseñar la pantalla que la consume.

---

## SECCIÓN 7. PREGUNTAS INCÓMODAS, CRÍTICAS Y MANEJO DE OBJECIONES

### 7.1. ¿Cómo puedes hablar de UPHARVEN C.A. si no tuviste acceso directo a su infraestructura real de producción?
- **Idea principal:** El proyecto es una **investigación aplicada y un desarrollo de ingeniería sobre un modelo de referencia**, no una consultoría externa en sitio con permisos de producción.
- **Fundamento técnico:** UPHARVEN C.A. es una empresa que evalúa su migración hacia la nube. Como estudiante e investigadora, solicitar credenciales con permisos de auditoría sobre servidores reales de producción violaría las propias políticas de seguridad de la información de la empresa. La investigación modeló sus perfiles de cargo, sus necesidades normativas y sus requerimientos técnicos dentro de un simulador determinista y construyó el adaptador técnico para que la empresa pueda ejecutarlo en su entorno con total confidencialidad.

### 7.2. ¿Los datos utilizados en las demostraciones son datos reales de empleados de la empresa?
- **Idea principal:** **No, son datos sintéticos deliberadamente anonimizados.**
- **Fundamento técnico:** En cumplimiento estricto de los principios de confidencialidad y protección de datos exigidos por la ética profesional y la norma ISO/IEC 27001, nunca deben utilizarse nombres reales, credenciales activas o direcciones IP productivas en pruebas de software académicas. Los datos de prueba representan arquetipos organizacionales realistas pero ficticios.

### 7.3. ¿Cómo sabes con certeza que este sistema funcionaría si se despliega mañana en una empresa real?
- **Idea principal:** Lo sabemos porque el adaptador AWS utiliza los contratos de interfaz oficiales de Boto3 validados con `Stubber` y el motor de auditoría procesa las estructuras JSON estándar que emite la API de AWS.
- **Fundamento técnico:** La API de IAM de AWS es universal: la respuesta que devuelve `list_users()` en una cuenta de prueba tiene exactamente la misma estructura de tipos, diccionarios y claves que en una cuenta corporativa multinacional. Al haber validado que el adaptador parsea y normaliza dicha respuesta sin errores, el comportamiento del motor ante una cuenta real es idéntico.

### 7.4. ¿Qué validez académica y práctica tienen los resultados si provienen de datos simulados?
- **Idea principal:** Tienen plena validez metodológica porque demuestran que **el modelo algorítmico es capaz de discriminar con precisión matemática entre configuraciones conformes, configuraciones no evaluables y brechas de seguridad**.
- **Fundamento técnico:** En la ciencia de la computación y la ingeniería de software, los bancos de pruebas sintéticos son el estándar para validar algoritmos. Probar el sistema contra datos simulados con casos borde controlados permitió demostrar que el motor no tiene sesgos y que detecta los 6 hallazgos inyectados con 100% de reproducibilidad.

### 7.5. ¿Por qué no implementaste auditorías automáticas programadas mediante cron o demonios?
- **Idea principal:** Porque se priorizó la seguridad operativa y el control humano directo exigido para una herramienta de auditoría de escritorio.
- **Fundamento técnico:** Ejecutar procesos de auditoría en segundo plano sin supervisión requiere almacenar claves de acceso permanentes en disco (*hardcoded* o en servicios de sistema), lo cual vulnera las buenas prácticas de seguridad. En esta etapa de prototipo, la auditoría interactiva ejecutada por el auditor asegura que las credenciales solo residan en memoria durante la ejecución de la tarea.

### 7.6. ¿Qué pasaría si el sistema identifica incorrectamente un hallazgo (falso positivo)?
- **Idea principal:** El sistema previene los falsos positivos gracias a su diseño determinista basado en conjuntos lógicos, pero si ocurre, la herramienta entrega la **evidencia técnica cruda** para que el auditor humano la evalúe.
- **Fundamento técnico:** El sistema no actúa como una "caja negra". Cada hallazgo registrado en la tabla `findings` y en los reportes incluye el fragmento JSON exacto de la política o la fecha de la credencial en `audit_evidence`. El auditor humano siempre tiene el juicio final y la evidencia completa para descartar una falsa alarma.

### 7.7. ¿Qué diferencia a tu trabajo de grado de un simple script en Python que consulta usuarios de IAM?
- **Idea principal:** Un script aislado es un conjunto de instrucciones no estructuradas; este proyecto es un **sistema de información completo con arquitectura de software empresarial**.
- **Fundamento técnico:** 
  - *Arquitectura:* Separa limpiamente Presentación, Aplicación, Dominio e Infraestructura.
  - *Persistencia:* Diseña un modelo relacional de 10 tablas en MySQL con restricciones transaccionales ACID y claves naturales.
  - *Calidad de software:* Cuenta con 309 pruebas automatizadas con 100% de aprobación.
  - *Alineación normativa:* No solo lista identidades, sino que las compara algorítmicamente contra controles formales de ISO 27001 y perfiles autorizados.
  - *Experiencia de usuario:* Posee una interfaz gráfica moderna, dashboard analítico interactivo y exportación ejecutiva a PDF y Excel.

### 7.8. ¿Cuál es el aporte real de tu investigación a la ingeniería informática?
- **Idea principal:** El aporte radica en **operacionalizar un estándar normativo abstracto (ISO/IEC 27001:2022) en un motor algorítmico determinista de software aplicable a la nube pública**.
- **Fundamento técnico:** La norma indica "qué" principio de seguridad debe alcanzarse, pero no proporciona algoritmos ni modelos de datos para la nube. Este trabajo cierra esa brecha, construyendo un puente formal entre la gobernanza de TI y la ingeniería de software aplicada a la ciberseguridad en AWS.

### 7.9. ¿Qué aspectos técnicos mejorarías o implementarías si dispusieras de 6 meses adicionales?
- **Idea principal:** Ampliaría la cobertura normativa a otros controles de ISO 27001, implementaría soporte multinube y desarrollaría un módulo de remediación asistida.
- **Fundamento técnico:**
  1. *Políticas organizacionales avanzadas:* Analizar *Service Control Policies* (SCPs) en AWS Organizations y *Permission Boundaries*.
  2. *Multinube:* Desarrollar adaptadores para Microsoft Entra ID (Azure) y Google Cloud IAM mediante la misma interfaz `DataSource`.
  3. *Remediación guiada:* Permitir que la herramienta genere plantillas de corrección en código (como Terraform o AWS CLI) para que el administrador corrija las brechas con un solo comando.

---

## SECCIÓN 8. PREGUNTAS RÁPIDAS DE CONCEPTOS (GLOSARIO DEFENSIVO)

| Concepto | Definición Breve para Respuesta Rápida (15-20 segundos) |
| :--- | :--- |
| **IAM (Identity and Access Management)** | Servicio y marco de seguridad que administra de forma centralizada quién puede autenticarse (identidad) y qué autorizaciones específicas tiene sobre qué recursos informáticos. |
| **Boto3** | SDK oficial desarrollado por Amazon Web Services para Python que permite interactuar mediante código con todos los servicios y APIs de AWS. |
| **MFA (Multi-Factor Authentication)** | Mecanismo de autenticación robusto que exige al usuario presentar al menos dos factores probatorios distintos (algo que sabe, algo que tiene o algo que es) para acceder. |
| **MySQL Server e InnoDB** | Sistema gestor de bases de datos relacional y su motor de almacenamiento transaccional por defecto, que soporta operaciones ACID, claves foráneas y bloqueo a nivel de fila. |
| **API (Application Programming Interface)** | Conjunto formal de definiciones, contratos y protocolos que permiten que dos aplicaciones de software se comuniquen e intercambien datos entre sí de forma estandarizada. |
| **Rol de IAM (IAM Role)** | Identidad en AWS que no tiene credenciales permanentes (contraseña o claves fijas); es asumida temporalmente por usuarios, servicios o aplicaciones mediante tokens efímeros. |
| **Grupo de IAM (IAM Group)** | Colección lógica de usuarios utilizada para aplicar políticas de permisos comunes y simplificar la administración bajo el principio de menor privilegio. |
| **Políticas JSON de IAM** | Documentos formales en formato JSON que declaran explícitamente autorizaciones mediante bloques de efecto (`Allow` / `Deny`), acciones (`Action`), recursos (`Resource`) y condiciones (`Condition`). |
| **Principio de Menor Privilegio (PoLP)** | Principio fundamental de seguridad que establece que una identidad solo debe tener los permisos mínimos estrictamente necesarios para cumplir con sus funciones laborales, nada más. |
| **Auditoría de Seguridad** | Proceso sistemático, independiente y documentado para evaluar de forma objetiva si las configuraciones y controles de un sistema cumplen con los criterios de seguridad establecidos. |
| **Hallazgo de Auditoría** | Desviación técnica o no conformidad detectada al comparar el estado real de un recurso contra el criterio normativo o la línea base autorizada. |
| **Evidencia de Auditoría** | Registro factual, volcados técnicos, fechas o trazas JSON inmutables que respaldan y demuestran la existencia verídica de un hallazgo o evaluación. |
| **botocore.stub.Stubber** | Herramienta oficial de prueba del SDK de AWS que intercepta llamadas a la API y devuelve respuestas predefinidas sin emitir tráfico de red real ni requerir credenciales activas. |
| **Pytest** | Marco de trabajo líder en Python para la automatización, parametrización y ejecución estructurada de pruebas de software unitarias y de integración. |
| **Anexo A de ISO/IEC 27001** | Catálogo referencial de 93 controles de seguridad de la información agrupados en 4 categorías, diseñado para ser seleccionado y aplicado según la Declaración de Aplicabilidad (SoA). |

---

## SECCIÓN 9. SIMULACIÓN DE JURADO EVALUADOR (RONDAS DE ALTA PRESIÓN)

Esta sección simula tres rondas consecutivas de preguntas con distintos niveles de dificultad, diseñadas para que la autora practique la articulación verbal y el aplomo ante el jurado.

---

### RONDA 1: PREGUNTAS BÁSICAS Y DE APERTURA

#### Pregunta 1.1: *"Explíquenos de forma sencilla qué hace su software y en qué se diferencia de una auditoría tradicional."*
- **Respuesta modelo de la autora:**  
  *"Mi software es una herramienta de escritorio que se conecta a AWS IAM o a un simulador de datos, extrae las configuraciones de usuarios y roles, y las evalúa automáticamente frente a cuatro controles de seguridad basados en la norma ISO/IEC 27001. A diferencia de una auditoría manual tradicional —que consiste en que un auditor revise pantalla por pantalla en la consola web, tardando horas y anotando en hojas de texto—, este sistema realiza la evaluación en dos segundos, aplica las mismas reglas matemáticas sin sesgos humanos, guarda las evidencias en una base de datos MySQL relacional y genera reportes ejecutivos en PDF y Excel listos para la gerencia."*
- **¿Por qué esta respuesta convence al jurado?**  
  Porque es clara, directa, no utiliza tecnicismos innecesarios en la apertura y resalta los tres beneficios tangibles de la automatización: ahorro de tiempo, eliminación de errores humanos y entrega de reportes profesionales inmediatos.

#### Pregunta 1.2: *"¿Por qué eligió la norma ISO 27001 y no otro marco de seguridad como NIST o CIS Benchmarks?"*
- **Respuesta modelo de la autora:**  
  *"Elegí ISO/IEC 27001:2022 porque es el estándar internacional más reconocido a nivel global para la implementación de Sistemas de Gestión de Seguridad de la Información (SGSI) y representa el marco estratégico hacia el cual UPHARVEN C.A. busca orientar sus políticas corporativas. Aunque CIS y NIST ofrecen guías técnicas excelentes, ISO 27001 aporta el marco de gobernanza que permite vincular la configuración técnica de la nube directamente con los objetivos de negocio y la gestión de riesgos de la empresa."*
- **¿Por qué esta respuesta convence al jurado?**  
  Porque demuestra que la autora conoce otros estándares de la industria (NIST, CIS) pero justifica su elección en función del contexto estratégico de la organización objeto de estudio.

#### Pregunta 1.3: *"¿Qué es el estado 'No evaluable' y por qué no simplemente marcar todo como Conforme o Hallazgo?"*
- **Respuesta modelo de la autora:**  
  *"El estado 'No evaluable' es una decisión de ingeniería deliberada para evitar los 'falsos conformes'. En seguridad informática, asumir que un recurso cumple una norma simplemente porque la regla no aplica para su tipo es un grave peligro. Por ejemplo, los roles de IAM no inician sesión con contraseña ni tienen dispositivos MFA físicos; son identidades que asumen servicios. Si la regla de MFA los marcara como 'Conformes', estaríamos falseando las métricas hacia la gerencia; y si los marcara como 'Hallazgos', inundaríamos al auditor con falsas alarmas. 'No evaluable' refleja con rigor técnico que la regla no es aplicable a esa entidad."*
- **¿Por qué esta respuesta convence al jurado?**  
  Porque evidencia madurez metodológica en ciberseguridad, demostrando que el sistema fue diseñado con rigor analítico y no con una lógica binaria simplista de "todo bien o todo mal".

---

### RONDA 2: PREGUNTAS TÉCNICAS E INTERMEDIAS

#### Pregunta 2.1: *"Explíquenos la arquitectura del sistema. ¿Cómo se comunican la interfaz gráfica, el motor de auditoría y la base de datos?"*
- **Respuesta modelo de la autora:**  
  *"El sistema implementa una arquitectura en cuatro capas desacopladas mediante el principio de inversión de dependencias. En la capa superior tenemos la Presentación con PySide6, que solo conoce a la capa de Aplicación a través de la clase `AuditService`. Cuando el usuario hace clic en 'Ejecutar Auditoría', `AuditService` orquesta el flujo: primero le pide a la fuente de datos (`DataSource`) que obtenga los recursos; luego le entrega esos datos al `AuditEngine` en la capa de Dominio, el cual evalúa las cuatro reglas algorítmicas de forma polimórfica. Finalmente, el servicio invoca la capa de Infraestructura para persistir los resultados en MySQL de forma transaccional mediante `save_audit_run()`. La interfaz gráfica nunca toca directamente la base de datos ni conoce a AWS, lo que asegura que cualquier componente pueda modificarse o probarse sin romper el resto."*
- **¿Por qué esta respuesta convence al jurado?**  
  Porque describe con exactitud el patrón de capas, menciona nombres reales de clases (`AuditService`, `AuditEngine`, `DataSource`), demuestra dominio de patrones de software y evidencia que la autora comprende cómo fluyen los datos en su propio código.

#### Pregunta 2.2: *"En la base de datos, ¿cómo garantiza que una auditoría histórica conserve sus datos aunque cambien las reglas o los perfiles en el futuro?"*
- **Respuesta modelo de la autora:**  
  *"Lo garantizamos mediante dos mecanismos: el diseño relacional de claves naturales y el aislamiento transaccional. La tabla `audit_results` guarda el estado exacto de cada evaluación con una restricción UNIQUE compuesta por el ID de la auditoría, el recurso, la regla y el código del criterio. Además, la tabla `audit_evidence` almacena el volcado técnico inmutable que respaldó el resultado en ese momento específico. Como las auditorías históricas nunca se actualizan en MySQL y la capa de repositorio solo ejecuta consultas de lectura sobre ejecuciones pasadas, la información permanece como un registro inmutable y fiel de lo ocurrido en esa fecha."*
- **¿Por qué esta respuesta convence al jurado?**  
  Porque aborda un requisito crítico de la auditoría informática: la inmutabilidad de las evidencias y la trazabilidad histórica de los hallazgos.

#### Pregunta 2.3: *"Usted afirma que tiene 309 pruebas automatizadas. ¿Qué prueban exactamente y cómo sé que no son pruebas triviales que siempre pasan?"*
- **Respuesta modelo de la autora:**  
  *"Las 309 pruebas abarcan unitarias, de integración y end-to-end organizadas en 19 archivos en `tests/`. No son triviales porque validan casos límite y situaciones de fallo: por ejemplo, 44 pruebas utilizan `botocore.stub.Stubber` para simular respuestas erróneas de AWS como `AccessDenied` o respuestas paginadas con miles de tokens; 57 pruebas están dedicadas exclusivamente a verificar las 4 reglas inyectando políticas JSON con comodines maliciosos y fechas límite; y 66 pruebas validan que la interfaz gráfica no colapse al cambiar filtros o exportar documentos. Todas se ejecutan en 9,59 segundos mediante `pytest` con cero fallos y cero omisiones."*
- **¿Por qué esta respuesta convence al jurado?**  
  Porque da cifras precisas y verificables, menciona casos de fallo concretos (no solo casos de éxito) y demuestra que la suite de pruebas es un pilar real de calidad de ingeniería.

---

### RONDA 3: PREGUNTAS CRÍTICAS, DIFÍCILES Y DE ALTA PRESIÓN

#### Pregunta 3.1: *"Si una empresa ya tiene AWS IAM Access Analyzer y AWS Security Hub, ¿por qué gastaría tiempo instalando su software? ¿No está reinventando la rueda?"*
- **Respuesta modelo de la autora:**  
  *"No estoy reinventando la rueda porque el propósito y el alcance son completamente diferentes. AWS Security Hub e IAM Access Analyzer son herramientas excelentes de infraestructura en la nube, pero son genéricas y analizan principalmente la exposición externa de recursos o configuraciones estándar. Nuestro sistema resuelve tres problemas específicos que esas herramientas no cubren: primero, compara las identidades contra la **línea base personalizada de perfiles de cargo de UPHARVEN C.A.**; segundo, mapea los resultados directamente a la taxonomía de controles de **ISO/IEC 27001:2022**; y tercero, no genera costos mensuales recurrentes en dólares ni requiere exponer puertos, operando en la estación del auditor con almacenamiento en su propio servidor MySQL. Nuestro sistema no reemplaza a Security Hub; lo complementa en el plano de gobernanza y cumplimiento normativo local."*
- **¿Por qué esta respuesta convence al jurado?**  
  Porque no comete el error de desprestigiar las herramientas de AWS ni de afirmar falsamente que el prototipo las supera. Reconoce el valor de las herramientas nativas y delimita con precisión el nicho de valor del proyecto de tesis.

#### Pregunta 3.2: *"Usted no se conectó a una cuenta real de AWS de UPHARVEN ni tiene datos reales de empleados. ¿Cómo puede afirmar en su tesis que esto funciona para UPHARVEN C.A.?"*
- **Respuesta modelo de la autora:**  
  *"En la ingeniería de software aplicada a la seguridad de la información, solicitar credenciales con permisos de auditoría sobre la infraestructura productiva real de una empresa constituiría una vulneración a los principios éticos y de confidencialidad que la misma norma ISO 27001 exige. La metodología de ingeniería nos instruye a modelar: tomamos los requerimientos, los cargos y la estructura operativa de UPHARVEN C.A. y creamos un escenario de simulación fiel y determinista con 10 identidades. Paralelamente, implementamos el adaptador real de AWS con Boto3 y lo validamos contra las especificaciones oficiales de la API de AWS mediante `Stubber`. Por tanto, el sistema está completamente preparado para operar en UPHARVEN: el día en que la empresa configure sus credenciales de auditor, el adaptador Boto3 ejecutará las mismas consultas validadas sin necesidad de alterar una sola línea de código."*
- **¿Por qué esta respuesta convence al jurado?**  
  Porque convierte una supuesta debilidad en una fortaleza ética y metodológica. Demuestra madurez profesional al proteger la confidencialidad de la empresa y fundamenta la validez técnica en el desacoplamiento de la arquitectura.

#### Pregunta 3.3: *"En su simulación solo encontró 6 hallazgos sobre 67 evaluaciones. ¿No le parece que un 8,9% de hallazgos es una muestra muy pequeña para justificar toda una tesis de grado?"*
- **Respuesta modelo de la autora:**  
  *"Al contrario, ese 8,96% es exactamente lo que valida la robustez del modelo. En un entorno empresarial real, lo esperado no es que el 100% de los usuarios incumplan las normas, sino que la mayoría opere con normalidad mientras que brechas críticas específicas permanecen ocultas. Esos 6 hallazgos fueron inyectados deliberadamente para representar las fallas más comunes y graves en la nube: un usuario con permisos de superusuario por comodín `*`, un usuario sin MFA, una cuenta inactiva por 120 días, un rol con confianza indebida y dos discrepancias en grupos. El hecho de que el motor haya identificado los 6 hallazgos con 100% de precisión y clasificado correctamente los 36 conformes y los 25 no evaluables demuestra que el sistema tiene una alta especificidad y no produce falsas alarmas ni omisiones."*
- **¿Por qué esta respuesta convence al jurado?**  
  Porque demuestra comprensión profunda de la estadística aplicada a la ciberseguridad. En auditoría, una tasa moderada de hallazgos bien identificados demuestra calibración y precisión, refutando contundentemente la objeción del jurado.

---

## RESUMEN DE CIFRAS Y DATOS INMUTABLES PARA LA DEFENSA

Grábate estas cifras exactas para citarlas con seguridad ante cualquier pregunta cuantitativa:

- **309** pruebas automatizadas en `tests/` (100% aprobadas, 0 fallos, 0 omitidas, ~9.6 segundos de tiempo de ejecución).
- **19** archivos de pruebas automatizadas.
- **10** tablas relacionales en MySQL Server con motor InnoDB y soporte transaccional.
- **4** controles de seguridad implementados de ISO/IEC 27001:2022 (A.5.15, A.5.16, A.5.18, A.8.5).
- **10** recursos evaluados en el simulador (7 usuarios IAM y 3 roles IAM).
- **67** evaluaciones granulares totales generadas en la corrida simulada.
- **36** resultados Conforme (53,73%).
- **25** resultados No evaluable (37,31%).
- **6** hallazgos detectados (8,96%).
- **17** operaciones de Boto3 IAM consumidas por el adaptador (todas de solo lectura `get_*` y `list_*`).
- **19** operaciones registradas formalmente en la tupla defensiva `READ_ONLY_OPERATIONS`.
- **4** formatos de entrega y visualización: Interfaz gráfica PySide6, PDF ejecutivo (ReportLab), Excel tabular (OpenPyXL) y CSV estructurado.

