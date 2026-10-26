# ui/widgets/chord_library/library_grid.py
from typing import Optional, Any, Callable
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFrame, QApplication, QLayout
from PyQt6.QtCore import Qt

from ui.widgets.chord_library.chord_card_widget import ChordCardWidget
from ui.widgets.chord_library.add_card_widget import AddCardWidget
from ui.widgets.chord_library.category_grid_widget import CategoryGridWidget
from ui.widgets.chord_library.category_header_widget import CategoryHeaderWidget
from ui.widgets.chord_library.legend_widget import LegendItemWidget, LegendContainerWidget
from models.chord import Chord
from assets.svg_icons.svg_hover_widgets import HoverIconButton

class LibraryGrid(QWidget):
    # Hinting UI elements loaded from the .ui file for better IDE support
    sidebarWidget: QFrame
    scrollArea: Any
    scrollAreaWidgetContents: QWidget

    def __init__(self, service: Any, on_edit_request: Callable[[Chord, bool], None]) -> None:
        super().__init__()
        uic.loadUi('ui/designer/library_window.ui', self)
        
        self.service: Any = service
        self.on_edit_request: Callable[[Chord, bool], None] = on_edit_request

        if self.layout() is not None:
            self.layout().setContentsMargins(0, 0, 0, 0)
            self.layout().setSpacing(0)  # opcjonalnie: brak przerwy między sidebarem a siatką

        self.setObjectName('LibraryGrid')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.sidebarWidget.setMinimumWidth(180)
        self.sidebarWidget.setMaximumWidth(240)
        self.sidebarWidget.setObjectName("sidebarWidget")
        self.sidebarWidget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.section_headers: dict[str, CategoryHeaderWidget] = {}
        self.category_grids: dict[str, CategoryGridWidget] = {}
        self.active_dragged_card: Optional[QWidget] = None
        self.active_dragged_legend: Optional[QWidget] = None

        self.interaction_locked: bool = False
        self.current_size_preset: str = 'M'
        self.CARD_PRESETS: dict[str, tuple[int, int]] = {
            'S': (120, 170),
            'M': (160, 220),
            'L': (200, 270)
        }

        self.collapsed_categories: set[str] = set()
        self.categories_order: list[str] = []
        self.editing_category_name: Optional[str] = None

        # Initialize main scroll area layout safely
        if self.scrollAreaWidgetContents.layout() is None:
            self.scroll_layout = QVBoxLayout(self.scrollAreaWidgetContents)
        else:
            self.scroll_layout = self.scrollAreaWidgetContents.layout()

        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setContentsMargins(15, 15, 15, 15)
        self.scroll_layout.setSpacing(10)

        # Initialize side navigation main layout
        if self.sidebarWidget.layout() is None:
            self.sidebar_layout = QVBoxLayout(self.sidebarWidget)
        else:
            self.sidebar_layout = self.sidebarWidget.layout()
        self.sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.sidebar_layout.setSpacing(0)

        # Build structural persistent containers inside the sidebar to prevent layout leaks
        self._setup_persistent_sidebar_skeleton()
        self._setup_floating_size_selector()

        # Perform initial structural data bind
        self.refresh_library()

    def _setup_persistent_sidebar_skeleton(self) -> None:
        """Creates the structural layout for the sidebar so dynamic content doesn't pile up."""
        # Dynamic container for categories and legends
        self.dynamic_sidebar_container = QWidget()
        self.dynamic_sidebar_layout = QVBoxLayout(self.dynamic_sidebar_container)
        self.dynamic_sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.dynamic_sidebar_layout.setSpacing(0)
        self.dynamic_sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.sidebar_layout.addWidget(self.dynamic_sidebar_container)
        self.sidebar_layout.addStretch(1)
        
        # Add a single, persistent footer instance
        self._build_sidebar_footer()

    def _setup_floating_size_selector(self) -> None:
        """Initializes the floating chord card selector overlay."""
        self.size_selector_container = QFrame(self)
        self.size_selector_container.setObjectName("sizeSelectorFrame")
        
        sel_layout = QHBoxLayout(self.size_selector_container)
        sel_layout.setContentsMargins(10, 4, 10, 4)
        sel_layout.setSpacing(6)

        lbl = QLabel("Layout size:")
        lbl.setObjectName("sizeSelectorLabel")
        
        self.combo_size = QComboBox()
        self.combo_size.setObjectName("sizeSelectorCombo")
        self.combo_size.addItems(["Small", "Medium", "Large"])

        preset_map = {'S': 0, 'M': 1, 'L': 2}
        self.combo_size.setCurrentIndex(preset_map[self.current_size_preset])
        self.combo_size.currentIndexChanged.connect(self._on_size_combo_changed)

        sel_layout.addWidget(lbl)
        sel_layout.addWidget(self.combo_size)
        self.size_selector_container.adjustSize()

    def set_interaction_locked(self, locked: bool) -> None:
        """Blocks interaction with library components during editing modes."""
        self.interaction_locked = locked
        self.refresh_library()

    def get_current_card_size(self) -> tuple[int, int]:
        """Returns a tuple (width, height) representing the active sizing matrix preset."""
        return self.CARD_PRESETS.get(self.current_size_preset, (160, 220))

    def register_drag_start(self, card_widget: QWidget) -> None:
        """Notifies the parent view grid systems that a physical card drag operation has initialized."""
        self.active_dragged_card = card_widget
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item is None:
                continue
            w = item.widget()

            if isinstance(w, CategoryGridWidget):
                w.set_style_state('drag_active')

                if card_widget in w.original_cards:
                    w.original_cards.remove(card_widget)
                    w.current_cards = list(w.current_cards)
                    w.update_grid_layout()

    def _on_size_combo_changed(self, index: int) -> None:
        reverse_map = {0: 'S', 1: 'M', 2: 'L'}
        self.current_size_preset = reverse_map.get(index, 'M')
        self.refresh_library()

    def resizeEvent(self, event: Any) -> None:
        """PyQt override repositioning the floating size widget context overlay dynamically."""
        super().resizeEvent(event)
        if hasattr(self, 'size_selector_container') and self.size_selector_container:
            sa_rect = self.scrollArea.geometry()
            x = sa_rect.right() - self.size_selector_container.width() - 25
            y = sa_rect.top() + 15
            self.size_selector_container.move(x, y)
            self.size_selector_container.raise_()

    def register_drag_end(self) -> None:
        """Resets dynamic overlay properties once the mouse button drops a card."""
        self.active_dragged_card = None
        self.refresh_library()

    def finalize_chord_move(self, chord: Chord, old_category: str, new_category: str, target_index: int) -> None:
        """Commits list-ordering structural database writes via the service tier layer."""
        self.service.move_chord_position(chord, new_category, target_index)
        self.refresh_library()

    def _clear_layout(self, layout: Optional[QLayout]) -> None:
        """Safely disposes of active layout tree hierarchies down to their leaf nodes to avoid memory leaks."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self._clear_layout(item.layout())

    def toggle_category_by_header(self, category: str, header_widget: CategoryHeaderWidget) -> None:
        """Toggles visibility of a specific category grid without rebuilding the layout tree."""
        grid_widget = self.category_grids.get(category)
        if not grid_widget: 
            return
        
        if category in self.collapsed_categories:
            self.collapsed_categories.remove(category)
            grid_widget.show()
            header_widget.is_collapsed = False
        else:
            self.collapsed_categories.add(category)
            grid_widget.hide()
            header_widget.is_collapsed = True

        header_widget.update_arrow_icon()

        if self.scrollArea.widget():
            self.scrollArea.widget().adjustSize()

    def add_category(self, category_name: str) -> None:
        """
        Adds an empty category to service and saves.
        """
        category_name = category_name.strip()
        if category_name:
            self.service.add_category(category_name)
            if category_name not in self.categories_order:
                self.categories_order.append(category_name)

            self.service.reorder_categories(self.categories_order)
            self.refresh_library()

    def rename_category(self, old_name: str, new_name: str) -> None:
        """Updates internal dictionary keys and persistence layer labels for a category identity."""
        old_name = old_name.strip()
        new_name = new_name.strip()
        
        if not new_name or old_name == new_name:
            return

        if old_name in self.categories_order:
            idx = self.categories_order.index(old_name)
            self.categories_order[idx] = new_name

        if old_name in self.collapsed_categories:
            self.collapsed_categories.remove(old_name)
            self.collapsed_categories.add(new_name)

        self.service.reorder_categories(self.categories_order)
        self.refresh_library()

    def delete_category(self, category_name: str) -> None:
        """Deletes a targeted category section and all its contained children."""
        self.service.delete_category(category_name)
        
        if category_name in self.collapsed_categories:
            self.collapsed_categories.remove(category_name)
        
        if category_name in self.categories_order:
            self.categories_order.remove(category_name)

        self.refresh_library()

    def finalize_category_reorder(self, new_order: list[str]) -> None:
        """Saves a modified section layout configuration to the service tier."""
        self.categories_order = new_order
        self.service.reorder_categories(new_order)
        self.refresh_library()

    def prompt_new_category(self) -> None:
        """Appends a placeholder section directly into active memory arrays and activates focus states."""
        if self.interaction_locked:
            return
        
        base_name = "Your new category"
        new_name = base_name
        counter = 2
        
        while new_name in self.categories_order:
            new_name = f"{base_name} ({counter})"
            counter += 1
        
        self.service.add_category(new_name)
        self.service.save_data_to_database()

        if new_name not in self.categories_order:
            self.categories_order.append(new_name)
        
        self.editing_category_name = new_name
        self.refresh_library()
        self.scroll_to_section(new_name)

    def refresh_library(self) -> None:
        """Performs a full re-bind, redrawing internal structural lists from scratch."""
        scroll_bar = self.scrollArea.verticalScrollBar()
        saved_scroll_position = scroll_bar.value()

        new_contents = QWidget()
        new_contents.setObjectName("scrollAreaWidgetContents")
        
        new_layout = QVBoxLayout(new_contents)
        new_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        new_layout.setContentsMargins(15, 15, 15, 15)
        new_layout.setSpacing(10)
        self.scroll_layout = new_layout

        # Clear volatile parts of the sidebar to avoid layout accumulation leaks
        self._clear_layout(self.dynamic_sidebar_layout)
        self.section_headers.clear()
        self.category_grids.clear()

        # Build Legend / Side Navigation Header
        legend_title = QLabel("JUMP TO")
        legend_title.setObjectName("sidebarLegendTitle")
        self.dynamic_sidebar_layout.addWidget(legend_title)

        self.legend_container = LegendContainerWidget(self)
        self.dynamic_sidebar_layout.addWidget(self.legend_container)

        grouped_chords = self.service.get_chords_grouped_by_category()
        service_categories = list(grouped_chords.keys())

        if not self.categories_order:
            self.categories_order = list(service_categories)
        else:
            valid_categories = set(service_categories)
            if self.editing_category_name:
                valid_categories.add(self.editing_category_name)
            
            self.categories_order = [c for c in self.categories_order if c in valid_categories]
            for c in service_categories:
                if c not in self.categories_order:
                    self.categories_order.append(c)

        # Render sections onto grid pipelines sequentially
        for category in self.categories_order:
            chords_list = grouped_chords.get(category, [])
            is_collapsed = category in self.collapsed_categories

            # Header binding logic
            header_widget = CategoryHeaderWidget(category, is_collapsed, self)
            new_layout.addWidget(header_widget)
            self.section_headers[category] = header_widget

            grid_widget = CategoryGridWidget(category, self)
            self.category_grids[category] = grid_widget
            
            if is_collapsed:
                grid_widget.hide()

            add_card = AddCardWidget(category, self.on_edit_request, self)
            grid_widget.add_card = add_card

            for chord in chords_list:
                card = ChordCardWidget(chord, self.on_edit_request, self)
                grid_widget.original_cards.append(card)

            grid_widget.current_cards = list(grid_widget.original_cards)
            grid_widget.update_grid_layout()
            new_layout.addWidget(grid_widget)

            # Insert an option hook directly into drag-and-drop structural systems
            legend_item = LegendItemWidget(category, self)
            self.legend_container.original_items.append(legend_item)
        
        self.legend_container.current_items = list(self.legend_container.original_items)
        self.legend_container.update_layout()
        new_layout.addStretch(1)

        # Add Category execution button item
        btn_add_category = QPushButton("+ Create Category")
        btn_add_category.setObjectName("addCategoryButton")
        btn_add_category.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_add_category.setEnabled(not self.interaction_locked)
        btn_add_category.clicked.connect(self.prompt_new_category)
    
        self.dynamic_sidebar_layout.addWidget(btn_add_category)

        # Atomically swap active scroll widgets out
        old_contents = self.scrollArea.takeWidget()
        self.scrollArea.setWidget(new_contents)
        
        if old_contents:
            old_contents.deleteLater()

        new_contents.adjustSize()
        scroll_bar.setValue(saved_scroll_position)

        # Trigger inline editing mechanics immediately if processing a new section
        if hasattr(self, 'editing_category_name') and self.editing_category_name:
            h_widget = self.section_headers.get(self.editing_category_name)
            if h_widget:
                h_widget.start_editing()
            self.editing_category_name = None

    def _build_sidebar_footer(self) -> None:
        """Builds a minimalist persistent sidebar footer."""
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(6)
        footer_layout.setContentsMargins(0, 15, 0, 0)

        btn_exit = HoverIconButton('power', size=25, color='red', hover_color='light_red')
        btn_exit.setObjectName('btn_exit')
        btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exit.clicked.connect(QApplication.instance().quit)

        footer_layout.addWidget(btn_exit)
        self.sidebar_layout.addLayout(footer_layout)

    def scroll_to_section(self, category: str) -> None:
        """Focuses the main viewing scroll framework to center cleanly onto a designated section."""
        header_widget = self.section_headers.get(category)
        if header_widget:
            target_y = max(0, header_widget.pos().y() - 15)
            self.scrollArea.verticalScrollBar().setValue(target_y)