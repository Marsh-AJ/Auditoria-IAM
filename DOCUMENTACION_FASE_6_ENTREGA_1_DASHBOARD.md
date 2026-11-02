# DOCUMENTACIÓN TÉCNICA — FASE 6, ENTREGA 6.1: DASHBOARD Y CONSULTA DE CONTROLES ISO/IEC 27001

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.  
**Fase:** Fase 6 — Visualización Ejecutiva, Reportes y Catálogo Normativo  
**Entrega:** Entrega 6.1 — Dashboard Funcional y Consulta Interactiva de Controles ISO/IEC 27001:2022  
**Fecha:** Noviembre 2026  
**Tecnologías:** Python 3.13, PySide6 (Qt 6.12.0, QtCharts), MySQL Server 9.6 / mysql-connector-python, Pytest  

---

## 1. Objetivo de la Entrega

Implementar un **Dashboard Ejecutivo y Funcional** dentro de la aplicación de escritorio de auditoría IAM (PySide6), que proporcione una visión panorámica y en tiempo real del estado de seguridad de identidades y accesos, integrando:

1. **Indicadores ejecutivos dinámicos (KPIs):** Total de evaluaciones, cantidad de resultados Conforme, Hallazgo y No evaluable derivados de la última auditoría persistida en MySQL.
2. **Gráfico de distribución porcentual:** Representación gráfica mediante `PySide6.QtCharts` (gráfico tipo dona/circular) complementada con insignias numéricas y porcentuales exactas.
3. **Resumen granular por regla IAM:** Desglose de evaluaciones por regla (`IAM-001`, `IAM-002`, `IAM-003`, `IAM-004`) obtenido directamente de `audit_results`.
4. **Información y trazabilidad de la última auditoría:** Identificador, fecha/hora, fuente, estado y conteo de hallazgos, con navegación directa a la vista de resultados e historial.
5. **Catálogo interactivo de controles ISO/IEC 27001:2022:** Paneles y diálogos de detalle (`IsoControlDetailDialog`) para los cuatro controles del alcance (`5.15`, `5.16`, `5.18`, `8.5`), delimitando el aspecto técnico auditado y aclarando formalmente que no representa una certificación organizacional.
6. **Acceso al documento de referencia alojado en Internet Archive:** Opción visible para consultar la tercera edición de ISO/IEC 27001:2022 alojada en Internet Archive mediante el navegador predeterminado del sistema operativo.
7. **Principio estricto de solo lectura:** Operaciones sustentadas exclusivamente en sentencias `SELECT`, sin alteraciones a catálogos ni escrituras a la base de datos durante el uso del dashboard.

---

## 2. Arquitectura de Visualización y Flujo de Datos

El dashboard se integra en la pantalla principal (`HomePage`, índice `0` de `MainWindow.stacked_widget`), reutilizando la capa de aplicación y repositorio sin duplicar mecanismos de navegación:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CAPA DE PRESENTACIÓN (PySide6 UI)                    │
│                                                                        │
│   MainWindow (Sidebar de 5 secciones persistentes)                    │
│       │                                                                │
│       ├──► [0] HomePage / Dashboard                                    │
│       │        ├── 4 Tarjetas KPI (Total, Conf, Hall, NoEv)            │
│       │        ├── Gráfico de distribución (QChartView QtCharts)       │
│       │        ├── Resumen por regla IAM (IAM-001 .. IAM-004)          │
│       │        ├── Tarjeta de última auditoría (Con enlaces directos)  │
│       │        ├── Catálogo interactivo de controles (4 tarjetas)      │
│       │        │     └── Abre: IsoControlDetailDialog (Modal)          │
│       │        └── Acceso a norma ISO externa (Internet Archive)       │
│       │                                                                │
│       ├──► [1] AuditPage (Ejecución de auditorías)                     │
│       ├──► [2] ResultsPage (Visualización granular)                   │
│       ├──► [3] HistoryPage (Historial cronológico)                     │
│       └──► [4] SettingsPage (Parámetros del sistema)                   │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                        (Solo Lectura / SELECT)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          CAPA DE APLICACIÓN                            │
│                                                                        │
│   AuditService                                                         │
│   └── get_dashboard_data(db_name=None)                                 │
│         ├── get_audit_history(limit=1) -> Última auditoría             │
│         └── get_historical_run_results(run_id) -> Resultados y resumen│
└────────────────────────────────────────────────────────────────────────┘
                                    │
                        (Solo Lectura / SELECT)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    CAPA DE PERSISTENCIA / REPOSITORIO                  │
