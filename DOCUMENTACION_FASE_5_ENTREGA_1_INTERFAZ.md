# DOCUMENTACIÓN TÉCNICA — FASE 5, ENTREGA 1: ESTRUCTURA DE LA APLICACIÓN DE ESCRITORIO

**Proyecto:** Modelo automatizado para la auditoría de gestión de identidades y accesos en entornos de nube basado en el estándar ISO 27001 para UPHARVEN C.A.  
**Fase:** Fase 5 — Interfaz Gráfica de Usuario (PySide6)  
**Entrega:** Entrega 1 — Estructura de la Aplicación de Escritorio y Navegación  
**Fecha:** Noviembre 2026  
**Tecnologías:** Python 3.13, PySide6 (Qt 6.12.0), Pytest  

---

## 1. Objetivo de la Entrega

Construir la estructura inicial de la aplicación de escritorio utilizando **PySide6**, implementando:
1. Una ventana principal (`MainWindow`) organizada con un menú lateral persistente y navegación fluida entre cinco vistas mediante `QStackedWidget`.
2. Las cinco secciones requeridas:
   - **Inicio (`HomePage`):** Descripción del propósito del sistema, controles ISO/IEC 27001 evaluados (5.15, 5.16, 5.18, 8.5) y fuentes de datos disponibles.
   - **Ejecutar auditoría (`AuditPage`):** Selector de fuente de datos ("Simulador", "AWS IAM") y botón de ejecución con aviso formal de activación en la siguiente entrega.
   - **Resultados (`ResultsPage`):** Estructura tabular (5 columnas) para visualizar hallazgos y evaluaciones de auditoría, con mensaje inicial de estado vacío.
   - **Historial (`HistoryPage`):** Estructura tabular (5 columnas) para consultar auditorías previas persistidas, con mensaje de estado vacío.
   - **Configuración (`SettingsPage`):** Visualización de parámetros operativos (fuentes, umbrales temporales de inactividad, severidad crítica y parámetros de ejecución en modo solo lectura/demostrativo, sin exposición de credenciales).
3. Una estética visual profesional orientada a ciberseguridad mediante una hoja de estilos unificada (QSS) en modo oscuro.
4. El punto de entrada ejecutable `main.py` en la raíz del proyecto.
5. El estricto desacoplamiento de la interfaz gráfica respecto al motor algorítmico, AWS IAM y MySQL, garantizando la preservación intacta de las fases previas aprobadas.

---

## 2. Arquitectura de la Interfaz

La arquitectura de la interfaz gráfica sigue el patrón de separación de responsabilidades y modularidad:

```
src/auditoria_iam/ui/
│
├── __init__.py               # Exportación de MainWindow
├── styles.py                 # Paleta de colores y hoja de estilos QSS centralizada
├── main_window.py            # Ventana principal (1200x750, min 960x600) con sidebar y QStackedWidget
└── pages/
    ├── __init__.py           # Exportación de las 5 páginas
    ├── home_page.py          # Vista 'Inicio'
    ├── audit_page.py         # Vista 'Ejecutar auditoría'
    ├── results_page.py       # Vista 'Resultados'
    ├── history_page.py       # Vista 'Historial'
    └── settings_page.py      # Vista 'Configuración'
```

### Componentes y Patrones de Diseño
- **`MainWindow` (`QMainWindow`):**
  - Configura dimensiones iniciales de `1200x750` píxeles y restricciones de tamaño mínimo de `960x600` píxeles.
  - Título de ventana: `"Sistema de Auditoría IAM"`.
  - Disposición horizontal (`QHBoxLayout`) que divide la pantalla en:
    1. **Sidebar lateral izquierdo (ancho fijo de 240 px):** Contiene la identidad del sistema ("AUDITORÍA IAM", "ISO 27001 Prototipo"), un grupo exclusivo de botones de navegación (`QButtonGroup`) con iconos tipográficos y estilo activo visible, un separador expansivo (`QSpacerItem`) y un pie de barra con versión y entorno institucional ("v1.0.0-rc | UPHARVEN C.A.").
    2. **Área de contenido central (`QStackedWidget`):** Administra el apilamiento y conmutación de las cinco páginas sin recargar componentes.
- **Mecanismo de Navegación:**
  - El índice de cada botón en el `QButtonGroup` coincide biyectivamente con el índice de la página en el `QStackedWidget` (`0: Inicio`, `1: Ejecutar auditoría`, `2: Resultados`, `3: Historial`, `4: Configuración`).
  - La conmutación ocurre a través del método `_on_navigation_clicked(button_id)`, garantizando sincronización bidireccional y navegación instantánea.
