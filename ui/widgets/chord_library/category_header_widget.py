# ui/widgets/chord_library/category_header_widget.py
from typing import Any
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, QEvent, QSize
from PyQt6.QtGui import QMouseEvent, QEnterEvent, QIcon

from assets.svg_icons.svg_hover_widgets import HoverIconButton, HoverLabel
from assets.svg_icons.svg_icons import get_svg_pixmap

class HeaderHoverContainer(QWidget):
    """Helper mini-widget bounding the hover detection zone tightly around the category title area."""
    def __init__(self, parent_header: 'CategoryHeaderWidget') -> None:
        super().__init__(parent_header)
        self.parent_header: 'CategoryHeaderWidget' = parent_header
        self.setMouseTracking(True)

    def enterEvent(self, event: QEnterEvent) -> None:
        if not self.parent_header.library_view.interaction_locked:
            self.parent_header.btn_edit.show()
            self.parent_header.btn_delete.show()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        if not self.parent_header.is_editing:
            self.parent_header.btn_edit.hide()
            self.parent_header.btn_delete.hide()
        super().leaveEvent(event)

class CategoryHeaderWidget(QWidget):
    def __init__(self, category_name: str, is_collapsed: bool, library_view: Any) -> None:
        super().__init__()
        self.category_name: str = category_name
        self.is_collapsed: bool = is_collapsed
        self.library_view: Any = library_view
        self.is_editing: bool = False

        self.is_arrow_hovered: bool = False
        self.setObjectName("CategoryHeaderWidget")
        
        # Main layout covering full parent viewport availability width
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 15, 0, 5)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Build tightly bound hover node container
        self.hover_container = HeaderHoverContainer(self)
        self.hc_layout = QHBoxLayout(self.hover_container)
        self.hc_layout.setContentsMargins(0, 0, 0, 0)
        self.hc_layout.setSpacing(10)
        self.hc_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Collapse/Expand toggle state indicator arrow
        self.arrow_label = HoverLabel(on_hover_callback=self._on_arrow_hover)
        self.arrow_label.setObjectName("CategoryHeaderArrow")
        self.arrow_label.setFixedSize(24, 24)
        self.arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.arrow_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hc_layout.addWidget(self.arrow_label)

        self.update_arrow_icon()

        # Category display node literal
        self.name_label = QLabel(self.category_name)
        self.name_label.setObjectName("CategoryHeaderTitle")
        self.name_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hc_layout.addWidget(self.name_label)

        # Inline editing line component (hidden by default instantiation state)
        self.name_edit = QLineEdit(self.category_name)
        self.name_edit.setObjectName("CategoryHeaderEdit")
        self.name_edit.hide()
        self.hc_layout.addWidget(self.name_edit)

        # Edit/Save button
        self.btn_edit = HoverIconButton('edit', size=16, color='icon_active', hover_color='icon_hover')
        self.btn_edit.setObjectName("CategoryHeaderEditButton")
        self.btn_edit.setFixedSize(26, 26)
        self.btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_edit.hide()

        # Delete button
        self.btn_delete = HoverIconButton('trash', size=16,
                                           color="icon_danger", hover_color="icon_danger_hover")
        self.btn_delete.setObjectName("CategoryHeaderDeleteButton")
        self.btn_delete.setFixedSize(26, 26)
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.hide()

        self.button_container = QWidget()
        self.button_container.setFixedHeight(26)
        self.button_container.setFixedWidth(58)

        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(6)
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.button_layout.addWidget(self.btn_edit)
        self.button_layout.addWidget(self.btn_delete)

        self.hc_layout.addWidget(self.button_container)

        # Append structured elements safely before spacer blocks take up the end layout
        self.main_layout.addWidget(self.hover_container)
        self.main_layout.addStretch()

        # Wire event triggers using explicit tracking layers
        self.arrow_label.mousePressEvent = self._on_header_clicked
        self.name_label.mousePressEvent = self._on_header_clicked

        self.btn_edit.clicked.connect(self._toggle_edit_mode)
        self.btn_delete.clicked.connect(self._delete_category)
        self.name_edit.returnPressed.connect(self._save_edit)

    def _on_arrow_hover(self, is_hover: bool) -> None:
        self.is_arrow_hovered = is_hover
        self.update_arrow_icon()

    def update_arrow_icon(self, is_hover: bool = False) -> None:
        """Renders SVG arrow, rotates it and changes color on hover."""
        rotation = 90 if not self.is_collapsed else 0
        color = 'icon_hover' if self.is_arrow_hovered else 'icon_active'
        pixmap = get_svg_pixmap('chevron_right', size=16, color=color, rotation=rotation)
        self.arrow_label.setPixmap(pixmap)
        
    def _on_header_clicked(self, event: QMouseEvent) -> None:
        if not self.is_editing and event.button() == Qt.MouseButton.LeftButton:
            self.library_view.toggle_category_by_header(self.category_name, self)

    def _toggle_edit_mode(self) -> None:
        if self.is_editing:
            self._save_edit()
        else:
            self.start_editing()

    def start_editing(self) -> None:
        """Switches the header view to a text editor control with input focus flags."""
        self.is_editing = True
        self.name_label.hide()
        self.name_edit.setText(self.category_name)
        self.name_edit.show()
        self.name_edit.setFocus()
        self.name_edit.selectAll()
        self.btn_edit.set_icon_config('save', color='icon_active', hover_color='icon_hover')
        self.btn_edit.show()
        self.btn_delete.show()

    def _save_edit(self) -> None:
        new_name = self.name_edit.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Error", "Category name cannot be empty!")
            self.name_edit.setFocus()
            return

        existing_categories = [cat for cat in self.library_view.categories_order if cat != self.category_name]
        
        if new_name in existing_categories:
            base_name = new_name
            suggested_name = base_name
            counter = 2
            while suggested_name in self.library_view.categories_order:
                suggested_name = f"{base_name} ({counter})"
                counter += 1
            
            QMessageBox.warning(
                self, "Duplicate Name", 
                f"Category '{new_name}' already exists!\nWe suggest using: '{suggested_name}'"
            )
            self.name_edit.setText(suggested_name)
            self.name_edit.setFocus()
            return

        if new_name != self.category_name:
            self.library_view.rename_category(self.category_name, new_name)
        
        self.is_editing = False
        self.btn_edit.set_icon_config('edit', color='icon_active', hover_color='icon_hover')
        self.name_edit.hide()
        self.name_label.setText(new_name)
        self.name_label.show()
        self.category_name = new_name
        self.btn_edit.hide()
        self.btn_delete.hide()

    def _delete_category(self) -> None:
        grouped_chords = self.library_view.service.get_chords_grouped_by_category()
        chords_in_category = grouped_chords.get(self.category_name, [])

        if chords_in_category:
            confirm = QMessageBox.question(
                self, "Delete Category",
                f"Are you sure you want to delete the category '{self.category_name}'?\n"
                f"This will permanently delete all chords inside this category!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            
        self.library_view.delete_category(self.category_name)