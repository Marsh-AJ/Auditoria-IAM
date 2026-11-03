"""
Estilos visuales (QSS) para la aplicación de escritorio del Sistema de Auditoría IAM.
Diseño empresarial moderno inspirado en consolas ejecutivas SaaS de ciberseguridad
y sistemas de gestión corporativa (paleta sobria, tarjetas de radio suave y tablas limpias):
  - Barra lateral profunda (Calm Navy): #111C2D
  - Azul primario institucional: #172B46
  - Azul acento secundario: #294F78 / #4C9AFF
  - Lienzo de trabajo (Canvas): #F5F7FA
  - Tarjetas y superficies: #FFFFFF (borde #E5E9F0, radio 12px)
  - Verde conforme: #16845B
  - Rojo hallazgo: #D64545
  - Ámbar no evaluable: #D49A32
"""

CYBER_SECURITY_STYLE = """
/* Reset y estilos base */
QMainWindow {
    background-color: #F5F7FA;
    color: #0F172A;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}

QWidget {
    color: #0F172A;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}

QLabel {
    background-color: transparent;
    border: none;
}

/* Área central y scroll */
QScrollArea {
    background-color: #F5F7FA;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: #F5F7FA;
}

/* Barra superior de contexto (Breadcrumb Bar) */
QFrame#top_header_bar {
    background-color: #FFFFFF;
    border: none;
    border-bottom: 1px solid #E5E9F0;
    min-height: 50px;
    max-height: 50px;
}

/* Panel lateral (Calm Navy Sidebar) */
QFrame#sidebar {
    background-color: #111C2D;
    border: none;
    border-right: 1px solid #1B2B42;
    min-width: 248px;
    max-width: 248px;
}

QLabel#brand_title {
    color: #FFFFFF;
    font-size: 14.5px;
    font-weight: 700;
    letter-spacing: 0.2px;
}

QLabel#brand_subtitle {
    color: #6E829F;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.9px;
    font-weight: 600;
}

QLabel#sidebar_section_label {
    color: #5B708B;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.1px;
    padding: 8px 10px 4px 10px;
}

/* Botones de navegación del sidebar */
QPushButton.nav_button {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 8px;
    padding: 10px 12px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
    margin: 1px 0px;
}

QPushButton.nav_button:hover {
    background-color: #18273E;
    color: #F1F5F9;
}

QPushButton.nav_button:checked {
    background-color: #1D304D;
    color: #FFFFFF;
    font-weight: 600;
    border-left: 3px solid #4C9AFF;
}

/* Contenedores de tarjetas modernas (sin propagar bordes a hijos) */
QFrame.card {
    background-color: #FFFFFF;
    border: 1px solid #E5E9F0;
    border-radius: 12px;
}

QFrame.subcard {
    background-color: #F8FAFC;
    border: 1px solid #EDF2F7;
    border-radius: 9px;
}

/* Encabezados y tipografía jerárquica */
QLabel.page_title {
    font-size: 22px;
    font-weight: 700;
    color: #0F172A;
}

QLabel.page_subtitle {
    font-size: 13px;
    color: #64748B;
}

QLabel.card_header_title {
    font-size: 14.5px;
    font-weight: 700;
    color: #0F172A;
}

/* Controles de formulario */
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #D8E0EA;
    border-radius: 8px;
    padding: 8px 12px;
    color: #0F172A;
    min-height: 24px;
    font-size: 13px;
}

QComboBox:hover {
    border-color: #94A3B8;
}

QComboBox:focus {
    border: 1px solid #294F78;
}

QComboBox::drop-down {
    border: none;
    padding-right: 12px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #D8E0EA;
    border-radius: 8px;
    selection-background-color: #EFF6FF;
    selection-color: #0F172A;
    color: #0F172A;
    padding: 4px;
    outline: none;
}

QLineEdit, QTextEdit {
    background-color: #FFFFFF;
    border: 1px solid #D8E0EA;
    border-radius: 8px;
    padding: 8px 12px;
    color: #0F172A;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: #294F78;
}

/* Sistema unificado de botones */
QPushButton.primary_button {
    background-color: #172B46;
    color: #FFFFFF;
    border: 1px solid #172B46;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 12.5px;
}

QPushButton.primary_button:hover {
    background-color: #223D63;
    border-color: #223D63;
}

QPushButton.primary_button:pressed {
    background-color: #0F1D30;
}

QPushButton.primary_button:disabled {
    background-color: #F1F5F9;
    color: #94A3B8;
    border: 1px solid #E2E8F0;
}

QPushButton.secondary_button {
    background-color: #FFFFFF;
    color: #1E293B;
    border: 1px solid #D8E0EA;
    border-radius: 8px;
    padding: 8px 15px;
    font-size: 12.5px;
    font-weight: 600;
}

QPushButton.secondary_button:hover {
    background-color: #F8FAFC;
    border-color: #B8C4D4;
    color: #0F172A;
}

QPushButton.secondary_button:pressed {
    background-color: #F1F5F9;
}

QPushButton.secondary_button:disabled {
    background-color: #F8FAFC;
    color: #94A3B8;
    border: 1px solid #E5E9F0;
}

/* Tablas empresariales limpias (sin rejilla vertical pesada) */
QTableWidget {
    background-color: #FFFFFF;
    alternate-background-color: #FAFBFD;
    border: none;
    gridline-color: transparent;
    color: #1E293B;
    font-size: 12.5px;
    selection-background-color: #EFF6FF;
    selection-color: #0F172A;
    outline: none;
}

QTableWidget::item {
    padding: 10px 14px;
    border-bottom: 1px solid #F1F5F9;
}

QTableWidget::item:selected {
    background-color: #EFF6FF;
    color: #0F172A;
}

QHeaderView::section {
    background-color: #F8FAFC;
    color: #64748B;
    padding: 10px 14px;
    border: none;
    border-top: 1px solid #EDF2F7;
    border-bottom: 1px solid #E5E9F0;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

/* Barras de progreso horizontales (estilo utilización por regla) */
QProgressBar {
    background-color: #EDF2F7;
    border: none;
    border-radius: 3px;
    max-height: 6px;
    min-height: 6px;
}

QProgressBar::chunk {
    background-color: #294F78;
    border-radius: 3px;
}

/* Tooltips legibles */
QToolTip {
    background-color: #0F172A;
    color: #F8FAFC;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* Barras de desplazamiento discretas */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 8px;
    margin: 2px 2px 2px 0px;
}

QScrollBar::handle:vertical {
    background: #CBD5E1;
    min-height: 28px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 8px;
    margin: 0px 2px 2px 2px;
}

QScrollBar::handle:horizontal {
    background: #CBD5E1;
    min-width: 28px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #94A3B8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""

# Alias semántico
ENTERPRISE_STYLE = CYBER_SECURITY_STYLE
