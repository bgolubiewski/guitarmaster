 # ui/widgets/chord_library/legend_widget.py
from typing import Any, Optional
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QFrame, QVBoxLayout
from PyQt6.QtCore import Qt, QMimeData, QPoint, QEvent, QSize
from PyQt6.QtGui import QDrag, QMouseEvent, QDragEnterEvent, QDragMoveEvent, QDragLeaveEvent, QDropEvent, QEnterEvent

from assets.svg_icons.svg_icons import get_svg_icon

class LegendDragHandle(QPushButton):
    """
    A custom drag handle for legend items preventing accidental triggers
    using Manhattan distance threshold checks.
    """
    def __init__(self, parent_item: 'LegendItemWidget') -> None:
        super().__init__('', parent_item)
        self.item_widget: 'LegendItemWidget' = parent_item
        self.drag_start_pos: QPoint = QPoint()

        self.setObjectName('LegendDragHandle')
        self.icon_normal = get_svg_icon('drag_handle', size=16, color="icon_default")
        self.icon_hover = get_svg_icon('drag_handle', size=16, color="icon_hover")

        self.setIcon(self.icon_normal)
        self.setIconSize(QSize(16, 16))
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def enterEvent(self, event: QEnterEvent) -> None:
        self.setIcon(self.icon_hover)
        self.update()  # wymusza natychmiastowe przerysowanie przycisku
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
            # Trigger drag session only if the mouse moves beyond the 5px tolerance threshold
            if (event.position().toPoint() - self.drag_start_pos).manhattanLength() > 5:
                self.item_widget.start_drag(event.position().toPoint())

class LegendItemWidget(QWidget):
    def __init__(self, category_name: str, library_view: Any) -> None:
        super().__init__()
        self.category_name: str = category_name
        self.library_view: Any = library_view

        self.setObjectName("LegendItemWidget")
        self.setMouseTracking(True)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 4, 6, 4)
        self.layout.setSpacing(4)

        # Category jump hyperlink node
        self.btn_link = QPushButton(category_name)
        self.btn_link.setObjectName("LegendCategoryButton")
        self.btn_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_link.clicked.connect(lambda: self.library_view.scroll_to_section(category_name))

        self.layout.addWidget(self.btn_link, stretch=1)

        # Custom explicit drag handle button instance
        self.drag_handle = LegendDragHandle(self)
        self.drag_handle.hide()
        self.layout.addWidget(self.drag_handle)

    def start_drag(self, hotspot_offset: QPoint) -> None:
        """Encapsulates and executes native Drag session initialization."""
        if self.library_view.interaction_locked:
            return
           
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData("application/x-legend-item", b"true")
        drag.setMimeData(mime_data)

        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(hotspot_offset + self.drag_handle.pos())

        self.library_view.active_dragged_legend = self

        # Signal target layout container to apply active system visual feedback states
        self.library_view.legend_container.set_style_state("drag_active")
       
        drag.exec(Qt.DropAction.MoveAction)

        self.library_view.active_dragged_legend = None
        self.library_view.legend_container.set_style_state("normal")
        self.library_view.refresh_library()

    def enterEvent(self, event: QEnterEvent) -> None:
        if not self.library_view.interaction_locked:
            self.drag_handle.show()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.drag_handle.hide()
        super().leaveEvent(event)

class LegendContainerWidget(QFrame):
    def __init__(self, library_view: Any) -> None:
        super().__init__()
        self.library_view: Any = library_view
        self.setAcceptDrops(True)
        self.setObjectName("LegendContainer")
        self.set_style_state('normal')

        self.v_layout = QVBoxLayout(self)
        self.v_layout.setContentsMargins(0, 4, 0, 4)
        self.v_layout.setSpacing(2)
        self.v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.original_items: list[LegendItemWidget] = []
        self.current_items: list[LegendItemWidget] = []
        self.last_target_index: Optional[int] = None

    def set_style_state(self, state: str) -> None:
        """Applies stylesheet visuals depending on drag operational states."""
        self.setProperty("dragState", state)
        self.style().unpolish(self)
        self.style().polish(self)

    def update_layout(self) -> None:
        """Redraws the layout tree sorting node hierarchies using current tracking state values."""
        while self.v_layout.count():
            item = self.v_layout.takeAt(0)
            if item is None:
                continue     

        for item_widget in self.current_items:
            self.v_layout.addWidget(item_widget)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat("application/x-legend-item") and not self.library_view.interaction_locked:
            event.acceptProposedAction()
            self.set_style_state("drag_hover")
            self.current_items = list(self.original_items)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if self.library_view.interaction_locked:
            return

        event.acceptProposedAction()
        dragged_item = self.library_view.active_dragged_legend
        if not dragged_item:
            return

        pos = event.position()
        y = pos.y()

        # Real-time fluid mid-point calculations tracking vertical insertions safely
        target_index = 0
        cumulative_height = 0.0

        for idx, item in enumerate(self.original_items):
            item_h = float(item.height() + 4)
            if y > cumulative_height + (item_h / 2.0):
                target_index = idx + 1
            cumulative_height += item_h

        if target_index > len(self.original_items):
            target_index = len(self.original_items)

        if self.last_target_index != target_index:
            self.last_target_index = target_index
            temp_list = [item for item in self.original_items if item != dragged_item]
            temp_list.insert(target_index, dragged_item)
            self.current_items = temp_list
            self.update_layout()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.set_style_state("drag_active")
        self.current_items = list(self.original_items)
        self.last_target_index = None
        self.update_layout()

    def dropEvent(self, event: QDropEvent) -> None:
        if self.library_view.interaction_locked:
            return
        dragged_item = self.library_view.active_dragged_legend
        if not dragged_item:
            return

        new_order = [item.category_name for item in self.current_items]
        self.library_view.finalize_category_reorder(new_order)
        event.acceptProposedAction() 