# ui/widgets/chord_editor/editor_panel.py
from typing import Optional, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QSpinBox, QPushButton, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QResizeEvent

from ui.widgets.chord_editor.chord_diagram_widget import ChordDiagramWidget
from models.chord import Chord

class EditorPanel(QWidget):
    """
    Sidebar panel responsible exclusively for the chord editing form UI, 
    input validation parameters, and diagram context bindings.
    """
    save_requested = pyqtSignal()
    cancel_requested = pyqtSignal()
    delete_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.current_chord: Optional[Chord] = None
        
        self.setObjectName("EditorPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Builds layout design and input elements for the sidebar form.
        """
        self.main_layout = QVBoxLayout(self)
        self.setMinimumWidth(320)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(10)

        self.title = QLabel('Chord Editor')
        self.title.setObjectName("EditorTitle")
        self.main_layout.addWidget(self.title)

        self.lbl_name = QLabel('Chord Name')
        self.lbl_name.setObjectName("FieldLabel")
        self.main_layout.addWidget(self.lbl_name)

        self.name_input = QLineEdit()
        self.name_input.setObjectName("EditorInput")
        self.name_input.setPlaceholderText("e.g. Cmaj7")
        self.main_layout.addWidget(self.name_input)

        self.lbl_fret = QLabel('Base fret position:')
        self.lbl_fret.setObjectName("FieldLabel")
        self.main_layout.addWidget(self.lbl_fret)

        self.fret_spin = QSpinBox()
        self.fret_spin.setObjectName("EditorSpinBox")
        self.fret_spin.setRange(1, 20)
        self.fret_spin.valueChanged.connect(self.diagram_editor_change_handler)
        self.main_layout.addWidget(self.fret_spin)

        self.lbl_diagram = QLabel('Fretting Matrix')
        self.lbl_diagram.setObjectName("FieldLabel")
        self.main_layout.addWidget(self.lbl_diagram)

        self.diagram_card = QFrame()
        self.diagram_card.setObjectName("DiagramContainer")
        card_layout = QVBoxLayout(self.diagram_card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.diagram_editor = ChordDiagramWidget(is_editing=True)
        card_layout.addWidget(self.diagram_editor)

        self.main_layout.addWidget(self.diagram_card, stretch=1)

        self._build_action_buttons(self.main_layout)

    def _build_action_buttons(self, parent_layout: QVBoxLayout) -> None:
        """
        Creates standard editor controls at the bottom of the layout.
        """
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(10)
        self.actions_layout.setContentsMargins(0, 12, 0, 0)

        # Danger action separated on the left side
        self.btn_delete = QPushButton('Delete')
        self.btn_delete.setObjectName("DangerButton")
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.clicked.connect(self.delete_requested.emit)

        # Secondary action
        self.btn_cancel = QPushButton('Cancel')
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.cancel_requested.emit)

        # Primary action
        self.btn_save = QPushButton('Save')
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_requested.emit)

        self.actions_layout.addWidget(self.btn_delete)
        self.actions_layout.addStretch(1)
        self.actions_layout.addWidget(self.btn_cancel)
        self.actions_layout.addWidget(self.btn_save)

        parent_layout.addLayout(self.actions_layout)

    def diagram_editor_change_handler(self, value: int) -> None:
        """Safely proxies spinbox values to the diagram visualizer layout."""
        if hasattr(self, 'diagram_editor') and self.diagram_editor:
            self.diagram_editor.on_base_fret_change(value)

    def set_chord(self, chord: Chord, is_new: bool) -> None:
        """
        Maps data properties from a Chord instance directly into the inputs configuration.
        """
        self.current_chord = chord
        self.name_input.setText(chord.name)

        self.fret_spin.blockSignals(True)
        self.fret_spin.setValue(chord.base_fret)
        self.fret_spin.blockSignals(False)

        self.diagram_editor.set_chord(chord)

        # Force a style refresh context dynamically based on the chord state
        if is_new:
            self.title.setText("New chord")
            self.btn_delete.hide()
        else:
            self.title.setText(f"Edit {chord.name}")
            self.btn_delete.show()

    def set_edit_mode(self, is_editing: bool) -> None:
        """Freezes or unblocks input fields based on application workflows."""
        self.name_input.setReadOnly(not is_editing)
        self.fret_spin.setEnabled(is_editing)
        self.diagram_editor.is_editing = is_editing
        if is_editing:
            self.name_input.setFocus()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Calculates geometric diagram proportions to fill available card space
        while maintaining aspect ratio (1:1.25) and restricting panel width.
        """
        super().resizeEvent(event)

        # restrict width to 30% of window width
        if self.window():
            window_width = self.window().width()
            max_allowed_width = int(window_width * 0.30)
            
            effective_max_width = max(self.minimumWidth(), max_allowed_width)
            self.setMaximumWidth(effective_max_width)

        # calculate diagram proportions
        card_margins = self.diagram_card.contentsMargins()
        avail_w = max(80, self.diagram_card.width() - card_margins.left() - card_margins.right())
        avail_h = max(100, self.diagram_card.height() - card_margins.top() - card_margins.bottom())

        aspect_ratio = 1.25 

        if avail_w * aspect_ratio <= avail_h:
            target_w = avail_w
            target_h = int(avail_w * aspect_ratio)
        else:
            target_h = avail_h
            target_w = int(avail_h / aspect_ratio)

        self.diagram_editor.setFixedSize(target_w, target_h)