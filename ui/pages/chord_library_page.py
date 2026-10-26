# ui/pages/chord_library_page.py
import copy
from PyQt6.QtWidgets import QWidget, QSplitter, QVBoxLayout, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal

from ui.widgets.chord_library.library_grid import LibraryGrid
from ui.widgets.chord_editor.editor_panel import EditorPanel
from models.chord import Chord

class ChordLibraryPage(QWidget):
    """
    Main page component coordinating the layout and data workflow between 
    the chord library grid (left side) and the chord editor panel (right side).
    """
    # Notifies the main window shell to lock navigation during active editing
    edit_mode_changed = pyqtSignal(bool)

    def __init__(self, service):
        super().__init__()

        self.setObjectName('chordLibraryPage')

        self.service = service
        self.is_new_chord = False
        self.old_chord_name = None
        self._setup_ui()

    def _setup_ui(self):
        """
        Initializes the user interface using a responsive horizontal splitter layout.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Splitter allows user to manually adjust the boundary between grid and form
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("chordLibrarySplitter")
        layout.addWidget(self.splitter)

        # Left Column - Scrollable Grid Component
        self.library_grid = LibraryGrid(self.service, self.open_chord_editor)
        self.splitter.addWidget(self.library_grid)

        # Right Column - Form Editor Sidebar Component
        self.editor_panel = EditorPanel()
        self.splitter.addWidget(self.editor_panel)

        # Set split ratios (Grid takes up roughly 75%, Form takes up 25%)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        # Prevent columns from collapsing entirely into zero-width
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)

        # Wire up event signals from nested child panels
        self.editor_panel.save_requested.connect(self.save_current_chord)
        self.editor_panel.cancel_requested.connect(self.cancel_editing)
        self.editor_panel.delete_requested.connect(self._on_delete_requested)
        self.editor_panel.name_input.textChanged.connect(self._on_name_changed_live)

        # Start with a clean slate (editor is closed by default)
        self.editor_panel.hide()

    def _on_name_changed_live(self, text: str):
        """
        Synchronously binds text modifications back to the active model 
        to trigger canvas updates within the diagram widget.
        """
        if self.editor_panel.current_chord and self.editor_panel.diagram_editor.is_editing:
            self.editor_panel.current_chord.name = text
            self.editor_panel.diagram_editor.update()

    def open_chord_editor(self, chord_or_category):
        """
        Prepares target chord instances and slides open the form sidebar.
        Accepts either a Chord object to edit, or a category string/None to spin up a new item.
        """
        if isinstance(chord_or_category, str) or chord_or_category is None:
            # Context: User wants to add a brand new chord to a specific category
            category = chord_or_category if isinstance(chord_or_category, str) else 'Other'
            chord = Chord("Your chord", [0, 0, 0, 0, 0, 0], [], base_fret=1, category=category)
            self.old_chord_name = None
            self.is_new_chord = True
        else:
            # Context: User clicked on an existing chord card to update it
            chord = copy.deepcopy(chord_or_category)
            self.old_chord_name = chord_or_category.name
            self.is_new_chord = False

        # Load instance parameters inside fields and trigger edit modes
        self.editor_panel.set_chord(chord, self.is_new_chord)
        self.editor_panel.set_edit_mode(True)

        # Freeze mouse and selection inputs on the grid to protect current state integrity
        self.library_grid.set_interaction_locked(True)

        self.editor_panel.show()
        self._allocate_splitter_space()
        self.edit_mode_changed.emit(True)

    def _allocate_splitter_space(self):
        """
        Calculates and applies an aesthetic initial pixel layout configuration 
        for the panel when the sidebar workspace expands.
        """
        total_width = self.splitter.width()
        target_editor_w = max(350, int(total_width * 0.28))
        target_library_w = total_width - target_editor_w
        
        self.splitter.setSizes([target_library_w, target_editor_w])

    def save_current_chord(self):
        """
        Validates input field rules, screens out identical title collisions, 
        and flushes modified data properties into local database streams.
        """
        chord = self.editor_panel.current_chord
        if not chord:
            return

        name = self.editor_panel.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, 'Error', 'Chord name cannot be empty!')
            return

        # --- Unique Name Collision Guard Block ---
        try:
            all_chords = self.service.get_all_chords()
            for existing_chord in all_chords:
                if existing_chord.name.lower() == name.lower():
                    # Block save if we're creating a duplicate, or shifting an old chord's name to a taken one
                    if self.is_new_chord or (self.old_chord_name and existing_chord.name.lower() != self.old_chord_name.lower()):
                        QMessageBox.warning(
                            self, 
                            "Duplicate Chord Name", 
                            f"A chord named '{name}' already exists in your library!\n"
                            "Please choose a unique name to avoid conflicts."
                        )
                        return 
        except Exception as e:
            print(f"Error during duplicate validation checks: {e}")

        # Update properties on the underlying model object
        chord.name = name
        chord.base_fret = self.editor_panel.fret_spin.value()

        # Direct database traffic depending on edit state context
        if self.is_new_chord:
            self.service.add_chord(chord)
        else:
            self.service.update_chord(self.old_chord_name, chord)

        # Finalize and push adjustments out to persistence layer
        self._close_editor_context()
        self.service.save_data_to_database()
        self.library_grid.refresh_library()
    
    def cancel_editing(self):
        """
        Safely drops unsaved mutations and slides the editor closed without changing states.
        """
        self._close_editor_context()
        self.library_grid.refresh_library()

    def _on_delete_requested(self):
        """
        Prompts confirmation alerts before truncating targeting rows inside database structures.
        """
        chord = self.editor_panel.current_chord
        if not chord or self.is_new_chord:
            return

        msg_box = QMessageBox(self)
        msg_box.setObjectName("deleteConfirmDialog")
        msg_box.setWindowTitle("Confirm Delete")
        msg_box.setText(f"Are you sure you want to delete the chord '{chord.name}'?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            name_to_delete = self.old_chord_name if self.old_chord_name else chord.name
            self.service.delete_chord(name_to_delete)
            self.service.save_data_to_database()
            self._close_editor_context()
            self.library_grid.refresh_library()

    def _close_editor_context(self):
        """
        Internal utility that resets interaction rules and locks sidebar visuals out of active views.
        """
        self.is_new_chord = False
        self.old_chord_name = None
        self.editor_panel.set_edit_mode(False)
        self.library_grid.set_interaction_locked(False)
        self.editor_panel.hide()
        self.edit_mode_changed.emit(False)