# assets/svg_icons/svg_hover_widgets.py
from PyQt6.QtWidgets import QPushButton, QLabel
from PyQt6.QtCore import QSize, Qt, QEvent

from assets.svg_icons.svg_icons import get_svg_icon

class HoverIconButton(QPushButton):
    """QPushButton which changes the SVG icon color upon mouse hover."""
    def __init__(
        self, 
        icon_name: str, 
        size: int = 16, 
        color: str = "icon_muted", 
        hover_color: str = None,
        rotation: float = 0,
        parent=None):
        super().__init__(parent)

        self.icon_size_px = size
        self.set_icon_config(icon_name, color, hover_color)
        
    def set_icon_config(self, icon_name: str, color: str = "light_grey", hover_color: str = None) -> None:
        """Dynamicaly changes the SVG icon and it's hover color."""
        self.icon_normal = get_svg_icon(icon_name, size=self.icon_size_px, color=color)
        self.icon_hover = (
            get_svg_icon(icon_name, size=self.icon_size_px, color=hover_color) 
            if hover_color else self.icon_normal)
        self.setIcon(self.icon_normal)
        self.setIconSize(QSize(self.icon_size_px, self.icon_size_px))

    def enterEvent(self, event: QEvent) -> None:
        self.setIcon(self.icon_hover)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.setIcon(self.icon_normal)
        super().leaveEvent(event)

class HoverLabel(QLabel):
    """QLabel which informs about hover state."""
    def __init__(self, on_hover_callback=None, parent=None) -> None:
        super().__init__(parent)
        self.on_hover_callback = on_hover_callback

    def enterEvent(self, event: QEvent) -> None:
        if self.on_hover_callback:
            self.on_hover_callback(True)  # True = kursor wszedł
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        if self.on_hover_callback:
            self.on_hover_callback(False) # False = kursor wyszedł
        super().leaveEvent(event)