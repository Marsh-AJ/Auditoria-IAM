"""
Utilidades de iconografía vectorial minimalista (estilo Lucide / Feather)
para la interfaz gráfica empresarial del Sistema de Auditoría IAM.
Renderiza íconos SVG nítidos en alta densidad de píxeles (HiDPI 2x) para
botones, barra lateral e insignias de tarjetas (KPIs y controles ISO).
"""
from typing import Optional

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QWidget

try:
    from PySide6.QtSvg import QSvgRenderer
    _HAS_QTSVG = True
except ImportError:
    _HAS_QTSVG = False


# Definiciones de trazos SVG minimalistas (viewBox 0 0 24 24)
_SVG_PATHS: dict[str, str] = {
    "brand_shield": (
        '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
        '<path d="m9 12 2 2 4-4"/>'
    ),
    "dashboard": (
        '<rect x="3" y="3" width="7" height="7" rx="1.5"/>'
        '<rect x="14" y="3" width="7" height="7" rx="1.5"/>'
        '<rect x="14" y="14" width="7" height="7" rx="1.5"/>'
        '<rect x="3" y="14" width="7" height="7" rx="1.5"/>'
    ),
    "play_bolt": (
        '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>'
    ),
    "clipboard": (
        '<rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>'
        '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>'
        '<path d="m9 14 2 2 4-4"/>'
    ),
    "history": (
        '<circle cx="12" cy="12" r="9"/>'
        '<polyline points="12 7 12 12 15.5 14"/>'
    ),
    "layers": (
        '<polygon points="12 2 2 7 12 12 22 7 12 2"/>'
        '<polyline points="2 17 12 22 22 17"/>'
        '<polyline points="2 12 12 17 22 12"/>'
    ),
    "shield_check": (
        '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
        '<path d="m9 12 2 2 4-4"/>'
    ),
    "alert_triangle": (
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>'
        '<line x1="12" y1="9" x2="12" y2="13"/>'
        '<line x1="12" y1="17" x2="12.01" y2="17"/>'
    ),
    "info_circle": (
        '<circle cx="12" cy="12" r="9"/>'
        '<line x1="12" y1="16" x2="12" y2="12"/>'
        '<line x1="12" y1="8" x2="12.01" y2="8"/>'
    ),
    "refresh": (
        '<path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>'
        '<path d="M3 3v5h5"/>'
        '<path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>'
        '<path d="M16 16h5v5"/>'
    ),
    "plus": (
        '<line x1="12" y1="5" x2="12" y2="19"/>'
        '<line x1="5" y1="12" x2="19" y2="12"/>'
    ),
    "external_link": (
        '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
        '<polyline points="15 3 21 3 21 9"/>'
        '<line x1="10" y1="14" x2="21" y2="3"/>'
    ),
    "users_lock": (
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
        '<circle cx="9" cy="7" r="4"/>'
        '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/>'
        '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
    ),
    "user_check": (
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
        '<circle cx="9" cy="7" r="4"/>'
        '<polyline points="16 11 18 13 22 9"/>'
    ),
    "file_json": (
        '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        '<line x1="8" y1="13" x2="16" y2="13"/>'
        '<line x1="8" y1="17" x2="13" y2="17"/>'
    ),
    "key_round": (
        '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>'
        '<path d="M7 11V7a5 5 0 0 1 10 0v4"/>'
    ),
    "database": (
        '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
        '<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>'
        '<path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/>'
    ),
    "cloud": (
        '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>'
    ),
    "file_export": (
        '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        '<path d="M12 18v-6"/>'
        '<path d="m9 15 3 3 3-3"/>'
    ),
    "settings": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>'
    ),
}


def render_svg_pixmap(
    name: str,
    color: str = "#64748B",
    size: int = 18,
    stroke_width: float = 1.9,
) -> QPixmap:
    """Renderiza un ícono SVG a un QPixmap HiDPI (@2x) limpio y sin bordes dentados."""
    scale = 2
    px_size = size * scale
    pixmap = QPixmap(px_size, px_size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    inner = _SVG_PATHS.get(name, _SVG_PATHS["info_circle"])
    if _HAS_QTSVG:
        svg_xml = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
            f'viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">'
            f"{inner}</svg>"
        )
        renderer = QSvgRenderer(QByteArray(svg_xml.encode("utf-8")))
        renderer.render(painter, QRectF(0, 0, px_size, px_size))
    else:
        # Fallback geométrico minimalista si QtSvg no estuviese disponible
        pen = QPen(QColor(color))
        pen.setWidthF(stroke_width * scale)
        painter.setPen(pen)
        margin = px_size * 0.22
        painter.drawRoundedRect(
            QRectF(margin, margin, px_size - 2 * margin, px_size - 2 * margin),
            4.0,
            4.0,
        )

    painter.end()
    pixmap.setDevicePixelRatio(float(scale))
    return pixmap


def render_svg_icon(
    name: str,
    color: str = "#64748B",
    active_color: Optional[str] = None,
    disabled_color: str = "#94A3B8",
    size: int = 18,
    stroke_width: float = 1.9,
) -> QIcon:
    """Crea un QIcon con soporte para estados normal, activo (checked) y deshabilitado."""
    icon = QIcon()
    normal_px = render_svg_pixmap(name, color=color, size=size, stroke_width=stroke_width)
    icon.addPixmap(normal_px, QIcon.Normal, QIcon.Off)

    if active_color:
        active_px = render_svg_pixmap(name, color=active_color, size=size, stroke_width=stroke_width)
        icon.addPixmap(active_px, QIcon.Normal, QIcon.On)
        icon.addPixmap(active_px, QIcon.Active, QIcon.On)

    disabled_px = render_svg_pixmap(name, color=disabled_color, size=size, stroke_width=stroke_width)
    icon.addPixmap(disabled_px, QIcon.Disabled, QIcon.Off)
    return icon


def create_icon_badge(
    name: str,
    fg_color: str = "#172B46",
    bg_color: str = "#F1F5F9",
    border_color: str = "#E2E8F0",
    box_size: int = 36,
    icon_size: int = 18,
    radius: int = 9,
    parent: Optional[QWidget] = None,
) -> QLabel:
    """
    Construye un contenedor cuadrado redondeado con ícono centrado,
    inspirado en las tarjetas de métricas ejecutivas modernas.
    """
    badge = QLabel(parent)
    badge.setFixedSize(QSize(box_size, box_size))
    badge.setAlignment(Qt.AlignCenter)
    badge.setStyleSheet(
        f"background-color: {bg_color}; "
        f"border: 1px solid {border_color}; "
        f"border-radius: {radius}px;"
    )
    badge.setPixmap(render_svg_pixmap(name, color=fg_color, size=icon_size))
    return badge