- **Estilo Visual (`styles.py`):**
  - Tema oscuro de ciberseguridad con paleta Slate / Blue / Teal:
    - Fondo de ventana: `#0b0f19` / Fondo principal: `#0f172a`.
    - Superficies de tarjetas y paneles: `#1e293b`.
    - Bordes sutiles: `#334155`.
    - Texto principal: `#f8fafc`; texto atenuado: `#94a3b8`.
    - Acentos primarios y selección: `#38bdf8` (Cyan) y `#0284c7`.
    - Indicadores semánticos: Verde éxito `#22c55e`, Naranja advertencia `#f59e0b`, Azul información `#38bdf8`.

---

## 3. Archivos Creados y Modificados

### Archivos Creados:
1. `src/auditoria_iam/ui/styles.py`: Definición de paleta de colores y cadena QSS integral para todos los controles Qt (botones, tablas, combos, etiquetas, tarjetas).
2. `src/auditoria_iam/ui/pages/home_page.py`: Clase `HomePage` con tarjetas informativas de propósito, controles ISO (5.16 con redacción formal sobre metadatos y umbral de 90 días), banner de estado y fuentes (aclarando la disponibilidad en vivo de AWS IAM mediante adaptador y activación desde interfaz en la siguiente entrega).
3. `src/auditoria_iam/ui/pages/audit_page.py`: Clase `AuditPage` con `QComboBox` ("Simulador", "AWS IAM"), botón de acción y cartel de estado desacoplado.
4. `src/auditoria_iam/ui/pages/results_page.py`: Clase `ResultsPage` con banner explicativo y `QTableWidget` de 5 columnas.
5. `src/auditoria_iam/ui/pages/history_page.py`: Clase `HistoryPage` con banner explicativo y `QTableWidget` de 5 columnas.
6. `src/auditoria_iam/ui/pages/settings_page.py`: Clase `SettingsPage` con formularios en modo solo lectura/demostrativo divididos en 3 secciones (umbral de inactividad de 90 días identificado como parámetro definido para el prototipo).
7. `src/auditoria_iam/ui/pages/__init__.py`: Módulo exportador de las 5 páginas.
8. `src/auditoria_iam/ui/main_window.py`: Clase `MainWindow` con integración del sidebar y `QStackedWidget`.
9. `main.py`: Punto de entrada raíz para el inicio de la aplicación de escritorio.
10. `tests/test_ui.py`: Suite de 9 pruebas automatizadas para la interfaz gráfica compatibles con entornos headless/offscreen.
11. `DOCUMENTACION_FASE_5_ENTREGA_1_INTERFAZ.md`: Presente informe técnico.

### Archivos Modificados:
1. `requirements.txt`: Se formalizaron las dependencias `boto3>=1.34.0` y `PySide6>=6.6.0`.
2. `src/auditoria_iam/ui/__init__.py`: Se exportó `MainWindow` para consumo público.

### Archivos No Modificados (Preservación Absoluta de Fases 1 a 4):
- Motor de auditoría y reglas: `engine.py`, `models.py`, `iam_001_access_control.py`, `iam_002_identity_management.py`, `iam_003_access_rights.py`, `iam_004_secure_authentication.py`.
- Fuentes de datos: `simulator.py`, `adapter.py`.
- Persistencia y configuración: `database/`, `config/`.
- Pruebas anteriores: `test_audit_engine.py`, `test_audit_models.py`, `test_rule_iam_001.py`, `test_rule_iam_002.py`, `test_rule_iam_003.py`, `test_rule_iam_004.py`, `test_simulator.py`, `test_aws_data_source.py`, `test_connection.py`, `test_repository.py`, `test_settings.py`.

---

## 4. Dependencias Incorporadas

- **`PySide6>=6.6.0`** (instalado: `6.12.0` con Qt 6.12.0): Biblioteca oficial de Qt para Python, requerida para el desarrollo de la interfaz gráfica nativa.
- **`boto3>=1.34.0`**: SDK oficial de AWS para Python (incorporado en Fase 4, Entrega 2).

Ambas dependencias se encuentran debidamente declaradas en el archivo `requirements.txt`.

---

## 5. Instrucciones para Ejecutar la Aplicación

Para iniciar la aplicación de escritorio en un entorno interactivo con servidor gráfico de ventanas:

