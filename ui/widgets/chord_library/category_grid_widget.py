# ui/widgets/chord_library/category_grid_widget.py
from typing import Any, Optional
from PyQt6.QtWidgets import QFrame, QGridLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDragMoveEvent, QDragLeaveEvent, QDropEvent

class CategoryGridWidget(QFrame):
    """
    Manages the live preview grid layout of chord cards with visual drag-and-drop feedback states.
    """
    def __init__(self, category: str, library_view: Any) -> None:
        super().__init__()
        self.category: str = category
        self.library_view: Any = library_view
        self.setAcceptDrops(True)

        self.setObjectName('CategoryGrid')

        self.grid_layout = QGridLayout(self)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.grid_layout.setContentsMargins(15, 15, 15, 15)
        self.grid_layout.setHorizontalSpacing(9)
        self.grid_layout.setVerticalSpacing(9)

        self.add_card: Optional[QWidget] = None
        self.original_cards: list[QWidget] = []
        self.current_cards: list[QWidget] = []
        self.last_target_index: Optional[int] = None

        self.set_style_state('normal')

    def set_style_state(self, state: str) -> None:
        """Updates dynamic QSS property state and re-polishes stylesheet selectors."""
        self.setProperty("dragState", state)
        self.style().unpolish(self)
        self.style().polish(self)

    def update_grid_layout(self) -> None:
        """Flushes the layout pipeline and maps active card configurations to grid nodes."""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            # Layout items are handled by the view state swap, we just detach them here
            if item is None:
                continue

        if self.add_card:
            self.grid_layout.addWidget(self.add_card, 0, 0)

        COLUMNS_COUNT = 5
        for index, card in enumerate(self.current_cards):
            grid_index = index + 1
            row = grid_index // COLUMNS_COUNT
            col = grid_index % COLUMNS_COUNT
            self.grid_layout.addWidget(card, row, col)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.set_style_state('drag_hover')
            self.current_cards = list(self.original_cards)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        event.acceptProposedAction()
        dragged_widget = self.library_view.active_dragged_card
        if not dragged_widget:
            return
        
        # Pull dynamic sizes calculated by presets (S, M, L) from the parent frame
        card_w, card_h = self.library_view.get_current_card_size()
        cell_width = card_w + 12
        cell_height = card_h + 12

        pos = event.position()
        col = int(pos.x() // cell_width)
        row = int(pos.y() // cell_height)

        COLUMNS_COUNT = 5
        max_col = COLUMNS_COUNT - 1
        if col > max_col: 
            col = max_col
        if col < 0: 
            col = 0
        if row < 0: 
            row = 0

        target_grid_index = row * COLUMNS_COUNT + col
        
        # Safe extraction protecting index 0 from transforming into pythonic backward tracking (-1)
        target_list_index = max(0, target_grid_index - 1)

        max_idx = len(self.original_cards)
        if dragged_widget not in self.original_cards:
            max_idx += 1

        if target_list_index > max_idx:
            target_list_index = max(0, max_idx - 1)

        if self.last_target_index != target_list_index: 
            self.last_target_index = target_list_index

            temp_list = [c for c in self.original_cards if c != dragged_widget]
            temp_list.insert(target_list_index, dragged_widget)

            self.current_cards = temp_list
            self.update_grid_layout()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.set_style_state('drag_active')
        self.current_cards = list(self.original_cards)
        self.last_target_index = None
        self.update_grid_layout()
    
    def dropEvent(self, event: QDropEvent) -> None:
        dragged_widget = self.library_view.active_dragged_card
        if not dragged_widget:
            return
        
        target_list_index = self.last_target_index if self.last_target_index is not None else 0

        self.library_view.finalize_chord_move(
            dragged_widget.chord,
            dragged_widget.chord.category,
            self.category,
            target_list_index
        )
        event.acceptProposedAction()