│                                                                        │
│   repository.py                                                        │
│   ├── get_audit_runs(limit=1) [SELECT audit_runs]                      │
│   └── get_audit_results_by_run(run_id) [SELECT audit_results JOIN ...] │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Componentes del Dashboard

### 3.1. Indicadores Principales (KPI Cards)
Cuatro tarjetas dinámicas ubicadas en la zona superior del dashboard:
- **Total Evaluaciones:** Total de criterios técnicos evaluados (ej. `67`).
- **Conforme:** Evaluaciones que satisfacen plenamente los requisitos técnicos (ej. `36`, color verde `#22c55e`).
- **Hallazgo:** Evaluaciones donde se identificó una desviación técnica o riesgo (ej. `6`, color rojo `#ef4444`).
- **No evaluable:** Evaluaciones que no pudieron completarse por atributos ausentes o incompletos (ej. `25`, color ámbar `#f59e0b`).
*(Si no existen auditorías en el sistema o la base de datos no está disponible, los contadores muestran `0` o `—` sin presentar datos ficticios).*

### 3.2. Gráfico de Distribución de Resultados
- Construido con `PySide6.QtCharts.QChartView` y `QChart` utilizando una serie de dona (`QPieSeries` con `holeSize = 0.35`).
- Colores representativos: Verde (`#22c55e`) para Conforme, Rojo (`#ef4444`) para Hallazgo y Ámbar (`#f59e0b`) para No evaluable.
- Acompañado por insignias de desglose con cantidades y porcentajes calculados a un decimal:
  - `Conforme: 36 (53.7%)`
  - `Hallazgo: 6 (9.0%)`
  - `No evaluable: 25 (37.3%)`
- **Estado vacío:** Cuando no existen datos de auditoría, el gráfico se oculta limpiamente y se presenta un contenedor informativo:  
  `"ℹ No hay información disponible. Aún no se han registrado auditorías en el sistema."`

### 3.3. Resumen por Regla Técnica
Desglose estructurado de las 4 reglas evaluadas por el motor algorítmico:
- **IAM-001 (Control 5.15 — Control de acceso):** Total evaluado, conformes, hallazgos y no evaluables.
- **IAM-002 (Control 5.16 — Gestión de identidades):** Antigüedad de actividad frente al umbral de 90 días.
- **IAM-003 (Control 5.18 — Derechos de acceso):** Permisos excesivamente amplios (`Action: *`, `Resource: *`).
- **IAM-004 (Control 8.5 — Autenticación segura):** Habilitación efectiva de autenticación multifactor (MFA).

### 3.4. Tarjeta de Última Auditoría y Navegación Integrada
Permite al usuario auditar la última sesión persistida sin tener que desplazarse manualmente:
- Identificador de Ejecución (`#ID`), Fecha y Hora, Fuente (`Simulacion` / `Aws`), Estado (`Completada`) y Total de Hallazgos.
- Botón **"Ver resultados detallados →"**: Comunica con `MainWindow` mediante la señal `run_selected`, cargando los resultados de dicha ejecución en `ResultsPage` (índice 2).
- Botón **"Ver historial completo"**: Emite la señal `navigate_requested(3)`, trasladando al usuario a `HistoryPage`.

---

## 4. Catálogo Interactivo de Controles ISO/IEC 27001:2022