```bash
# Opción 1: Mediante el entorno virtual activo
python main.py

# Opción 2: Especificando la ruta al ejecutable del entorno virtual
.\.venv\Scripts\python.exe main.py
```

### Ejecución en Entornos de Integración Continua o Headless:
En entornos sin servidor gráfico (servidores de CI/CD o terminales remotas), la interfaz puede ejecutarse o validarse configurando la plataforma offscreen de Qt:
```bash
set QT_QPA_PLATFORM=offscreen
python -c "from PySide6.QtWidgets import QApplication; from auditoria_iam.ui.main_window import MainWindow; app = QApplication([]); win = MainWindow(); print(win.windowTitle())"
```

---

## 6. Pruebas Automatizadas y Resultados

Se implementaron 9 pruebas unitarias específicas para la interfaz gráfica en `tests/test_ui.py`, diseñadas para operar en modo `offscreen` sin requerir interacción física del usuario.

### Detalle de las Pruebas de Interfaz (`tests/test_ui.py`):
1. `test_ui_modules_import`: Verifica la importación limpia de todos los módulos y componentes de la UI.
2. `test_main_window_creation`: Valida título (`"Sistema de Auditoría IAM"`), dimensiones mínimas (960x600) e iniciales (1200x750).
3. `test_five_sections_exist_in_stack`: Comprueba la existencia exacta de las cinco páginas en el `QStackedWidget`.
4. `test_navigation_between_screens`: Simula clics en los botones del sidebar y comprueba el cambio de índice en el stack.
5. `test_audit_page_source_selector`: Verifica las opciones disponibles en el selector de fuentes ("Simulador", "AWS IAM").
6. `test_audit_page_execute_button_does_not_invoke_engine`: Confirma que el clic en "Ejecutar auditoría" no dispara el motor ni genera excepciones en esta entrega.
7. `test_results_page_structure`: Valida los encabezados de las 5 columnas requeridas y el cartel de estado inicial vacío.
8. `test_history_page_structure`: Valida los encabezados de las 5 columnas requeridas y el cartel de estado inicial vacío.
9. `test_settings_page_sections_and_no_credentials`: Comprueba la existencia de las 3 secciones requeridas, la no exposición de credenciales y el umbral de 90 días.

### Resultado de la Suite Completa:
```text
============================= 155 passed in 2.07s =============================
- Pruebas del motor algorítmico y reglas (Fase 3):         80 passed
- Pruebas de base de datos y configuración (Fase 1 y 2):   16 passed
- Pruebas del simulador de datos (Fase 4, Entrega 1):       9 passed
- Pruebas del adaptador AWS IAM (Fase 4, Entrega 2):       41 passed
- Pruebas de la interfaz de escritorio (Fase 5, Entrega 1): 9 passed
Total: 155 pruebas aprobadas, 0 fallidas (100% de éxito).
```

---

## 7. Limitaciones Actuales y Desacoplamiento

Conforme a las directrices de la Fase 5, Entrega 1:
1. **Desacoplamiento Operativo:** El botón "Ejecutar auditoría" en `AuditPage` muestra un aviso informativo y no ejecuta el motor algorítmico `AuditEngine`. La conexión y orquestación corresponden a la Entrega 2 de la Fase 5.
2. **Persistencia No Vinculada a Vistas:** Las tablas de `ResultsPage` e `HistoryPage` presentan su estructura completa y un estado vacío por diseño; no consultan la base de datos MySQL ni manipulan registros de ejecuciones en esta entrega.
3. **Parámetros en Modo Demostrativo:** Los controles de `SettingsPage` se muestran en modo solo lectura y fines de visualización arquitectónica, sin almacenar modificaciones en disco ni realizar llamadas de red.

---

## 8. Confirmación Expresa de Restricciones Respetadas

Se certifica el cumplimiento estricto de las directrices fijadas para esta entrega:
- **No se modificó el motor de auditoría** (`engine.py`, `models.py` ni ninguna de las cuatro reglas `iam_001` a `iam_004`).
- **No se modificó el simulador de datos** (`simulator.py`).
- **No se modificó el adaptador AWS IAM** (`adapter.py`).
- **No se modificaron los esquemas ni tablas de la base de datos MySQL**.
- **No se realizaron llamadas de red a AWS** ni operaciones de escritura en AWS o MySQL.
- **Se mantuvieron intactas las 146 pruebas preexistentes**, sumando 9 pruebas de interfaz para un total de **155 pruebas satisfactorias**.
- **La entrega queda formalmente puesta a disposición para la revisión y aprobación por parte del usuario o líder del proyecto.**

