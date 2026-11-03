# MANUAL DE USUARIO
## Sistema Automatizado de Auditoría IAM — ISO/IEC 27001:2022

**Proyecto de Grado:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.  
**Destinatarios:** Auditores de Seguridad, Oficiales de Seguridad de la Información (CISO), Administradores de Sistemas y Evaluadores  
**Versión del Sistema:** 1.0.0  
**Fecha de Publicación:** Noviembre 2026  

---

## ÍNDICE GENERAL

1. [Portada e Información del Documento](#1-portada-e-información-del-documento)
2. [Introducción y Descripción General del Sistema](#2-introducción-y-descripción-general-del-sistema)
3. [Requisitos para Utilizar el Sistema](#3-requisitos-para-utilizar-el-sistema)
4. [Inicio de la Aplicación](#4-inicio-de-la-aplicación)
5. [Descripción de la Interfaz y Navegación](#5-descripción-de-la-interfaz-y-navegación)
6. [Panel Principal (Dashboard)](#6-panel-principal-dashboard)
7. [Ejecución de Auditorías Paso a Paso](#7-ejecución-de-auditorías-paso-a-paso)
8. [Consulta y Filtrado de Resultados](#8-consulta-y-filtrado-de-resultados)
9. [Historial de Auditorías y Trazabilidad](#9-historial-de-auditorías-y-trazabilidad)
10. [Exportación de Informes (PDF, Excel y CSV)](#10-exportación-de-informes-pdf-excel-y-csv)
11. [Módulo de Configuración](#11-módulo-de-configuración)
12. [Interpretación de Resultados y Toma de Decisiones](#12-interpretación-de-resultados-y-toma-de-decisiones)
13. [Solución de Problemas Frecuentes](#13-solución-de-problemas-frecuentes)
14. [Recomendaciones de Uso y Seguridad](#14-recomendaciones-de-uso-y-seguridad)
15. [Glosario de Términos para el Usuario](#15-glosario-de-términos-para-el-usuario)

---

## 1. PORTADA E INFORMACIÓN DEL DOCUMENTO

- **Nombre Institucional del Proyecto:**  
  *Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.*
- **Título del Documento:**  
  *Manual de Usuario — Operación y Manejo de la Aplicación de Escritorio de Auditoría IAM*
- **Organización de Referencia:** UPHARVEN C.A.
- **Entorno Operativo:** Aplicación de escritorio nativa multiplataforma (Windows / Linux / macOS) desarrollada en Python y PySide6.

---

## 2. INTRODUCCIÓN Y DESCRIPCIÓN GENERAL DEL SISTEMA

### 2.1. Propósito de este Manual
Este manual tiene como objetivo guiar de manera práctica, ordenada y no técnica a los usuarios que interactuarán con la aplicación de escritorio. Proporciona instrucciones detalladas para abrir el sistema, iniciar auditorías, interpretar indicadores cuantitativos, analizar hallazgos de seguridad y exportar informes ejecutivos.

### 2.2. ¿Qué es el Sistema de Auditoría IAM?
Es una herramienta informática diseñada para auditar de forma automatizada las configuraciones de seguridad de cuentas, usuarios y roles en Amazon Web Services (AWS IAM). El sistema compara dichas configuraciones contra las directrices de cuatro controles fundamentales de seguridad establecidos en la norma internacional **ISO/IEC 27001:2022**:
1. **Control 5.15 (Control de acceso):** Verifica que los usuarios pertenezcan a los grupos correctos y que los roles solo admitan entidades de confianza autorizadas.
2. **Control 5.16 (Gestión de identidades):** Detecta cuentas inactivas o credenciales que superan el umbral de 90 días sin uso.
3. **Control 5.18 (Derechos de acceso):** Examina las políticas de permisos para evitar accesos administrativos ilimitados o comodines globales (`*`).
4. **Control 8.5 (Autenticación segura):** Comprueba que los usuarios tengan activado obligatoriamente un segundo factor de autenticación (MFA).

### 2.3. Modalidades de Operación
La aplicación ofrece dos modalidades claramente diferenciadas:
- **Modo Simulador de Datos Local:** Utiliza datos de prueba controlados generados en memoria. No necesita Internet, no utiliza credenciales de AWS y permite realizar demostraciones inmediatas y seguras.
- **Modo AWS IAM Cloud:** Se conecta a través de Internet a una cuenta real de Amazon Web Services mediante el SDK Boto3 para auditar recursos reales en modo estricto de solo lectura (sin modificar ni eliminar nada).

> **Aviso Importante:** Los resultados generados en el *Modo Simulador* son **completamente ficticios** y fueron diseñados con fines didácticos y de verificación; no reflejan la infraestructura real de UPHARVEN C.A. Asimismo, el sistema es una herramienta de **diagnóstico técnico de apoyo** y no emite un certificado oficial de cumplimiento ISO/IEC 27001.

---

## 3. REQUISITOS PARA UTILIZAR EL SISTEMA

Para utilizar la aplicación en su estación de trabajo, verifique contar con los siguientes elementos:

1. **Equipo y Sistema Operativo:** Computador con Windows 10/11 (64-bit), Linux o macOS.
2. **Resolución de Pantalla:** Mínima recomendada de 1280 × 720 píxeles.
3. **Servidor de Base de Datos MySQL:** MySQL Server (versión 8.0 o 9.6) en ejecución, con la base de datos `auditoria_iam_upharven` configurada.
4. **Archivo de Configuración `.env`:** Archivo ubicado en la carpeta del programa con los datos de acceso a MySQL (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`).
5. **Conectividad a Internet (Opcional):**
   - **No requerida** para operar con el *Simulador Local*.
   - **Requerida obligatoriamente** si va a auditar cuentas de *AWS IAM*, además de disponer de credenciales válidas de AWS (`Access Key` y `Secret Key`) con permisos de lectura.

---

## 4. INICIO DE LA APLICACIÓN

Para abrir el sistema, siga estos sencillos pasos desde la consola de Windows PowerShell:

### Paso 1: Abrir la terminal
Haga clic en el menú Inicio, escriba `PowerShell` y abra la aplicación.

### Paso 2: Dirigirse a la carpeta del sistema
Escriba el siguiente comando y presione `Enter`:
```powershell
cd c:\Users\andre\Desktop\TESIS\sistema
```

### Paso 3: Activar el entorno de trabajo
Ejecute el siguiente comando para activar el entorno de dependencias:
```powershell
.\.venv\Scripts\Activate.ps1
```
*(Observará que al inicio de la línea de comandos aparece el prefijo `(.venv)`).*

### Paso 4: Iniciar la aplicación
Escriba y presione `Enter`:
```powershell
python main.py
```

### Resultado Esperado
En pocos segundos se abrirá la ventana principal del sistema titulada **“Sistema de Auditoría IAM”** con dimensiones de 1200 × 750 píxeles y el tema visual oscuro (*Cyber Security Theme*).

---

## 5. DESCRIPCIÓN DE LA INTERFAZ Y NAVEGACIÓN

La aplicación está diseñada para ser intuitiva y cuenta con dos zonas claramente definidas:

### 5.1. Barra Lateral de Navegación (Izquierda)
Ubicada en el costado izquierdo, contiene el identificador institucional:
- **AUDITORÍA IAM**
- **UPHARVEN C.A. • ISO 27001**

Debajo se presentan cinco botones de acceso directo correspondientes a las vistas del sistema:
1. **Inicio:** Accede al panel principal con tarjetas de indicadores ejecutivos, gráficos y catálogo de controles.
2. **Ejecutar auditoría:** Permite seleccionar la fuente de datos y lanzar una evaluación técnica.
3. **Resultados:** Muestra la tabla detallada de evaluaciones de la auditoría actual con filtros de búsqueda y opciones de exportación.
4. **Historial:** Presenta la bitácora cronológica de auditorías guardadas en la base de datos MySQL.
5. **Configuración:** Muestra los parámetros de conexión y umbrales operativos del sistema en modo demostrativo.

### 5.2. Área Central de Contenido (Derecha)
Es el espacio dinámico donde se visualiza la información de la sección activa. Al hacer clic en cualquier botón de la barra lateral, la pantalla conmuta instantáneamente sin abrir ventanas adicionales ni recargar el programa.

---

## 6. PANEL PRINCIPAL (DASHBOARD)

Al iniciar el sistema o pulsar el botón **“Inicio”**, se presenta el Dashboard ejecutivo. Su propósito es brindar un resumen gráfico inmediato del estado de cumplimiento de la última auditoría realizada.

### 6.1. Tarjetas de Indicadores Clave (KPIs)
En la parte superior se exhiben cuatro tarjetas con contadores destacados:
- **TOTAL EVALUACIONES:** Número total de verificaciones técnicas individuales ejecutadas sobre los recursos auditados.
- **CONFORME (Color Verde):** Cantidad y porcentaje de verificaciones que cumplen satisfactoriamente los requisitos de la norma.
- **HALLAZGO (Color Rojo/Naranja):** Cantidad y porcentaje de desviaciones, debilidades o configuraciones de riesgo detectadas.
- **NO EVALUABLE (Color Gris):** Evaluaciones que no pudieron completarse por falta de información o políticas inaccesibles.

### 6.2. Gráfico Circular de Cumplimiento
En el cuadrante central derecho se muestra un gráfico circular interactivo (*Pie Chart*) que ilustra la proporción visual entre evaluaciones Conformes, Hallazgos y No Evaluables, facilitando la presentación ejecutiva ante directivos.

### 6.3. Tarjeta de Última Auditoría
Muestra el identificador único (`ID`), la fecha y hora exacta de la última corrida, el origen evaluado (*Simulador* o *AWS IAM*) y el porcentaje global de conformidad alcanzado.

### 6.4. Resumen por Regla ISO/IEC 27001
Presenta barras horizontales con el porcentaje individual de cumplimiento para cada uno de los cuatro controles técnicos evaluados:
- **IAM-001 (Control 5.15):** Control de acceso.
- **IAM-002 (Control 5.16):** Gestión de identidades.
- **IAM-003 (Control 5.18):** Derechos de acceso.
- **IAM-004 (Control 8.5):** Autenticación segura.

### 6.5. Catálogo Interactivo de Controles y Enlace a la Norma
En la sección inferior encontrará cuatro tarjetas informativas. Al hacer clic en **“Ver detalle del control →”**, se abre un diálogo modal que explica:
- El objetivo formal de seguridad según el estándar internacional.
- Qué aspectos técnicos de AWS IAM revisa el sistema.
- Criterios de evaluación y significado de los estados.
- Las delimitaciones de alcance técnico.

En la cabecera del panel encontrará el botón: **“Consultar norma ISO/IEC 27001:2022 (Internet Archive) ↗”**, el cual abre en su navegador web predeterminado la versión oficial de acceso público de la norma.

---

## 7. EJECUCIÓN DE AUDITORÍAS PASO A PASO

Para ejecutar una nueva auditoría técnica automatizada, siga estos pasos:

### Paso 1: Ir a la pantalla de ejecución
Haga clic en la opción **“Ejecutar auditoría”** del menú lateral izquierdo.

### Paso 2: Seleccionar la fuente de información
Ubique el selector desplegable **“Fuente de Información”** y elija una de las dos opciones:
1. **Simulador de Datos Local (Fase 4 - Entrega 1):** Selecciónela para demostraciones, capacitaciones o pruebas sin conexión a Internet.
2. **Adaptador AWS IAM Cloud - Boto3 (Fase 4 - Entrega 2):** Selecciónela para auditar una cuenta real de AWS conectada mediante Internet.

### Paso 3: Iniciar el proceso
Haga clic en el botón azul **“Ejecutar auditoría”**.

### Qué sucede durante la ejecución:
- El botón se desactiva temporalmente para evitar ejecuciones duplicadas.
- El panel de estado mostrará un mensaje informativo con fondo azul:  
  *“⏳ Ejecutando auditoría técnica... Procesando identidades, grupos, roles y políticas JSON frente a las reglas IAM-001, IAM-002, IAM-003 e IAM-004...”*
- El motor algorítmico evalúa todas las identidades en pocos segundos.

### Paso 4: Revisar el resumen de finalización
Al concluir con éxito, el recuadro de estado cambiará a color verde mostrando:
- Confirmación de éxito (*“✓ Auditoría finalizada correctamente”*).
- Desglose cuantitativo (Total de evaluaciones, Conforme, Hallazgo, No evaluable).
- Mensaje de confirmación de guardado en la base de datos MySQL con el identificador asignado.
- Se hace visible el botón azul claro: **“Ver resultados detallados →”**.

### Paso 5: Ir a los resultados
Haga clic en **“Ver resultados detallados →”** para examinar el informe exhaustivo en la pestaña de Resultados.

---

## 8. CONSULTA Y FILTRADO DE RESULTADOS

La vista **“Resultados”** presenta el desglose pormenorizado de cada verificación realizada sobre cada recurso.

### 8.1. Columnas de la Tabla de Resultados
- **Recurso:** Nombre o identificador técnico de la identidad evaluada (ej. `ana.operaciones`, `carlos.soporte`, `rol.ec2.operaciones`).
- **Tipo:** Naturaleza del recurso (`IAM_USER` para usuarios humanos o `IAM_ROLE` para roles de servicio).
- **Regla:** Código interno de la regla aplicada (`IAM-001`, `IAM-002`, `IAM-003`, `IAM-004`).
- **Control ISO:** Identificador del control correspondiente en ISO/IEC 27001:2022 (`5.15`, `5.16`, `5.18`, `8.5`).
- **Criterio:** Código técnico del subcriterio auditado (ej. `C15-01`, `C18-01`, `C85-01`).
- **Estado:** Veredicto emitido por el sistema, identificado por colores:
  - **Verde:** `Conforme`.
  - **Rojo:** `Hallazgo`.
  - **Gris:** `No evaluable`.
- **Justificación:** Explicación técnica y objetiva que fundamenta por qué el recurso obtuvo esa calificación.

### 8.2. Uso de la Barra de Filtros
Para facilitar el análisis cuando existen decenas de evaluaciones, utilice los filtros ubicados sobre la tabla:
1. **Filtro por Regla:** Haga clic en el selector *“Filtrar por regla”* para aislar un control específico (ej. seleccionar únicamente `IAM-004 (8.5)` para ver únicamente el estado de autenticación MFA).
2. **Filtro por Estado:** Haga clic en el selector *“Filtrar por estado”* para concentrarse en situaciones críticas (ej. seleccionar `Hallazgo` para ver exclusivamente las desviaciones que requieren atención).

Los filtros actúan de forma instantánea y combinada sin necesidad de pulsar botones adicionales de búsqueda.

---

## 9. HISTORIAL DE AUDITORÍAS Y TRAZABILIDAD

Haga clic en la pestaña **“Historial”** del menú lateral para consultar las auditorías realizadas con anterioridad.

### 9.1. Bitácora de Auditorías Guardadas
La tabla de historial muestra cronológicamente las auditorías persistidas en MySQL:
- **ID:** Número de identificación único de la corrida.
- **Fecha y Hora:** Marca temporal exacta en que se ejecutó la evaluación.
- **Origen:** Fuente de datos empleada (`simulacion` o `aws`).
- **Estado:** Condición del proceso (`completada`).
- **Hallazgos:** Número total de problemas detectados en esa auditoría.
- **Resumen:** Conteo sintético de evaluaciones Conformes, Hallazgos y No Evaluables.

### 9.2. Recuperar y Visualizar una Corrida Pasada
1. Haga un clic sobre la fila de la auditoría que desea inspeccionar en la tabla de historial.
2. Haga clic en el botón **“Ver resultados de auditoría”** ubicado en la barra superior.
3. El sistema consultará automáticamente la base de datos MySQL, reconstruirá los resultados y transferirá la vista a la pestaña **“Resultados”**, permitiéndole navegar y filtrar esa auditoría histórica como si la acabara de ejecutar.

### 9.3. Botón Actualizar
Si se han ejecutado nuevas auditorías recientemente o desde otra terminal, pulse el botón **“Actualizar historial 🔄”** para refrescar la lista.

---

## 10. EXPORTACIÓN DE INFORMES (PDF, EXCEL Y CSV)

El sistema permite generar informes profesionales e independientes para ser entregados a la gerencia, auditores externos o equipos de tecnología. Puede exportar informes tanto desde la pestaña **Resultados** como desde la pestaña **Historial**.

### 10.1. Exportación a PDF (Informe Ejecutivo)
1. Pulse el botón **“Exportar PDF”**.
2. Se abrirá una ventana de diálogo para seleccionar la carpeta donde desea guardar el archivo y asignarle un nombre (por defecto sugiere un nombre con la fecha y hora, por ejemplo: `informe_auditoria_20261102.pdf`).
3. Haga clic en **“Guardar”**.
4. **Contenido del PDF generado:**
   - Portada corporativa con el título institucional de UPHARVEN C.A.
   - Resumen ejecutivo con gráfico circular vectorial de cumplimiento.
   - Tablas consolidadas de resultados por cada control ISO.
   - Inventario detallado de hallazgos con severidad y recomendaciones técnicas de solución.
   - Registro de evidencias técnicas asociadas.
   - Cláusula de descargo de responsabilidad y delimitación técnica.
   - Numeración dinámica formal en todas las páginas (*"Página X de Y"*).

### 10.2. Exportación a Microsoft Excel (Libro XLSX)
1. Pulse el botón **“Exportar Excel”**.
2. Seleccione la ruta y guarde el archivo `.xlsx`.
3. **Estructura del libro Excel:**
   El archivo contiene **cuatro hojas de trabajo** estructuradas:
   - **`Resumen`:** Tarjetas de métricas, datos de la corrida y porcentajes.
   - **`Evaluaciones`:** Tabla completa de todas las evaluaciones con autofiltros de Excel activados y celdas coloreadas según el estado.
   - **`Hallazgos`:** Lista filtrada únicamente con los incumplimientos para seguimiento del equipo de soporte.
   - **`Evidencias`:** Trazas técnicas y referencias de soporte.

### 10.3. Exportación a CSV (Datos Tabulares Planos)
1. Pulse el botón **“Exportar CSV”**.
2. Guarde el archivo `.csv`.
3. **Compatibilidad:** El archivo se genera con codificación `UTF-8 con BOM` (`utf-8-sig`), lo que garantiza que pueda abrirse directamente con doble clic en Microsoft Excel en Windows sin que las tildes o caracteres en español se deformen.

---

## 11. MÓDULO DE CONFIGURACIÓN

Al pulsar la pestaña **“Configuración”** en la barra lateral, accederá a la vista de parámetros operativos.

### 11.1. Información Mostrada en Pantalla
La pantalla organiza los parámetros del sistema en bloques informativos:
1. **Parámetros de Base de Datos:** Servidor host, puerto de escucha, nombre de base de datos y usuario configurado.
2. **Parámetros de Conexión AWS:** Región por defecto configurada y estado del proveedor de credenciales.
3. **Parámetros de Evaluación:** Umbral operativo de inactividad de cuentas (configurado en **90 días**).

### 11.2. Modo Demostrativo y Protección de Seguridad
En la parte superior de la vista se presenta un banner informativo azul claro:
> *“ℹ En esta entrega estructural, los controles de configuración se presentan en modo demostrativo y no modifican el archivo .env, la base de datos ni credenciales del sistema.”*

**Por qué funciona de esta manera:**  
Para garantizar la máxima seguridad y evitar la exposición o sobreescritura accidental de contraseñas de red o claves de nube, el sistema bloquea cualquier intento de mutar el archivo de configuración `.env` desde la interfaz de usuario. Cualquier cambio de contraseñas de MySQL debe ser efectuado directamente en el archivo `.env` en el servidor por un administrador autorizado.

---

## 12. INTERPRETACIÓN DE RESULTADOS Y TOMA DE DECISIONES

Como usuario u operador del sistema, es crucial saber interpretar los veredictos y aplicar el criterio profesional antes de emprender acciones correctivas:

### 12.1. ¿Cómo Interpretar un "Hallazgo"?
Un estado de **Hallazgo** señala que una configuración técnica se aparta de la buena práctica de seguridad o del perfil autorizado. Sin embargo:
- **Requiere validación humana:** Antes de desactivar un usuario o eliminar una política en AWS, el auditor debe confirmar con el área de Talento Humano o el líder del proyecto si la identidad corresponde a un servicio activo o a una excepción justificada de negocio.
- **Revisar la recomendación:** Cada hallazgo en el reporte PDF y Excel incluye una recomendación orientativa (por ejemplo: *"Exigir enrolamiento mandatorio de MFA antes del próximo inicio de sesión"*).

### 12.2. ¿Cómo Interpretar un estado "No Evaluable"?
El estado **No evaluable** **no significa que el recurso sea vulnerable, pero tampoco garantiza que sea seguro**. Indica que el sistema no contó con datos suficientes para certificar su conformidad.
- *Ejemplo común:* Si un rol de AWS no tiene asignado un perfil de acceso formal en la base de datos MySQL, el sistema no puede adivinar qué entidades deberían tener permiso para asumirlo; por lo tanto, declara `No evaluable`.
- *Acción recomendada:* Registrar el perfil correspondiente en el catálogo de MySQL para que en la próxima auditoría pueda ser calificado como Conforme o Hallazgo.

---

## 13. SOLUCIÓN DE PROBLEMAS FRECUENTES

A continuación se describen los mensajes de error más comunes y las acciones recomendadas para resolverlos:

| Situación o Mensaje de Error | Causa Probable | Acción Recomendada |
| :--- | :--- | :--- |
| **"Error al conectar con la base de datos MySQL en localhost:3306..."** | El servicio de MySQL Server está detenido o la contraseña en `.env` es incorrecta. | 1. Verifique en los servicios de Windows (`services.msc`) que el servicio MySQL esté iniciado.<br>2. Verifique que las credenciales en el archivo `.env` coincidan con su usuario local de MySQL. |
| **"❌ Error de autenticación en AWS: The security token included in the request is invalid"** | Las credenciales de AWS no están configuradas o caducaron. | Configure sus credenciales de AWS mediante las variables de entorno estándar `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY` o mediante el comando `aws configure` en la consola. |
| **"❌ Permisos insuficientes en AWS IAM: AccessDenied"** | El usuario de AWS utilizado no tiene permisos suficientes para leer la configuración. | Asegúrese de que las credenciales de AWS tengan asignada la política administrada `IAMReadOnlyAccess` o permisos equivalentes de consulta (`iam:List*` e `iam:Get*`). |
| **"❌ Error de conexión con AWS IAM"** | Fallo de conexión a Internet o resolución DNS. | Compruebe que su computador tenga salida activa a Internet y que no exista un firewall o proxy bloqueando el dominio `iam.amazonaws.com`. |
| **La tabla de Historial aparece vacía** | Aún no se han ejecutado auditorías con persistencia o la base de datos se inicializó recientemente. | Ejecute una nueva auditoría desde la sección *“Ejecutar auditoría”*; al finalizar con éxito, el registro aparecerá automáticamente en el Historial. |

---

## 14. RECOMENDACIONES DE USO Y SEGURIDAD

Para un uso óptimo y seguro del sistema de auditoría, tenga en cuenta las siguientes recomendaciones:

1. **Uso de Cuentas de Solo Lectura:** Para auditar cuentas reales de AWS IAM, cree y utilice exclusivamente usuarios o roles que posean la política `IAMReadOnlyAccess`. **Nunca utilice las credenciales de la cuenta raíz (Root Account)** ni credenciales con privilegios de administrador para realizar auditorías.
2. **Protección del Archivo `.env`:** El archivo `.env` contiene datos de conexión a su base de datos. Manténgalo protegido con permisos de lectura restringidos en su sistema operativo y nunca lo envíe por correo electrónico ni lo publique en repositorios abiertos.
3. **Respaldo Periódico de la Base de Datos:** Realice respaldos regulares (*backups*) de su base de datos MySQL `auditoria_iam_upharven` mediante `mysqldump` para conservar la trazabilidad histórica de todas las auditorías realizadas.
4. **Validación de Datos del Simulador:** Al presentar informes generados en el *Modo Simulador*, informe siempre a su audiencia que se trata de un escenario sintético de demostración académica y no de una auditoría sobre la infraestructura real de UPHARVEN C.A.

---

## 15. GLOSARIO DE TÉRMINOS PARA EL USUARIO

- **Auditoría IAM:** Examen técnico y metódico de las identidades, credenciales y permisos de acceso configurados en una organización para verificar que cumplan con las políticas de seguridad.
- **AWS IAM:** Servicio de Amazon Web Services que permite gestionar de forma centralizada usuarios, grupos, roles y permisos de acceso en la nube.
- **Conforme:** Estado de una evaluación que indica que la configuración técnica cumple con los requisitos del estándar de seguridad evaluado.
- **Control de Seguridad:** Medida, política o salvaguarda técnica diseñada para proteger la confidencialidad, integridad y disponibilidad de la información según la norma ISO/IEC 27001.
- **Dashboard:** Panel visual interactivo que resume mediante gráficos e indicadores ejecutivos el estado general de una auditoría.
- **Evidencia:** Información técnica verificable (volcados JSON, listas de grupos, fechas de acceso) que respalda y demuestra la validez de un veredicto de auditoría.
- **Grupo de IAM:** Colección de usuarios de AWS IAM a los que se les aplican permisos comunes de manera simultánea.
- **Hallazgo:** Desviación técnica o vulnerabilidad detectada que representa un riesgo para la seguridad y requiere corrección.
- **MFA (Autenticación Multifactor):** Mecanismo de seguridad que exige presentar dos o más pruebas de identidad independientes (por ejemplo, contraseña más un código numérico generado en el teléfono móvil) para iniciar sesión.
- **No Evaluable:** Calificación técnica que previene falsos conformes cuando no se dispone de datos suficientes para certificar la seguridad de una identidad.
- **Política de IAM (Policy):** Documento formal en formato JSON que especifica exactamente qué acciones tiene permitido o prohibido realizar un usuario o rol en AWS.
- **Principio de Menor Privilegio:** Principio de ciberseguridad que establece que a cada usuario o servicio solo se le deben otorgar los permisos estrictamente indispensables para desempeñar sus funciones laborales, ni uno más.
- **Rol de IAM:** Identidad técnica en AWS diseñada para ser asumida temporalmente por aplicaciones o servicios (como máquinas virtuales EC2 o funciones Lambda) sin necesidad de compartir contraseñas permanentes.
- **Simulador:** Módulo del sistema que genera identidades ficticias controladas para demostrar el funcionamiento del motor sin requerir conexión a AWS.

