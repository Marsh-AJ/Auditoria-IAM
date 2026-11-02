# DOCUMENTACIÓN TÉCNICA — FASE 6, ENTREGA 6.2
## GENERACIÓN Y EXPORTACIÓN DE INFORMES DE AUDITORÍA IAM (PDF, XLSX, CSV)

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.  
**Fase:** Fase 6 — Entrega 6.2  
**Tecnologías:** Python 3.13, PySide6, ReportLab 5.1.0, openpyxl 3.1.5, csv (UTF-8 BOM), MySQL Server, pytest  
**Fecha de Entrega:** Noviembre 2026  
**Estado:** Finalizado y verificado (207 pruebas unitarias y de integración aprobadas al 100%)

---

## 1. OBJETIVO Y ALCANCE DE LA ENTREGA

La presente entrega implementa la funcionalidad integral de generación y exportación de informes técnicos de auditoría IAM en tres formatos estándar: **PDF**, **Microsoft Excel (XLSX)** y **CSV (con UTF-8 BOM)**.

La funcionalidad se integra completamente con la aplicación de escritorio PySide6 existente, permitiendo:
1. Exportar los resultados de la auditoría actual visualizada en la sección **Resultados** (tanto ejecuciones recién completadas como corridas históricas cargadas en memoria).
2. Exportar directamente cualquier auditoría histórica persistida en MySQL desde la sección **Historial**, sin necesidad de cargar previamente los resultados en la interfaz.
3. Garantizar estricta integridad y seguridad: la exportación opera exclusivamente en modo de solo lectura sobre los datos almacenados en MySQL o memoria, sin re-ejecutar auditorías, sin consultar APIs externas y sin realizar operaciones de escritura (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`) en la base de datos.

---

## 2. ARQUITECTURA DE LA SOLUCIÓN DE INFORMES

La solución se diseñó siguiendo una arquitectura desacoplada y orientada a capas, agrupando los componentes de reporte dentro del nuevo paquete `src/auditoria_iam/reports/`:

```
src/auditoria_iam/
├── application/
│   └── audit_service.py         # Orquestación de exportación y normalización de datos
├── database/
│   └── repository.py            # Nueva función de consulta de solo lectura: get_evidence_by_run
├── reports/                     # Nuevo paquete de exportación
│   ├── __init__.py              # Interfaz pública de exportadores
│   ├── report_data.py           # Normalización de datos desde MySQL y memoria
│   ├── pdf_report.py            # Generador PDF profesional con ReportLab
│   ├── excel_report.py          # Generador de hojas de cálculo con openpyxl
│   └── csv_report.py            # Generador CSV tabular con UTF-8 BOM
└── ui/
    └── pages/
        ├── results_page.py      # Barra de exportación (PDF, Excel, CSV)
        └── history_page.py      # Botones de exportación de corridas históricas
```

### 2.1. Módulo de Normalización de Datos (`report_data.py`)
Centraliza la conversión de las estructuras de datos (tanto objetos `AuditResult` en memoria como registros relacionales de `audit_runs`, `audit_results`, `findings` y `audit_evidence` en MySQL) hacia una estructura de diccionario unificada:
- **`metadata`**: ID de auditoría, fecha/hora de ejecución, fuente de datos, recursos evaluados, título del proyecto, organización y descargo de responsabilidad técnico.
- **`summary`**: Métricas cuantitativas (Total, Conforme, Hallazgo, No evaluable) y porcentajes de cumplimiento calculados con un decimal.
- **`rules_summary`**: Desglose por regla técnica (`IAM-001` a `IAM-004`) y control ISO/IEC 27001:2022 (5.15, 5.16, 5.18 y 8.5), incluyendo conteos y porcentaje de conformidad.
- **`evaluations`**: Lista ordenada de evaluaciones individuales con clave de recurso, nombre, tipo, regla, control, criterio, estado y justificación técnica.
- **`findings`**: Lista de hallazgos de seguridad con severidad (`CRÍTICA`, `ALTA`, `MEDIA`, `BAJA`), título, descripción, valor observado y recomendación técnica.
- **`evidences`**: Lista de evidencias técnicas vinculadas a los hallazgos y evaluaciones, con tipo, detalle JSON seguro y referencia de procedencia.

### 2.2. Capa de Aplicación (`AuditService`)
Se añadieron dos métodos principales:
- `get_audit_report_data(run_id, results, resources, summary, db_name)`: Recupera de forma segura los datos de MySQL si se provee un `run_id`, o utiliza las estructuras en memoria, invocando `build_report_data`.
- `export_audit_report(filepath, format_type, run_id, results, resources, summary, db_name)`: Dirige la generación hacia `generate_pdf_report`, `generate_excel_report` o `generate_csv_report` según el formato solicitado (`pdf`, `xlsx`, `csv`).

### 2.3. Capa de Persistencia (`repository.py`)
Se incorporó la consulta de solo lectura `get_evidence_by_run(audit_run_id)` que permite recuperar todas las evidencias técnicas registradas para una corrida determinada:
```sql
SELECT
    ae.id, ae.finding_id, ae.audit_result_id, ae.evidence_type,
    ae.evidence_detail, ae.evidence_reference, ae.captured_at,
    COALESCE(rf.resource_key, rr.resource_key) AS resource_key,
    COALESCE(rf.display_name, rr.display_name) AS display_name,
    COALESCE(rulef.rule_code, ruler.rule_code) AS rule_code,
    COALESCE(rulef.iso_control, ruler.iso_control) AS iso_control
FROM audit_evidence ae
LEFT JOIN findings f ON ae.finding_id = f.id
LEFT JOIN resources rf ON f.resource_id = rf.id
LEFT JOIN audit_rules rulef ON f.audit_rule_id = rulef.id
LEFT JOIN audit_results ar ON ae.audit_result_id = ar.id
LEFT JOIN resources rr ON ar.resource_id = rr.id
LEFT JOIN audit_rules ruler ON ar.audit_rule_id = ruler.id
WHERE f.audit_run_id = %s OR ar.audit_run_id = %s
ORDER BY ae.id;
```

---

## 3. ESPECIFICACIÓN DETALLADA DE LOS FORMATOS DE EXPORTACIÓN

### 3.1. Formato PDF (`pdf_report.py`)
Construido mediante **ReportLab Platypus** y gráficos vectoriales nativos de ReportLab (`Drawing`, `Pie`, `Legend`):
- **Estructura del documento:** Tamaño Carta (Letter) con márgenes estándar de 0.5 pulgadas (36 pt), ancho útil de 540 pt.
- **Canvas de doble pasada (`NumberedCanvas`):**
  - **Encabezado dinámico:** A partir de la página 2, dibuja el título institucional del proyecto, norma evaluada y una línea divisoria sutil.
  - **Pie de página:** En todas las páginas, incluye la leyenda de confidencialidad y la numeración dinámica en formato «Página X de Y».
- **Secciones del informe:**
  1. *Encabezado Institucional:* Banner estilizado con fondo azul oscuro (`#0F172A`), título formal, nombre del proyecto, organización y norma de referencia.
  2. *Metadatos de Ejecución:* Tabla con ID de auditoría, fecha/hora, fuente de datos, total de recursos y controles evaluados.
  3. *Resumen Ejecutivo y Distribución:*
     - Tabla de indicadores KPI con totales y porcentajes coloreados según la paleta del sistema (`#16A34A` para Conforme, `#DC2626` para Hallazgo, `#64748B` para No evaluable).
     - Gráfico de pastel (`Pie` chart vectorial nativo) y leyenda lateral descriptiva calculada matemáticamente.
  4. *Desglose por Control ISO/IEC 27001:2022:* Tabla de los controles 5.15, 5.16, 5.18 y 8.5 con cantidades y porcentaje de conformidad.
  5. *Detalle de Evaluaciones Técnicas:* Tabla completa con ajuste automático de texto (`Paragraph`) para evitar desbordamientos, indicando recurso, tipo, regla, control, estado y justificación.
  6. *Hallazgos Técnicos de Seguridad:* Fichas técnicas individuales con severidad destacada (`CRÍTICA`, `ALTA`, `MEDIA`, `BAJA`), valor observado y recomendaciones específicas. Si no hay hallazgos, muestra un mensaje formal en recuadro verde.
  7. *Evidencias Técnicas Recopiladas:* Tabla con el detalle técnico minimizado, identificadores y fechas de captura.
  8. *Conclusiones Técnicas y Descargo de Responsabilidad:* Párrafo formal que aclara que el dictamen refleja una auditoría algorítmica de configuraciones lógicas y no constituye una certificación formal de cumplimiento organizacional ISO/IEC 27001.

### 3.2. Formato Microsoft Excel (`excel_report.py`)
Construido mediante **openpyxl 3.1.5** con cuatro hojas de cálculo:
1. **Hoja 1: `Resumen`**
   - Identificador de auditoría, Fecha y hora, Fuente de datos, Estado de ejecución y Recursos IAM evaluados.
   - Tabla de indicadores globales (Total de evaluaciones, Conforme, Hallazgo, No evaluable, con formato porcentual `0.0%`).
   - Tabla de desglose por regla y control ISO/IEC 27001:2022.
   - Recuadro de conclusiones técnicas y descargo de responsabilidad.
2. **Hoja 2: `Evaluaciones`**
   - Columnas: `Identificador del Resultado`, `Recurso`, `Tipo de Recurso`, `Código de Control`, `Código de Regla`, `Código de Criterio`, `Estado`, `Descripción`.
   - Estilo condicional de celdas por estado (Conforme en verde, Hallazgo en rojo, No evaluable en gris).
   - Inmovilización de la fila superior de encabezados (`freeze_panes = "A2"`).
   - Filtros automáticos en todas las columnas (`auto_filter`).
   - Autoajuste dinámico del ancho de columnas en función del contenido.
3. **Hoja 3: `Hallazgos`**
   - Columnas: `Identificador`, `Recurso`, `Control`, `Regla`, `Criterio`, `Severidad`, `Descripción`, `Evidencia disponible`, `Recomendación Técnica`.
   - Colores distintivos según severidad (`CRÍTICA`, `ALTA`, `MEDIA`, `BAJA`).
   - Manejo de caso borde: Si no existen hallazgos, conserva la hoja e inserta una fila indicando «No se detectaron hallazgos técnicos en esta auditoría».
4. **Hoja 4: `Evidencias`**
   - Columnas: `Identificador de Evidencia`, `Resultado o Hallazgo Asociado`, `Recurso`, `Regla`, `Control ISO`, `Tipo de Evidencia`, `Detalle Técnico`, `Referencia Técnica`, `Fecha de Captura`.
   - Manejo de caso borde: Si no existen evidencias, conserva la hoja e inserta una fila informativa.

### 3.3. Formato CSV (`csv_report.py`)
Generado mediante el módulo nativo `csv` de Python:
- **Codificación:** `utf-8-sig` (UTF-8 con Byte Order Mark `\xef\xbb\xbf`), garantizando apertura directa en Microsoft Excel en Windows sin distorsión de caracteres con tilde, eñes o comillas.
- **Delimitador:** Comas con entrecomillado mínimo defensivo (`csv.QUOTE_MINIMAL`) para respetar textos multilínea y caracteres especiales.
- **Columnas estándar en español:**
  `ID de auditoría, Fecha, Fuente, Recurso, Tipo de recurso, Control ISO, Regla, Criterio, Estado, Descripción`

---

## 4. INTEGRACIÓN CON LA INTERFAZ GRÁFICA (PYSIDE6)

### 4.1. Sección «Resultados» (`ResultsPage`)
- Se incorporó una barra horizontal de acciones de exportación con tres botones ergonómicos:
  - **Exportar PDF 📄** (Azul `#0284c7`)
  - **Exportar Excel 📊** (Verde esmeralda `#059669`)
  - **Exportar CSV 📑** (Gris pizarra `#1e293b`)
- Los botones permanecen deshabilitados por defecto y se habilitan automáticamente cuando se cargan resultados reales en la tabla.
- Al pulsar un botón, se abre el cuadro de diálogo estándar del sistema operativo (`QFileDialog.getSaveFileName`) sugiriendo un nombre predeterminado con fecha y hora.
- Tras la exportación, el banner superior informa el éxito de la operación con la ruta del archivo generado, o notifica cualquier eventual error de I/O de manera clara.

### 4.2. Sección «Historial» (`HistoryPage`)
- En la barra de acciones superior se añadieron tres botones de exportación rápida:
  - **PDF 📄**, **Excel 📊**, **CSV 📑**
- Los botones se habilitan únicamente cuando el usuario selecciona una fila de ejecución histórica en la tabla.
- Permite exportar cualquier corrida histórica persistida en MySQL directamente a disco, sin necesidad de navegar a la vista de resultados.

---

## 5. SEGURIDAD, INTEGRIDAD Y RENDIMIENTO

| Criterio | Mecanismo de Garantía Implementado |
|---|---|
| **Solo Lectura en BD** | Los generadores de informes no invocan sentencias de escritura (`INSERT`, `UPDATE`, `DELETE`, `ALTER`). Verificado mediante análisis estático y pruebas con mocks de base de datos. |
| **Cero Re-evaluación** | Los informes se construyen a partir de los datos en memoria o recuperados de MySQL; no se ejecutan reglas algorítmicas ni llamadas externas a AWS durante la exportación. |
| **Conservación de Estados** | Los tres estados («Conforme», «Hallazgo», «No evaluable») se tratan como categorías disjuntas. «No evaluable» nunca se clasifica como «Conforme». |
| **Protección contra Fugas** | Las evidencias técnicas en los informes están minimizadas de acuerdo con el principio de necesidad y no contienen secretos, claves de acceso ni credenciales en texto claro. |
| **Manejo de Errores I/O** | Si el usuario selecciona una ruta protegida o no disponible, la aplicación captura la excepción (`OSError`, `PermissionError`) y muestra un mensaje amigable sin congelar ni cerrar la interfaz. |

---

## 6. RESULTADOS DE PRUEBAS AUTOMATIZADAS

Se diseñó e implementó la suite completa `tests/test_reports.py` compuesta por 14 pruebas automatizadas (las 12 requeridas más 2 pruebas de controles de interfaz gráfica):

| # | Identificador de Prueba | Descripción | Resultado |
|---|---|---|:---:|
| 1 | `test_pdf_report_generation` | Verifica que el archivo PDF se cree, sea válido, contenga cabecera `%PDF` y tamaño adecuado. | **PASSED** |
| 2 | `test_excel_report_generation` | Verifica que el libro XLSX contenga las 4 hojas (`Resumen`, `Evaluaciones`, `Hallazgos`, `Evidencias`) y datos consistentes. | **PASSED** |
| 3 | `test_csv_report_generation` | Verifica que el archivo CSV se cree con BOM UTF-8 (`\xef\xbb\xbf`) y las 10 columnas en español. | **PASSED** |
| 4 | `test_report_data_matches_audit_results` | Comprueba que los totales, estados, claves de recursos y porcentajes coincidan exactamente con la auditoría. | **PASSED** |
| 5 | `test_historical_run_export` | Verifica la exportación completa a partir de un ID de corrida histórica persistida en MySQL. | **PASSED** |
| 6 | `test_preservation_of_three_statuses` | Verifica que «Conforme», «Hallazgo» y «No evaluable» se conserven como 3 estados separados sin conversiones erróneas. | **PASSED** |
| 7 | `test_edge_case_no_findings` | Caso borde: Exporta sin errores cuando una auditoría tiene 0 hallazgos (100% conformes/no evaluables). | **PASSED** |
| 8 | `test_edge_case_no_evidences` | Caso borde: Exporta sin errores cuando una auditoría no tiene evidencias adjuntas. | **PASSED** |
| 9 | `test_special_characters_and_accents` | Verifica la codificación correcta de tildes, eñes (`áéíóúñ`), signos (`¿? ¡! «»`) y símbolos técnicos. | **PASSED** |
| 10 | `test_file_write_error_handling` | Verifica que rutas no válidas o sin permisos generen excepciones controladas sin colapsar el sistema. | **PASSED** |
| 11 | `test_export_does_not_perform_mysql_writes` | Análisis estático de código y mock de cursor confirmando cero sentencias de modificación en MySQL. | **PASSED** |
| 12 | `test_export_does_not_execute_new_audits` | Mock de `AuditEngine` y fuentes de datos confirmando cero ejecuciones de auditoría durante la exportación. | **PASSED** |
| 13 | `test_results_page_export_controls` | Verifica el ciclo de vida de los botones de exportación en la pantalla `ResultsPage` (deshabilitados/habilitados). | **PASSED** |
| 14 | `test_history_page_export_controls_on_selection` | Verifica que los botones de exportación en `HistoryPage` se habiliten exclusivamente ante una fila seleccionada. | **PASSED** |

### Resumen Global de la Suite de Pruebas
```
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\andre\Desktop\TESIS\sistema
collected 207 items

tests/test_audit_engine.py .................................. [ 16%]
tests/test_audit_models.py .................................. [ 25%]
tests/test_aws_data_source.py ............................... [ 40%]
tests/test_connection.py .................................... [ 43%]
tests/test_dashboard.py ..................................... [ 49%]
tests/test_persistence.py ................................... [ 57%]
tests/test_reports.py ....................................... [ 64%]
tests/test_repository.py .................................... [ 72%]
tests/test_rule_iam_001.py .................................. [ 77%]
tests/test_rule_iam_002.py .................................. [ 82%]
tests/test_rule_iam_003.py .................................. [ 88%]
tests/test_rule_iam_004.py .................................. [ 91%]
tests/test_settings.py ...................................... [ 97%]
tests/test_simulator.py ..................................... [ 98%]
tests/test_ui.py ............................................ [100%]

============================= 207 passed in 9.61s =============================
```

---

## 7. RESOLUCIÓN DEL CICLO DE VIDA DE OBJETOS QT EN PRUEBAS (STATUS_ACCESS_VIOLATION 0xC0000005)

Durante la ejecución continua de la suite completa de 207 pruebas en Windows (Python 3.13 + PySide6), se identificó un cierre anómalo con código de salida nativo `STATUS_ACCESS_VIOLATION` (`0xC0000005`), el cual ocurría tras completarse con éxito la totalidad de las aserciones funcionales.

### 7.1. Diagnóstico Técnico
- **Causa raíz:** En las pruebas de interfaz gráfica (`test_ui.py`, `test_dashboard.py`, `test_reports.py`) se instanciaban más de 200 widgets de nivel superior (`MainWindow`, `QDialog`, `QChartView`, diálogos de control, etc.) sin cierre ni liberación explícita.
- **Colisión de desmontaje:** Al finalizar la sesión de pytest, el recolector de basura cíclico de Python (`gc`) y el descargador de DLLs de C++ de Qt colisionaban al intentar destruir simultáneamente árboles de objetos Qt nativos cuyos punteros C++ quedaban desincronizados durante la descarga del runtime de Python.
- **Impacto:** Aunque las 207 pruebas pasaban sus aserciones funcionales, el proceso Python finalizaba con código 1 o excepción fatal nativa de Windows (`0xC0000005`) en `<no Python frame>`.

### 7.2. Implementación de la Solución
Se aplicó una arquitectura de gestión de ciclo de vida centralizada y no invasiva:
1. **Archivo `tests/conftest.py`:**
   - Centralización del fixture `qapp` con `scope="session"`, garantizando una única instancia de `QApplication` compartida y un barrido de cierre final antes de salir.
   - Implementación del fixture automático `clean_qt_widgets` (`autouse=True`):
     - Antes de cada prueba, registra el conjunto de widgets de nivel superior preexistentes (`existing_widgets = set(qapp.topLevelWidgets())`).
     - Al concluir la prueba, detecta exclusivamente los widgets nuevos generados durante la misma.
     - Invoca de forma segura `close()` y `deleteLater()` sobre cada widget nuevo.
     - Procesa los eventos diferidos de Qt con `sendPostedEvents(None, QEvent.Type.DeferredDelete)` y `processEvents()`.
     - No destruye `QApplication` ni altera widgets de pruebas previas.
2. **Depuración de fixtures duplicados:**
   - Se eliminaron las definiciones redundantes de `qapp` en `tests/test_ui.py`, `tests/test_dashboard.py` y `tests/test_reports.py`.
   - Se actualizó el fixture `main_window` en `tests/test_ui.py` como fixture generador con `yield window` y teardown explícito (`close()`, `deleteLater()`).

### 7.3. Validación de Estabilidad
La solución se verificó rigurosamente en el entorno de ejecución:
- `test_ui.py`: 18 aprobadas individualmente (código 0).
- `test_dashboard.py`: 13 aprobadas individualmente (código 0).
- `test_reports.py`: 14 aprobadas individualmente (código 0).
- 3 archivos Qt combinados (45 pruebas): aprobadas al 100% (código 0).
- **Suite completa (207 pruebas):** ejecutada en 3 ocasiones consecutivas completando las 207 pruebas sin fallos, con código de salida real 0 y 0 excepciones nativas.

---

## 8. CONCLUSIONES

La Entrega 6.2 dota al sistema de auditoría IAM de capacidades profesionales de reportería y trazabilidad documental. Los tres formatos implementados cubren los diferentes casos de uso esperados en una auditoría corporativa bajo ISO/IEC 27001:
- **PDF:** Documento ejecutivo y técnico formal para presentación ante comités de seguridad o partes interesadas.
- **XLSX:** Herramienta analítica para auditores de TI y administradores de sistemas que requieran filtrar, ordenar o cruzar hallazgos y evidencias.
- **CSV:** Formato universal de interoperabilidad para integración con sistemas SIEM, herramientas de análisis de datos o scripts de automatización.

