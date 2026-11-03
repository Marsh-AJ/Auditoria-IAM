# GUÍA DE DEMOSTRACIÓN ACADÉMICA Y DEFENSA DEL SISTEMA
## Sistema Automatizado de Auditoría IAM — ISO/IEC 27001:2022
**Proyecto de Grado:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.  
**Destinatarios:** Tesistas, Jurado Calificador y Evaluadores Técnicos  
**Fecha:** Noviembre 2026  

---

## INTRODUCCIÓN Y OBJETIVO DE LA GUÍA

Esta guía describe el recorrido práctico y la secuencia recomendada para realizar la demostración funcional del sistema durante la predefensa y defensa formal de tesis. 

El objetivo es guiar al expositor paso a paso a través de las pantallas, funcionalidades y criterios técnicos implementados en la aplicación de escritorio (`PySide6`), demostrando el cumplimiento riguroso de los objetivos de investigación planteados.

---

## 1. PREPARACIÓN PREVIA DEL ENTORNO DE DEMOSTRACIÓN

Antes de iniciar la presentación ante el jurado, verifique que los siguientes componentes se encuentren operativos:

1. **Terminal:** Abra Windows PowerShell en el directorio raíz del proyecto (`c:\Users\andre\Desktop\TESIS\sistema`).
2. **Entorno Virtual Activo:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
3. **Servicio MySQL:** Asegúrese de que el servicio MySQL Server esté iniciado y que la base de datos `auditoria_iam_upharven` haya sido creada con el script `init_database_upharven.sql`.
4. **Archivo de Configuración:** Confirme que el archivo `.env` exista en la raíz con las credenciales locales correctas de MySQL.
5. **Verificación Previa Silenciosa:** Si desea validar rápidamente que todo está en orden antes de encender el proyector, ejecute:
   ```powershell
   .\.venv\Scripts\pytest.exe -q
   ```
   Debe reportar `309 passed`.

---

## 2. INICIO DE LA APLICACIÓN

Inicie la aplicación ejecutando en la consola:
```powershell
python main.py
```

**Qué señalar al jurado:**
- La aplicación es un software de escritorio nativo desarrollado con **Python 3.13** y **PySide6 (Qt 6)**.
- Presenta una interfaz moderna con temática ergonómica de ciberseguridad (*slate/navy*), diseñada para operadores y auditores de seguridad de la información.
- En el panel lateral izquierdo se observa la identidad institucional: **“AUDITORÍA IAM — UPHARVEN C.A. • ISO 27001”** y la barra de navegación persistente con cinco secciones: *Inicio*, *Ejecutar auditoría*, *Resultados*, *Historial* y *Configuración*.

---

## 3. EXPLICACIÓN DEL DASHBOARD EJECUTIVO (VISTA INICIO)

Al iniciar la aplicación, la pantalla predeterminada es la pestaña **Inicio** (`HomePage`).

**Qué mostrar y explicar:**
1. **Tarjetas de Métricas Ejecutivas (KPIs):**
   - **Total Evaluaciones:** Número total de verificaciones individuales aplicadas en la última auditoría.
   - **Conforme:** Evaluaciones que satisfacen plenamente los criterios del estándar ISO.
   - **Hallazgo:** Desviaciones o vulnerabilidades que requieren atención o remediación.
   - **No Evaluable:** Evaluaciones donde los datos eran incompletos, ausentes o no aplicables (principio de prevención de falsos conformes).
2. **Gráfico Circular Interactivo:**
   - Renderizado dinámicamente mediante `QtCharts` (`QPieSeries`).
   - Representa visualmente la proporción porcentual de cumplimiento de la última auditoría.
3. **Tarjeta de Estado de la Última Auditoría:**
   - Muestra el identificador de la corrida, la fecha/hora de ejecución, el tipo de fuente evaluada (`Simulación` o `AWS IAM`) y el porcentaje global de conformidad.
4. **Resumen por Regla ISO:**
   - Desglosa el cumplimiento individual para los cuatro controles: 5.15, 5.16, 5.18 y 8.5.

---

## 4. SELECCIÓN DE LA FUENTE DE DATOS: EL SIMULADOR LOCAL

Haga clic en el botón **“Ejecutar auditoría”** del menú lateral izquierdo (o en el botón de acción rápida del Dashboard).

**Qué mostrar y explicar:**
1. En la página de configuración se visualiza el menú desplegable **“Fuente de Información”**.
2. Despliegue las dos opciones:
   - *Simulador de Datos Local (Fase 4 - Entrega 1)*.
   - *Adaptador AWS IAM Cloud - Boto3 (Fase 4 - Entrega 2)*.