Ubicado en la sección donde anteriormente se mostraban las tarjetas estáticas de controles. Se implementó un catálogo dinámico y estructurado en [`src/auditoria_iam/ui/controls_catalog.py`](file:///c:/Users/andre/Desktop/TESIS/sistema/src/auditoria_iam/ui/controls_catalog.py) con cuatro controles de seguridad:

| Control ISO | Nombre del Control | Regla IAM | Aspecto Técnico Auditado en AWS IAM | Criterios Aplicados |
| :--- | :--- | :--- | :--- | :--- |
| **5.15** | Control de acceso | **IAM-001** | Correspondencia de membresías de grupos asignados a usuarios y relaciones de confianza en roles frente a perfiles autorizados. | `C15-01` (Grupos asignados)<br>`C15-02` (Confianza en roles) |
| **5.16** | Gestión de identidades | **IAM-002** | Verificación del estado de vigencia/activación y análisis de metadatos normalizados de actividad frente al umbral configurable (90 días por defecto). | `C16-01` (Estado de vigencia y activación)<br>`C16-02` (Actividad reciente normalizada) |
| **5.18** | Derechos de acceso | **IAM-003** | Análisis sintáctico estricto de políticas JSON para identificar sentencias con comodines globales (`Action: *`, `Resource: *`). | `C18-01` (Comodines globales) |
| **8.5** | Autenticación segura | **IAM-004** | Verificación técnica de la activación de dispositivos de autenticación multifactor (MFA) en usuarios humanos interactivos. | `C85-01` (MFA obligatorio) |

### 4.1. Vista Detallada de cada Control (`IsoControlDetailDialog`)
Al pulsar **"Consultar detalle técnico →"** en cualquiera de las cuatro tarjetas, se despliega una ventana modal interactiva con:
1. **Código y Nombre:** Identificador formal ISO y nombre del control.
2. **Referencia Normativa:** Ubicación en el Anexo A de ISO/IEC 27001:2022.
3. **Descripción Informativa:** Resumen explicativo no literal del propósito del control.
4. **Objetivo de Seguridad:** Finalidad técnica y de negocio del control.
5. **Aspecto Técnico Auditado:** Delimitación técnica de lo que el sistema inspecciona en AWS IAM.
6. **Criterios de Verificación:**
   - **Control 5.16:** C16-01 evalúa `resource_status` distinguiendo identidades activas de inactivas/deshabilitadas (requiriendo evidencia explícita de deficiencia de desprovisionamiento para emitir Hallazgo; de lo contrario resulta No evaluable). C16-02 evalúa metadatos normalizados de actividad admitidos por el motor (`last_access_days`, `days_since_last_access`, `days_inactive`, `inactivity_days`) frente al umbral del prototipo (90 días por defecto).
7. **Significado de Estados:** Explicación concreta de qué implica obtener `Conforme`, `Hallazgo` o `No evaluable` para cada criterio de evaluación.
8. **Alcance Técnico y Limitaciones (Advertencia Formal):** Cuadro destacado aclarando que la evaluación se limita a verificaciones técnicas en AWS IAM y no constituye una certificación ISO 27001 ni una auditoría organizacional completa.

### 4.2. Acceso al Documento de la Norma en Internet Archive
- En la zona de controles se incorporó el botón:  
  **`Consultar documento ISO/IEC 27001:2022 ↗`**
- Al seleccionarlo, se invoca de manera segura `QDesktopServices.openUrl(QUrl(EXTERNAL_ISO_URL))`, abriendo el navegador predeterminado hacia la URL externa:  
  `https://ia801902.us.archive.org/28/items/iso-iec-27001-2022-standard/ISO%20IEC%2027001%202022%20Standard.pdf`
- Se incluye una nota visible y discreta indicando que el documento está alojado en Internet Archive como recurso independiente de referencia académica, sin atribuirle carácter de sitio oficial de ISO ni afirmar derechos de distribución.

---

## 5. Resiliencia y Principio de Solo Lectura

1. **Ausencia total de escrituras:** Ni el dashboard ni sus componentes de visualización ejecutan sentencias `INSERT`, `UPDATE`, `DELETE`, `DROP` o `ALTER`. Se validó mediante análisis estático de código en pruebas automatizadas.
2. **Botón "Actualizar dashboard 🔄":** Re-ejecuta exclusivamente consultas `SELECT` sobre `audit_runs` y `audit_results`, refrescando los widgets sin lanzar nuevas auditorías ni alterar registros existentes.
3. **Tolerancia a fallos de MySQL:** Si la base de datos se encuentra fuera de servicio, la interfaz captura defensivamente la excepción y muestra un banner comprensible:  
   `"⚠️ No se pudo conectar a la base de datos MySQL para consultar los datos del dashboard..."`  
   Los contadores se reinician a guiones (`—`) para evitar presentar información desactualizada o ficticia.

---

## 6. Archivos Creados y Modificados

### Archivos Creados:
1. `src/auditoria_iam/ui/controls_catalog.py`: Base de conocimiento estructurada de los controles ISO/IEC 27001:2022, criterios y enlace a Internet Archive.
2. `src/auditoria_iam/ui/dialogs/control_detail_dialog.py`: Diálogo modal `IsoControlDetailDialog` con visualización completa del control y delimitación de alcance.
3. `src/auditoria_iam/ui/dialogs/__init__.py`: Paquete de diálogos de usuario.
4. `tests/test_dashboard.py`: Suite de 13 pruebas automatizadas para la Entrega 6.1.
5. `DOCUMENTACION_FASE_6_ENTREGA_1_DASHBOARD.md`: Presente informe técnico.

### Archivos Modificados:
1. `src/auditoria_iam/application/audit_service.py`: Adición del método `get_dashboard_data(db_name=None)` para el cálculo agregado de indicadores y distribución.
2. `src/auditoria_iam/ui/pages/home_page.py`: Transformación integral de `HomePage` en el Dashboard Ejecutivo interactivo con tarjetas KPI, gráfico de dona `QtCharts`, resumen por regla, catálogo interactivo de controles y apertura del PDF normativo.
3. `src/auditoria_iam/ui/main_window.py`: Conexión de señales de navegación (`run_selected`, `navigate_requested`), refresco automático de dashboard al entrar a Inicio (`_on_navigate(0)`) y tras finalizar una auditoría (`_on_audit_completed`).

---

## 7. Resultados de las Pruebas Automatizadas

Se ejecutó la suite completa de pruebas del sistema (incluyendo pruebas de motor, modelos, simulador, adaptador AWS, conexión, persistencia, interfaz y dashboard):

```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\andre\Desktop\TESIS\sistema
collected 193 items

tests/test_audit_engine.py ........                                      [  4%]
tests/test_audit_models.py ......                                        [  7%]
tests/test_aws_data_source.py ............................               [ 21%]
tests/test_connection.py ......                                          [ 24%]
tests/test_dashboard.py .............                                    [ 31%]
tests/test_persistence.py ................                               [ 39%]
tests/test_repository.py ...................                             [ 49%]
tests/test_rule_iam_001.py ................                              [ 57%]
tests/test_rule_iam_002.py .............                                 [ 64%]
tests/test_rule_iam_003.py ......................                        [ 75%]
tests/test_rule_iam_004.py ......                                        [ 78%]
tests/test_settings.py .............                                     [ 85%]
tests/test_simulator.py .........                                        [ 90%]
tests/test_ui.py ..................                                      [100%]

============================= 193 passed in 6.90s =============================
```

- **Total de pruebas en el sistema:** 193 pruebas.
- **Pruebas aprobadas:** 193 pruebas (100% de éxito).
- **Pruebas fallidas:** 0 pruebas.

---

## 8. Instrucciones de Uso y Verificación

1. **Iniciar la aplicación:**
   ```powershell
   .\.venv\Scripts\python.exe main.py
   ```
2. **Visualizar el Dashboard:**
   - La pantalla de bienvenida ("Inicio") presenta inmediatamente el dashboard con los indicadores de la última auditoría registrada en MySQL.
   - En caso de no existir auditorías previas, se visualizará el mensaje informativo y los contadores en cero.
3. **Consultar Controles ISO:**
   - En la sección inferior de Inicio, haga clic en el botón **"Consultar detalle técnico →"** de cualquiera de los cuatro controles (ej. Control 5.15). Se abrirá la ventana modal con todos los requisitos y advertencias de alcance.
4. **Consultar documento ISO/IEC 27001:2022:**
   - En la barra de referencia normativa, pulse **"Consultar documento ISO/IEC 27001:2022 ↗"** para abrir el documento PDF alojado en Internet Archive en su navegador predeterminado.
5. **Navegar a Resultados:**
   - En la tarjeta de la última auditoría, pulse **"Ver resultados detallados →"** para transferir la visualización a la vista tabular de `ResultsPage`.

