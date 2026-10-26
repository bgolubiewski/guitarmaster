# assets/svg_icons/svg_icons.py
from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QPixmap, QPainter, QTransform, QIcon
from PyQt6.QtSvg import QSvgRenderer

SVG_DICTIONARY = {
    "chevron_right": """
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
          stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" 
          class="lucide lucide-chevron-right-icon lucide-chevron-right"><path d="m9 18 6-6-6-6"/>
          </svg>
    """,

    "edit": """
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" 
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" 
        class="lucide lucide-pen-line-icon lucide-pen-line"><path d="M13 21h8"/>
        <path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/>
        </svg>
    """,

    "trash": """
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" 
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" 
        class="lucide lucide-trash2-icon lucide-trash-2"><path d="M10 11v6"/><path d="M14 11v6"/>
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
        </svg>
    """,

    "power": """
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" 
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" 
        class="lucide lucide-power-icon lucide-power"><path d="M12 2v10"/><path d="M18.4 6.6a9 9 0 1 1-12.77.04"/>
        </svg>
    """,

    "drag_handle": """
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" 
        fill="{color}" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="9" cy="12" r="1"/><circle cx="9" cy="5" r="1"/><circle cx="9" cy="19" r="1"/>
        <circle cx="15" cy="12" r="1"/><circle cx="15" cy="5" r="1"/><circle cx="15" cy="19" r="1"/>
        </svg>
    """,

    "save": """
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
          stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" 
          class="lucide lucide-save-icon lucide-save"><path d="M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/>
          <path d="M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7"/><path d="M7 3v4a1 1 0 0 0 1 1h7"/>
          </svg>
    """
}

COLORS = {
    "background": "#EAE5D9",
    "surface": "#DFD8CB",
    "surface_hover": "#CECBC7",
    "surface_variant": "#F2EEE5",

    "card_bg": "#FAF8F5",
    "card_bg_hover": "#FFFFFF",
    "card_border": "#CFC7B8",

    "primary": "#8C3A4A",       
    "primary_hover": "#6E2B38",
    "accent": "#C06A3B",    

    "text": "#2B303A",
    "text_secondary": "#5C6573",
    "text_on_primary": "#FFFFFF",

    "border": "#C4BCAF",
    "danger": "#B52A4A",
}

ICON_COLORS = {
    "icon_default": "#5C6573",
    "icon_active": "#8C3A4A",
    "icon_hover": "#6E2B38",
    "icon_disabled": "#A89E8F",
    "icon_danger": "#B52A4A",
    "icon_danger_hover": "#8C1E34",
}

def get_svg_pixmap(icon_name: str, size: int = 16, color: str = "light_grey", rotation: float = 0):
    """Generates QPixmap with of a given SVG from the dictionary."""

    hex_color = ICON_COLORS.get(color, COLORS.get(color, color))

    raw_svg = SVG_DICTIONARY.get(icon_name, '')
    if not raw_svg:
        # transparent map
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        return pix
    
    formatted_svg = raw_svg.format(color = hex_color)
    renderer = QSvgRenderer(QByteArray(formatted_svg.encode('utf-8')))

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    if not renderer.isValid():
        print(f"[SVG Error] Invalid SVG syntax for icon: '{icon_name}'")
        return pixmap

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    if rotation != 0:
        transform = QTransform().rotate(rotation)
        pixmap = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)

    return pixmap

def get_svg_icon(icon_name: str, size: int = 16, color: str = "icon_default",
                  hover_color: str = None, rotation: float = 0) -> QIcon:
    """Return QIcon object for QPushButton."""
    icon = QIcon()
    pixmap_normal = get_svg_pixmap(icon_name, size, color, rotation)
    icon.addPixmap(pixmap_normal, QIcon.Mode.Normal)

    if hover_color:
        pixmap_hover = get_svg_pixmap(icon_name, size, hover_color, rotation)
        icon.addPixmap(pixmap_hover, QIcon.Mode.Active)

    return icon