3. Seleccione **“Simulador de Datos Local”**.
4. **Fundamento técnico:** Aclare al jurado que el simulador local genera un conjunto de datos sintético determinista compuesto por **10 identidades (6 usuarios y 4 roles)**. Este modo permite ejecutar demostraciones completas, robustas y reproducibles sin depender de conexión a Internet ni de credenciales vivas de AWS.

---

## 5. EJECUCIÓN DE UNA AUDITORÍA AUTOMATIZADA

Con la fuente `Simulador de Datos Local` seleccionada, pulse el botón azul:  
**“Ejecutar auditoría”**

**Qué observar durante la ejecución:**
1. El botón se deshabilita preventivamente para evitar concurrencia accidental.
2. El mensaje de estado cambia a un indicador dinámico: *“⏳ Ejecutando auditoría técnica... Procesando identidades...”*.
3. La interfaz procesa eventos en tiempo real (`QApplication.processEvents()`) manteniendo la ventana responsiva.
4. En cuestión de segundos, la ejecución concluye y el bloque de estado se ilumina en color verde:
   - *✓ Auditoría finalizada correctamente (Simulador Local).*
   - *• Total de evaluaciones: 67*
   - *• Conforme: 40*
   - *• Hallazgo: 15*
   - *• No evaluable: 12*
   - Muestra la confirmación de persistencia transaccional en MySQL Server con el `audit_run_id` generado.
5. Aparece el botón de navegación directa: **“Ver resultados detallados →”**. Pulse dicho botón.

---

## 6. INTERPRETACIÓN DE LA VISTA DE RESULTADOS

Al pulsar el botón o seleccionar la pestaña **“Resultados”**, se despliega la tabla analítica completa.

**Qué mostrar y explicar:**
1. **Tarjetas de Resumen Cuantitativo Superior:**
   - Confirman las 67 evaluaciones con sus respectivos contadores.
2. **Barra de Filtros Reactivos:**
   - **Filtro por Regla:** Permite aislar los resultados de una regla específica (`IAM-001`, `IAM-002`, `IAM-003` o `IAM-004`).
   - **Filtro por Estado:** Permite ver únicamente las evaluaciones en estado `Conforme`, `Hallazgo` o `No evaluable`.
3. **Columnas de la Tabla de Resultados:**
   - `Recurso`: Identidad evaluada (ej. `ana.operaciones`, `carlos.soporte`, `rol.ec2.operaciones`).
   - `Tipo`: Tipo técnico (`IAM_USER` o `IAM_ROLE`).
   - `Regla`: Código de regla (`IAM-001` a `IAM-004`).
   - `Control ISO`: Identificador del control (`5.15`, `5.16`, `5.18`, `8.5`).
   - `Criterio`: Subcriterio normativo auditado (ej. `C15-01`, `C18-01`, `C85-01`).
   - `Estado`: Etiqueta cromática (Verde = Conforme, Rojo/Naranja = Hallazgo, Gris = No evaluable).
   - `Justificación`: Argumento técnico objetivo que fundamenta el veredicto algorítmico.

---

## 7. EXPLICACIÓN DE LOS TRES ESTADOS DE EVALUACIÓN

El jurado valorará especialmente el rigor metodológico en la clasificación de los resultados:

| Estado | Significado Técnico y Metodológico |
| :---: | :--- |
| **Conforme** | La configuración auditada satisface plenamente el criterio normativo de seguridad ISO/IEC 27001:2022 y coincide con el perfil de acceso autorizado. |
| **Hallazgo** | Se constata una desviación técnica, vulnerabilidad o exceso de privilegios que vulnera el principio de menor privilegio o el control evaluado. |
| **No Evaluable** | **Principio de prevención de falsos conformes:** Cuando los metadatos son incompletos, la política no es accesible o la identidad carece de un perfil de referencia activo, el motor **nunca asume conformidad**. Registra justificadamente `No evaluable` para advertir al auditor que se requieren datos complementarios. |

---

## 8. EJEMPLO EN VIVO DE UN HALLAZGO GENERADO POR EL SIMULADOR

En la tabla de resultados, filtre por **Estado = “Hallazgo”** y seleccione uno de los siguientes casos para explicar la lógica algorítmica:

