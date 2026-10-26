# assets/theme.py
from pathlib import Path
from PyQt6.QtWidgets import QApplication

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

def load_stylesheet(app: QApplication, relative_path: str = "assets/styles/style.qss") -> None:
    """
    Reads the QSS file from disk and applies it globally to the QApplication instance.
    """
    base_dir = Path(__file__).resolve().parent.parent
    qss_path = base_dir / relative_path

    if not qss_path.exists():
        print(f"[Warning] Stylesheet not found at: {qss_path}")
        return

    with open(qss_path, "r", encoding="utf-8") as file:
        formatted_qss = file.read()

    theme_merged = {**COLORS, **ICON_COLORS}
    for key, value in theme_merged.items():
        formatted_qss = formatted_qss.replace(f"{{{key}}}", value)

    app.setStyleSheet(formatted_qss)