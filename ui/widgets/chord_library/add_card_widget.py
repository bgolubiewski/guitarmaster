# ui/widgets/chord_library/add_card_widget.py
from typing import Any, Callable
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent

class AddCardWidget(QFrame):
    """
    A custom tile that acts as an inline '+ add' placeholder inside 
    individual categories in the chord library grid layout.
    """
    def __init__(self, category: str, on_click_callback: Callable[[str], None], library_view: Any) -> None:
        super().__init__()
        self.category: str = category
        self.on_click: Callable[[str], None] = on_click_callback
        self.library_view: Any = library_view

        self.setObjectName("AddCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Build clean centralized layout tree
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Initialize explicit components to expose them to cascade style updates
        self.plus_label = QLabel('+')
        self.plus_label.setObjectName("PlusLabel")
        self.plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.plus_label)

        self.txt_label = QLabel("Add new chord")
        self.txt_label.setObjectName("TxtLabel")
        self.txt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.txt_label)

        # Trigger dynamic dimension and styling calculations
        self.update_card_size()

    def update_card_size(self) -> None:
        """
        Dynamically refreshes geometric boundaries and reactive typography constraints 
        based on active global library viewport presets (S, M, L).
        """
        card_w, card_h = self.library_view.get_current_card_size()
        self.setFixedSize(card_w, card_h)

        is_small = card_w < 130
        if self.property("small") != is_small:
            self.setProperty("small", is_small)
            self.style().unpolish(self)
            self.style().polish(self)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Triggers the creation pipeline callback when the user clicks the card framework.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # Drop interaction routing if parent container view locks current states (Read-Only)
            if self.library_view.interaction_locked:
                return
            self.on_click(self.category)
            
        super().mousePressEvent(event)