- **Ejemplo 1 (IAM-004 / Control 8.5 — Autenticación Segura):**
  - *Recurso:* `cuenta.sin_mfa`.
  - *Hallazgo:* El criterio `C85-01` detecta que el usuario tiene `mfa_enabled = False`.
  - *Justificación:* Se constata que la identidad de usuario carece de un dispositivo de factor múltiple de autenticación activo, lo que infringe el control 8.5 de ISO/IEC 27001:2022.
  - *Severidad:* ALTA.

- **Ejemplo 2 (IAM-003 / Control 5.18 — Derechos de Acceso):**
  - *Recurso:* `carlos.soporte` o identidad con privilegios amplios.
  - *Hallazgo:* El criterio `C18-01` analiza el documento JSON de la política y detecta comodines globales: `Action: "*"` y `Resource: "*"`.
  - *Justificación:* Asignación de permisos irrestrictos de administración que contraviene el principio de mínimo privilegio.
  - *Severidad:* CRÍTICA.

---

## 9. CONSULTA DEL CATÁLOGO DE CONTROLES ISO/IEC 27001:2022

Regrese a la pestaña **“Inicio”** (Dashboard) y desplace la vista hacia la sección inferior: **“Catálogo de Controles ISO/IEC 27001:2022”**.

**Qué mostrar y explicar:**
1. Se observan cuatro tarjetas interactivas, una por cada control abordado:
   - **Control 5.15:** Control de acceso (Regla IAM-001).
   - **Control 5.16:** Gestión de identidades (Regla IAM-002).
   - **Control 5.18:** Derechos de acceso (Regla IAM-003).
   - **Control 8.5:** Autenticación segura (Regla IAM-004).
