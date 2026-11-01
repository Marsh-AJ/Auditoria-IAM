"""
Estilos visuales (QSS) para la aplicación de escritorio del Sistema de Auditoría IAM.
Diseño moderno, profesional y ergonómico con temática de ciberseguridad.
"""

CYBER_SECURITY_STYLE = """
/* Reset y estilos generales */
QMainWindow, QWidget {
    background-color: #0f172a;
    color: #f8fafc;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

/* Panel lateral (Sidebar) */
#sidebar {
    background-color: #090d16;
    border-right: 1px solid #1e293b;
    min-width: 240px;
    max-width: 240px;
}

#brand_title {
    color: #38bdf8;
    font-size: 16px;
    font-weight: bold;
    padding: 10px 0px 2px 0px;
}

#brand_subtitle {
    color: #64748b;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding-bottom: 12px;
    border-bottom: 1px solid #1e293b;
}

/* Botones de navegación del sidebar */
QPushButton.nav_button {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}

QPushButton.nav_button:hover {
    background-color: #1e293b;
    color: #f8fafc;
}

QPushButton.nav_button:checked {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: bold;
}

/* Tarjetas y Contenedores */
QFrame.card {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 16px;
}

QFrame.badge_card {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 10px;
}

/* Encabezados de página */
QLabel.page_title {
    font-size: 20px;
    font-weight: bold;
    color: #f8fafc;
    padding-bottom: 4px;
}

QLabel.page_subtitle {
    font-size: 13px;
    color: #94a3b8;
    padding-bottom: 12px;
}

QLabel.section_header {
    font-size: 14px;
    font-weight: 600;
    color: #38bdf8;
    margin-top: 8px;
    margin-bottom: 4px;
}

/* Formularios y controles */
QComboBox {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 12px;
    color: #f8fafc;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #38bdf8;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #1e293b;
    border: 1px solid #334155;
    selection-background-color: #0284c7;
    color: #f8fafc;
}

QLineEdit, QTextEdit {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 12px;
    color: #f8fafc;
}

/* Botones principales y de acción */
QPushButton.primary_button {
    background-color: #0284c7;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton.primary_button:hover {
    background-color: #0369a1;
}

QPushButton.primary_button:disabled {
    background-color: #334155;
    color: #64748b;
}

/* Tablas */
QTableWidget {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    gridline-color: #1e293b;
    color: #f8fafc;
}

QHeaderView::section {
    background-color: #1e293b;
    color: #38bdf8;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #334155;
    font-weight: 600;
}

/* Badges / Etiquetas de Estado */
QLabel.badge_iso {
    background-color: #0369a1;
    color: #e0f2fe;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: bold;
}

QLabel.status_banner {
    background-color: #1e293b;
    border-left: 4px solid #38bdf8;
    padding: 12px;
    border-radius: 4px;
    color: #cbd5e1;
}
"""

