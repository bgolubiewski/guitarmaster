# ui/widgets/chord_library/chord_card_widget.py
from typing import Any, Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, QMimeData, QPoint, QEvent, QSize
from PyQt6.QtGui import QDrag, QMouseEvent, QResizeEvent, QEnterEvent

from ui.widgets.chord_editor.chord_diagram_widget import ChordDiagramWidget
from models.chord import Chord
from assets.svg_icons.svg_icons import get_svg_icon
from assets.svg_icons.svg_hover_widgets import HoverIconButton

class DragHandle(QPushButton):
    """
    A custom drag-button handle configured exclusively for handling chord card drag triggers.
    """
    def __init__(self, parent_card: 'ChordCardWidget') -> None:
        super().__init__('', parent_card)
        self.card: 'ChordCardWidget' = parent_card
        self.drag_start_pos: QPoint = QPoint()

        self.setObjectName("ChordCardDragHandle")

        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        
        self.icon_normal = get_svg_icon('drag_handle', size=16, color="icon_default")
        self.icon_hover = get_svg_icon('drag_handle', size=16, color="icon_hover")
        self.setIcon(self.icon_normal)
        self.setIconSize(QSize(16, 16))
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def enterEvent(self, event: QEnterEvent) -> None:
        self.setIcon(self.icon_hover)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.setIcon(self.icon_normal)
        self.update()
        super().leaveEvent(event) 

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Check the Manhattan length to prevent accidental micro-drags during clicks
            if (event.position().toPoint() - self.drag_start_pos).manhattanLength() > 5:
                self.card.start_drag(event.position().toPoint())
        super().mouseMoveEvent(event)

class ChordCardWidget(QFrame):
    def __init__(self, chord: Chord, on_edit_click: Callable[[Chord], None], library_view: Any) -> None:
        """
        Displays a compact chord tile. Handles preset scaling sizes, hover boundaries, 
        and toggles visibility for control layers during hover triggers.
        
        :param chord: Chord object model reference.
        :param on_edit_click: Callback opening the chord editor window.
        :param library_view: Reference to the parent LibraryView layer.
        """
        super().__init__()
        self.chord: Chord = chord
        self.on_edit_click: Callable[[Chord], None] = on_edit_click
        self.library_view: Any = library_view

        self.setMouseTracking(True)
        self.setObjectName("ChordCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        # Pull layout geometries bound directly to UI view sizing properties
        card_w, card_h = self.library_view.get_current_card_size()
        self.setFixedSize(card_w, card_h)

        # Structural setup layout mapping
        layout = QVBoxLayout(self)
        top_content_margin = int(card_h * 0.13) 
        layout.setContentsMargins(10, top_content_margin, 10, 10)
        layout.setSpacing(5)

        # Title component
        self.title_label = QLabel(chord.name)
        self.title_label.setObjectName("ChordCardTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setProperty("small", card_w < 130)
        layout.addWidget(self.title_label)

        # Vector diagram child node initialization
        self.diagram = ChordDiagramWidget()
        self.diagram.is_editing = False
        self.diagram.set_chord(chord)
        layout.addWidget(self.diagram)

        # System Action Overlay Button: Edit
        self.btn_edit = HoverIconButton('edit', size=16, color="icon_default",
                                        hover_color="icon_hover", parent=self)
        self.btn_edit.setObjectName("ChordCardEditButton")
        self.btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_edit.setFixedSize(24, 24)
        self.btn_edit.hide()
        self.btn_edit.clicked.connect(lambda: self.on_edit_click(self.chord))

        # Dynamic Handle Button: Drag Trigger
        self.btn_drag = DragHandle(self)
        self.btn_drag.setFixedSize(24, 24)
        self.btn_drag.hide()
        self.btn_drag.move(8, 8)

        # Push elements to their coordinate vectors
        self._reposition_edit_button()

    def _reposition_edit_button(self) -> None:
        """Calculates precise positioning vectors keeping the edit node aligned right."""
        margin = 8
        x_edit = self.width() - self.btn_edit.width() - margin
        self.btn_edit.move(x_edit, margin)

    def start_drag(self, hotspot_offset: QPoint) -> None:
        """Initializes a native layout drag pipeline session packaging structural MIME items."""
        if self.library_view.interaction_locked: 
            return
        
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.chord.name)
        drag.setMimeData(mime_data)

        pixmap = self.grab()
        drag.setPixmap(pixmap)
        
        # Pin alignment hotspot accurately matching local card space vectors
        drag.setHotSpot(hotspot_offset + self.btn_drag.pos())

        self.library_view.register_drag_start(self)
        drag.exec(Qt.DropAction.MoveAction)
        self.library_view.register_drag_end()

    def enterEvent(self, event: QEnterEvent) -> None:
        if not self.library_view.interaction_locked:
            self.btn_edit.show()
            self.btn_drag.show()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.btn_edit.hide()
        self.btn_drag.hide()
        super().leaveEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Tracks parent resizing changes to protect layouts across scaling presets."""
        super().resizeEvent(event)
        card_w = self.width()
        self.title_label.setProperty("small", card_w < 130)
        self.title_label.style().unpolish(self.title_label)
        self.title_label.style().polish(self.title_label)
        
        self._reposition_edit_button()