2. Haga clic en el botón **“Ver detalle del control →”** de cualquiera de las tarjetas (por ejemplo, el Control 5.15).
3. Se abre el diálogo modal [`IsoControlDetailDialog`](file:///c:/Users/andre/Desktop/TESIS/sistema/src/auditoria_iam/ui/dialogs/control_detail_dialog.py):
   - Muestra el objetivo de seguridad formal según la norma.
   - Detalla los aspectos técnicos auditados en AWS IAM.
   - Explica el significado específico de cada estado (`Conforme`, `Hallazgo`, `No evaluable`) para ese control.
   - Presenta la **Delimitación de alcance**: aclara expresamente que la verificación técnica de identidades es un insumo diagnóstico y no constituye una certificación completa del control organizacional.
4. Muestre el botón superior del Dashboard: **“Consultar norma ISO/IEC 27001:2022 (Internet Archive) ↗”**, el cual abre en el navegador predeterminado el documento formal de la norma de acceso público.

---

## 10. CONSULTA DEL HISTORIAL Y TRAZABILIDAD (MYSQL)

Haga clic en la pestaña **“Historial”** del menú lateral.

**Qué mostrar y explicar:**
1. La tabla lista cronológicamente las corridas de auditoría almacenadas en MySQL Server.
2. Cada fila muestra: `ID`, `Fecha y Hora`, `Origen` (`simulacion` o `aws`), `Estado` (`completada`), `Hallazgos` y `Resumen cuantitativo`.
3. Seleccione una corrida anterior y haga clic en **“Ver resultados de auditoría”**.
4. La aplicación recupera de forma transparente los resultados desde la tabla `audit_results` y transfiere la vista automáticamente a `ResultsPage`, permitiendo auditar corridas históricas sin necesidad de reevaluar.

---

## 11. EXPORTACIÓN DE INFORMES (PDF, EXCEL Y CSV)

En la página de **Resultados** (o en la barra de acciones de **Historial**), muestre las opciones de exportación:

1. **Exportar a PDF:**
   - Pulse el botón **“Exportar PDF”**. Seleccione la carpeta de destino.
   - Abra el PDF generado: muestre la portada institucional, el resumen ejecutivo con gráfico circular, las tablas desglosadas por control ISO, el inventario de hallazgos con recomendaciones técnicas y el descargo de responsabilidad legal y técnica.
2. **Exportar a Excel (XLSX):**
   - Pulse **“Exportar Excel”**.
   - Abra el archivo `.xlsx` en Microsoft Excel: demuestre que el libro contiene cuatro hojas estructuradas (`Resumen`, `Evaluaciones`, `Hallazgos`, `Evidencias`) con autofiltros y colores condicionales según el estado de cumplimiento.
3. **Exportar a CSV:**
   - Pulse **“Exportar CSV”**.
   - Demuestre que el archivo utiliza codificación `UTF-8 con BOM` (`utf-8-sig`), abriéndose correctamente en Excel en español sin deformar tildes ni caracteres especiales.

---

## 12. EXPLICACIÓN DE LA INTEGRACIÓN AWS IAM (BOTO3)

Explique al jurado cómo opera la integración con la nube de Amazon Web Services:

1. **Arquitectura del Adaptador:**
   - Muestre en la arquitectura que `AWSIAMDataSource` utiliza el SDK oficial `boto3`.
2. **Principio de Mínimo Privilegio y Solo Lectura Estricto:**
   - El adaptador implementa un catálogo cerrado de 21 operaciones permitidas (`READ_ONLY_OPERATIONS`), todas de tipo `get_*` y `list_*`.
   - Bloquea preventivamente 15 prefijos de mutación (`create`, `delete`, `update`, `put`, `attach`, etc.).
   - Es imposible que el sistema altere o elimine recursos en la nube.
3. **Procesamiento de Políticas:**
   - Descarga políticas adjuntas e inline de usuarios, grupos y roles, decodifica el JSON (gestionando URL encoding de AWS) y evalúa la presencia de comodines globales (`*`).
4. **Manejo Seguro de Excepciones:**
   - Si AWS rechaza la conexión por credenciales inválidas o permisos insuficientes (`AccessDenied`), el adaptador captura el error y lo transforma en una excepción de dominio (`AWSIAMPermissionError`) sin exponer tokens ni secretos en pantalla.

---

## 13. DIFERENCIAS ENTRE MODO SIMULADOR Y MODO AWS IAM

Presente este cuadro comparativo para responder anticipadamente a posibles preguntas del jurado:

| Característica | Modo Simulador Local | Modo AWS IAM Cloud |
| :--- | :--- | :--- |
| **Origen de los datos** | Generador sintético en memoria (`simulator.py`). | API de AWS IAM mediante SDK Boto3. |
| **Dependencia de Internet** | Ninguna (opera 100% desconectado). | Requiere conexión activa a Internet. |
| **Credenciales requeridas** | Ninguna. | Credenciales de AWS (`Access Key` / `Secret Key`). |
| **Propósito principal** | Demostración académica y validación algorítmica. | Diagnóstico real de entornos en la nube. |
| **Riesgo operativo** | Cero. | Cero (modo de solo lectura verificado). |

---

## 14. LIMITACIONES TÉCNICAS Y METODOLÓGICAS DEL PROYECTO

Concluya la exposición con madurez técnica, señalando las limitaciones y delimitaciones formales del trabajo:

1. **Datos Ficticios en Demostración:** Los datos del simulador son puramente sintéticos y diseñados para activar todos los caminos lógicos de las reglas.
2. **Ausencia de Credenciales Reales de la Empresa:** La empresa UPHARVEN C.A. no suministró credenciales de producción para realizar pruebas sobre su cuenta activa de AWS. La compatibilidad con la nube se encuentra demostrada y validada al 100% mediante pruebas automatizadas y `botocore.stub.Stubber`.
3. **Herramienta Diagnóstica:** El sistema no emite certificados oficiales de cumplimiento ni sustituye a un organismo certificador acreditado ante ISO.
4. **Delimitación de Alcance:** El análisis se limita a las configuraciones lógicas de identidad en el plano de control de AWS IAM y a los cuatro controles seleccionados (5.15, 5.16, 5.18, 8.5). No inspecciona el contenido de bases de datos, redes privadas virtuales (VPC) ni sistemas operativos de instancias EC2.

---

## RESUMEN DE PREGUNTAS FRECUENTES DEL JURADO

- **¿Por qué hay evaluaciones en estado “No evaluable”?**  
  *Respuesta:* Para garantizar la integridad técnica y evitar falsos positivos o falsos conformes. Si una política no se puede leer o una cuenta carece de perfil de referencia, asumir que está conforme sería un error de seguridad grave.
- **¿El sistema puede dañar las configuraciones de AWS?**  
  *Respuesta:* No. El código restringe preventivamente todas las llamadas al SDK a una lista blanca inmutable de solo lectura (`READ_ONLY_OPERATIONS`) y tiene pruebas automatizadas específicas que verifican el rechazo de operaciones de escritura.
- **¿Cómo se garantiza que las pruebas son confiables si no hay cuenta real de AWS?**  
  *Respuesta:* Mediante la herramienta oficial de AWS `botocore.stub.Stubber`, la cual intercepta las llamadas HTTP a nivel de protocolo y simula con exactitud milimétrica las respuestas JSON y los códigos de error que emite la API real de AWS IAM.

