# ui/widgets/chord_editor/chord_diagram_widget.py
from typing import Optional, Any
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QResizeEvent, QMouseEvent
from PyQt6.QtCore import Qt

from models.chord import Chord

DIAGRAM_COLORS = {
    "text_title": "#2B303A",       # Grafitowy tytuł akordu
    "text_secondary": "#5C6573",   # Grafitowy podtytuł
    "string": "#4A5260",           # Wyraziste, ciemnografitowe struny
    "fret": "#C8C0B2",             # Delikatne progi w tle
    "fret_nut": "#2B303A",         # Ciemny grafit dla siodełka
    "note_accent": "#1A202C",      # Bardzo ciemny, matowy grafit dla kropek i poprzeczek
    "string_muted": "#717D8A",
    "string_open": "#2B303A",
}

class ChordDiagramWidget(QWidget):
    """
    A custom PyQt6 widget that renders an interactive guitar chord diagram.
    Supports both large interactive editing mode and compact library preview mode.
    """

    def __init__(
        self, 
        chord: Optional[Chord] = None, 
        parent: Optional[QWidget] = None, 
        is_editing: bool = False
    ) -> None:
        """
        Initializes the chord diagram widget.
        
        :param chord: The Chord data object to display. Defaults to an empty chord if None.
        :param parent: The parent QWidget, if any.
        :param is_editing: If True, enables mouse interactions to modify the chord.
        """
        super().__init__(parent)

        self.fret_count: int = 5
        self.string_count: int = 6

        # Define initial margins
        self.left_margin: int = 40
        self.right_margin: int = 60
        self.top_margin: int = 60
        self.bottom_margin: int = 20

        # Variables tracking user drag state for creating barre chords
        self.drag_start_string: Optional[int] = None
        self.drag_start_fret: Optional[int] = None
        self.current_drag_string: Optional[int] = None

        # Dynamic geometric properties calculated during resize events
        self.w: int = self.width()
        self.h: int = self.height()
        self.fret_spacing: float = 0.0
        self.string_spacing: float = 0.0
        self.radius: int = 0

        # Dynamic font size
        self.name_font_size: int = 12
        self.marker_font_size: int = 20     # X/O symbols
        self.fret_font_size: int = 0        # fret number

        # Initialize chord data with a fallback default empty chord
        self.chord: Chord = chord or Chord("", [0, 0, 0, 0, 0, 0], [], base_fret=1)
        self.setMinimumSize(100, 125)

        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

        self._is_editing: bool = is_editing
        

    @property
    def is_editing(self) -> bool:
        """Returns whether the widget is in interactive editing mode."""
        return self._is_editing

    @is_editing.setter
    def is_editing(self, value: bool) -> None:
        self._is_editing = value
        self.calculate_geometry()
        self.update()

    def set_chord(self, chord: Chord) -> None:
        """
        Updates the widget with a new chord object and triggers a repaint.
        
        :param chord: The new Chord object to display.
        """
        self.chord = chord
        self.calculate_geometry()
        self.update()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        PyQt override triggered automatically when the widget size changes.
        Recalculates rendering layout boundaries.
        """
        super().resizeEvent(event)
        self.calculate_geometry()

    def calculate_geometry(self) -> None:
        """
        Calculates dynamic measurements, margins, spacing, and sizing based on the current 
        widget dimensions to ensure the diagram scales nicely.
        """
        self.w = self.width()
        self.h = self.height()

        # if self._is_editing:
        #     self.top_margin = max(45, int(self.h * 0.22))
        #     self.bottom_margin = max(15, int(self.h * 0.08))
        #     self.left_margin = max(30, int(self.w * 0.15))
        #     self.right_margin = max(38, int(self.w * 0.20))
        # else:
        #     self.top_margin = max(24, int(self.h * 0.18))
        #     self.bottom_margin = max(10, int(self.h * 0.06))
        #     self.left_margin = max(18, int(self.w * 0.13))
        #     self.right_margin = max(30, int(self.w * 0.18))

        self.top_margin = max(18, int(self.h * 0.14))
        self.bottom_margin = max(8, int(self.h * 0.05))

        side_margin = max(20, int(self.w * 0.14))
        self.left_margin = side_margin
        self.right_margin = side_margin

        # Calculate working space
        usable_h = max(1, self.h - self.top_margin - self.bottom_margin)
        usable_w = max(1, self.w - self.right_margin - self.left_margin)

        self.fret_spacing = usable_h / self.fret_count
        # Spacing between strings; 6 strings -> 5 spaces
        self.string_spacing = usable_w / (self.string_count - 1)

        # Note size (radius of note = 1/4 of distance between frets)
        self.radius = max(int(self.fret_spacing * 0.25), 4)

        # Text scaling
        self.name_font_size = max(9, min(18, int(self.top_margin * 0.40)))
        self.fret_font_size = max(12, min(16, int(self.top_margin * 0.40)))
        self.marker_font_size = max(10, min(16, int(self.top_margin * 0.40)))


    def paintEvent(self, event: Any) -> None:
        """
        PyQt override responsible for rendering the visual elements of the widget.
        Draws the grid, labels, notes, and interactive previews sequentially.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Render static layout layers
        if self._is_editing:
            self.draw_chord_name(painter)
        
        self.draw_strings(painter)
        self.draw_frets(painter)
        self.draw_base_fret_number(painter)

        # Render live interactions layer (barre creation preview)
        if (self._is_editing and 
                self.drag_start_string is not None and 
                self.drag_start_fret is not None and 
                self.current_drag_string is not None):
            if self.drag_start_string != self.current_drag_string and self.drag_start_fret > 0:
                self.draw_barre_preview(
                    painter, 
                    self.drag_start_string, 
                    self.current_drag_string, 
                    self.drag_start_fret
                )

        # Render current chord states layer
        self.draw_barres(painter)
        self.draw_notes(painter)
        painter.end()

    # -------------------------------------------------------------------------
    # Helper Logic Methods
    # -------------------------------------------------------------------------

    def get_string_x(self, string_index: int) -> int:
        """
        Calculates the absolute X coordinate on the widget for a given string index.
        
        :param string_index: Index of the string (0 to 5).
        :return: X coordinate as an integer.
        """
        return int(self.left_margin + string_index * self.string_spacing)
    
    def get_fret_y(self, fret: int) -> int:
        """
        Calculates the absolute Y coordinate on the widget representing the center 
        of a given fret space. Takes base fret offsets into account.
        
        :param fret: Real fret number from the chord data.
        :return: Y coordinate as an integer centered inside the fret space.
        """
        visible_fret = (fret - self.chord.base_fret + 1)
        return int(self.top_margin + (visible_fret - 0.5) * self.fret_spacing)

    # -------------------------------------------------------------------------
    # Rendering / View Methods
    # -------------------------------------------------------------------------

    def draw_chord_name(self, painter: QPainter) -> None:
        """Draws the name of the chord centered at the top of the widget."""
        font = QFont()
        font.setPixelSize(self.name_font_size)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(DIAGRAM_COLORS["text_title"]))

        height_box = int(self.top_margin * 0.4)
        painter.drawText(0, int(self.top_margin * 0.1), 
                         self.w, height_box,
                         Qt.AlignmentFlag.AlignCenter, self.chord.name)

    def draw_strings(self, painter: QPainter) -> None:
        """Draws the vertical lines representing guitar strings."""
        pen = QPen(QColor(DIAGRAM_COLORS["string"]), 2)
        painter.setPen(pen)

        for i in range(self.string_count):
            x = self.get_string_x(i)
            painter.drawLine(x, self.top_margin, x, int(self.h - self.bottom_margin))

    def draw_frets(self, painter: QPainter) -> None:
        """
        Draws the horizontal lines representing frets. Makes the first line 
        (the nut) thicker if the diagram starts at fret 1.
        """
        for i in range(self.fret_count + 1):
            y = int(self.top_margin + self.fret_spacing * i)

            # Bolder guitar nut for open chords
            if i == 0 and self.chord.base_fret == 1:
                pen_width = 5 if self._is_editing else 4
                pen_color = QColor(DIAGRAM_COLORS["fret_nut"])
            else:
                pen_width = 2
                pen_color = QColor(DIAGRAM_COLORS["fret"])

            pen = QPen(pen_color, pen_width)
            painter.setPen(pen)
            painter.drawLine(self.left_margin, y, int(self.w - self.right_margin), y)

    def draw_base_fret_number(self, painter: QPainter) -> None:
        """Displays the starting fret number label next to the top fret."""
        if self.chord.base_fret <= 1:
            return

        font = QFont()
        font.setPixelSize(self.fret_font_size)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(DIAGRAM_COLORS["text_secondary"]))

        last_string_x = self.w - self.right_margin
        gap = max(4, int(self.radius * 0.5))
        x_pos = int(last_string_x + self.radius + gap)

        width_box = max(15, int(self.w - x_pos))
        height_box = int(self.fret_spacing)

        painter.drawText(x_pos, self.top_margin,
                         width_box, height_box,
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         f"{self.chord.base_fret}")

    def draw_barres(self, painter: QPainter) -> None:
        """Draws rounded solid rectangles representing active barre shapes."""
        painter.setBrush(QColor(DIAGRAM_COLORS["note_accent"]))
        painter.setPen(Qt.PenStyle.NoPen)

        for barre in self.chord.barres:
            fret, start_string, end_string = barre

            y = self.get_fret_y(fret)
            x1 = self.get_string_x(start_string)
            x2 = self.get_string_x(end_string)

            barre_height = int(self.radius * 1.5)
            painter.drawRoundedRect(
                x1, int(y - barre_height / 2), x2 - x1,
                barre_height, barre_height / 2, barre_height / 2
            )

    def draw_notes(self, painter: QPainter) -> None:
        """Draws standard fretted note circles, muted and open string markings (X/O)."""
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(DIAGRAM_COLORS["note_accent"]))

        marker_font = QFont()
        marker_font.setPixelSize(self.marker_font_size)
        marker_font.setBold(True)

        # Draw circles/caps at the outer edges of active barres
        for fret, start_str, end_str in self.chord.barres:
            y_barre = self.get_fret_y(fret)

            for string_idx in (start_str, end_str):
                x_edge = self.get_string_x(string_idx)
                painter.drawEllipse(
                    int(x_edge - self.radius), int(y_barre - self.radius),
                    self.radius * 2, self.radius * 2
                )

        # Draw individual note markers and open/muted string signs
        for i, fret in enumerate(self.chord.frets):
            x = self.get_string_x(i)

            # Muted/open strings, draw X/O
            if fret in (-1,0):
                painter.setFont(marker_font)
                text_color = DIAGRAM_COLORS["string_muted"] if fret == -1 else DIAGRAM_COLORS["string_open"]
                painter.setPen(QColor(text_color))
                label = 'X' if fret == -1 else 'O'

                box_w = max(10, int(self.string_spacing))
                box_h = int(self.top_margin * 0.55)
                box_x = int(x - box_w / 2)
                box_y = int(self.top_margin - box_h - 4)

                painter.drawText(box_x, box_y, box_w, box_h,
                                 Qt.AlignmentFlag.AlignCenter, label)
            
            # Fretted notes
            elif fret > 0:
                # Skip drawing a single note circle if it is already covered by a barre
                is_covered_by_any_barre = any(
                    barre_fret == fret and start_str <= i <= end_str
                    for barre_fret, start_str, end_str in self.chord.barres
                )       
                if is_covered_by_any_barre:
                    continue
                # Draw a note
                y = self.get_fret_y(fret)
                painter.drawEllipse(
                    int(x - self.radius), int(y - self.radius),
                    self.radius * 2, self.radius * 2
                )
        
    def draw_barre_preview(self, painter: QPainter, start_str: int, end_str: int, fret: int) -> None:
        """Draws a translucent blue guide line following the cursor when dragging to create a barre."""
        x1 = self.get_string_x(start_str)
        x2 = self.get_string_x(end_str)
        absolute_fret = fret + self.chord.base_fret - 1
        y = self.get_fret_y(absolute_fret)

        preview_color = QColor(DIAGRAM_COLORS["note_accent"])
        preview_color.setAlpha(120)

        pen = QPen(preview_color, self.radius * 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(int(x1), int(y), int(x2), int(y))

    # -------------------------------------------------------------------------
    # Mouse Event Handling
    # -------------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Captures initial string and fret position on left clicks to prepare for dragging."""
        if not self._is_editing:
            return
        
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            snap_margin = int(self.string_spacing / 2) + 1

            self.drag_start_string = self._get_string_at_x(pos.x(), max_distance=snap_margin)
            self.drag_start_fret = self._get_fret_at_y(pos.y())
            self.current_drag_string = self.drag_start_string
            self.update()
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Tracks active cursor coordinates while dragging to update real-time barre preview."""
        if not self._is_editing or self.drag_start_string is None:
            return
        
        new_string = self._get_string_at_x(event.position().x(), max_distance=120)
        if new_string is not None and new_string != self.current_drag_string:
            self.current_drag_string = new_string
            self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Routes actions to specific click handlers and resets interaction states."""
        if not self._is_editing:
            return
        
        pos = event.position()
        string = self._get_string_at_x(pos.x(), max_distance=120)
        fret = self._get_fret_at_y(pos.y())
        
        if event.button() == Qt.MouseButton.RightButton:
            # Right-click requires precise string targeting to switch mute status
            precise_string = self._get_string_at_x(pos.x(), max_distance=30)
            if precise_string is not None:
                self._handle_right_click(precise_string)

        elif event.button() == Qt.MouseButton.LeftButton:
            self._handle_left_click_release(pos.x(), string, fret)

        # Clear active dragging states upon touch release
        self._reset_drag_states()    

    # -------------------------------------------------------------------------
    # Interaction Helpers
    # -------------------------------------------------------------------------

    def _handle_left_click_release(self, pos_x: float, string: Optional[int], fret: Optional[int]) -> None:
        """Main decision pipeline processing adjustments triggered by a left click release."""
        if string is None or fret is None:
            return
        
        # Validate horizontal drag across strings (barre creation)
        is_drag_gesture = (self.drag_start_fret is not None and
                           self.drag_start_string is not None and
                           self.drag_start_string != string and
                           self.drag_start_fret == fret)
        
        if is_drag_gesture:
            self._create_or_extend_barre(self.drag_start_string, string, fret)
            return
        
        # Static click. Remove barre if hit
        if self._try_remove_barre_by_hit(pos_x, fret):
            return
        
        # Static click. Toggle single note or open string
        self._toggle_note_or_open(string, fret)

    def _handle_right_click(self, string: int) -> None:
        """Mutes the string target (X) or restores to open (O), ignoring active barres."""
        is_under_barre = any(barre[1] <= string <= barre[2] for barre in self.chord.barres)
        if is_under_barre:
            return 
        
        self.chord.frets[string] = -1 if self.chord.frets[string] != -1 else 0
        self.update()

    def _toggle_note_or_open(self, string: int, fret: int) -> None:
        """Handles toggling operations between single fret notes and open string states."""
        target_fret = fret + self.chord.base_fret - 1

        # Clicking above the nut sets string to open
        if fret == 0:
            if any(barre[1] <= string <= barre[2] for barre in self.chord.barres):
                return
            self.chord.frets[string] = 0
            self.update()
            return
        
        # Toggle standalone note
        if self.chord.frets[string] == target_fret:
            # Turning off an active note restores background barre values or resets to 0
            covering_barre = next((barre for barre in self.chord.barres if barre[0] != target_fret and
                                   barre[1] <= string <= barre[2]), None)
            if covering_barre:
                self.chord.frets[string] = covering_barre[0]
            else: 
                self.chord.frets[string] = 0
        else:
            self.chord.frets[string] = target_fret
        
        self.update()

    def _try_remove_barre_by_hit(self, mouse_x: float, fret: int) -> bool:
        """Checks if a static left-click directly collides with an existing barre element to delete it."""
        target_fret = fret + self.chord.base_fret - 1

        for barre in self.chord.barres:
            barre_fret, start_str, end_str = barre

            if barre_fret == target_fret:
                x_start = self.get_string_x(start_str)
                x_end = self.get_string_x(end_str)

                # Check bounding dimensions including the rounded radius padding
                if x_start - self.radius <= mouse_x <= x_end + self.radius:
                    self.chord.barres.remove(barre)
                    self._clear_frets_for_removed_barre(start_str, end_str, target_fret)
                    self.update()
                    return True
        return False

    def _create_or_extend_barre(self, start_str: int, end_str: int, fret: int) -> None:
        """Creates or extends a barre chord segment, merging overlapping segments."""
        target_fret = fret + self.chord.base_fret - 1
        min_str = min(start_str, end_str)
        max_str = max(start_str, end_str)
        
        # Divide all barres into those on current fret and others
        other_frets_barres = [barre for barre in self.chord.barres if barre[0] != target_fret]
        current_barres = [barre for barre in self.chord.barres if barre[0] == target_fret]

        # Calculate needed merges
        independent_barres, new_min, new_max = self._merge_barre_segments(
            current_barres, min_str, max_str
        )
        self.chord.barres = other_frets_barres + independent_barres + [(target_fret, new_min, new_max)]

        # Automatically reassign underlying note values to match the barre row
        for string_index in range(min_str, max_str + 1):
            if self.chord.frets[string_index] <= target_fret:
                self.chord.frets[string_index] = target_fret
        self.update()

    def _merge_barre_segments(
        self, 
        current_fret_barres: list[tuple[int, int, int]], 
        new_min: int, 
        new_max: int
    ) -> tuple[list[tuple[int, int, int]], int, int]:
        """Executes an interval merge calculation for intersecting barres sharing a fret."""
        overlapping_barres = []
        independent_barres = []

        for barre in current_fret_barres:
            _, barre_start, barre_end = barre
            if not (new_max < barre_start or new_min > barre_end):
                overlapping_barres.append(barre)
            else:
                independent_barres.append(barre)

        if overlapping_barres:
            for barre in overlapping_barres:
                new_min = min(new_min, barre[1])
                new_max = max(new_max, barre[2])

        return independent_barres, new_min, new_max 
    
    def _clear_frets_for_removed_barre(self, start_str: int, end_str: int, removed_fret: int) -> None:
        """Cleans up the frets after a barre is removed, reverting to lower barres if nested."""
        for s in range(start_str, end_str + 1):
            if self.chord.frets[s] == removed_fret:
                other_barres = [b for b in self.chord.barres if b[1] <= s <= b[2]]

                if other_barres:
                    other_barres.sort(key=lambda b: b[0], reverse=True)
                    highest_remaining_barre_fret = other_barres[0][0]
                    self.chord.frets[s] = highest_remaining_barre_fret
                else:
                    self.chord.frets[s] = 0

    def _shift_single_notes(self, fret_delta: int) -> None:
        """Iterates through strings and shifts active fretted notes by a delta value."""
        for i in range(self.string_count):
            if self.chord.frets[i] > 0:
                self.chord.frets[i] = max(1, self.chord.frets[i] + fret_delta)

    def _shift_barre_structures(self, fret_delta: int) -> None:
        """Shifts all active barre chords vertically along the fretboard by a delta value."""
        updated_barres = []
        for fret, start_str, end_str in self.chord.barres:
            new_fret = max(1, fret + fret_delta)
            updated_barres.append((new_fret, start_str, end_str))
        self.chord.barres = updated_barres

    # -------------------------------------------------------------------------
    # Coordinate Helpers
    # -------------------------------------------------------------------------

    def _get_string_at_x(self, mouse_x: float, max_distance: Optional[float] = None) -> Optional[int]:
        """Maps a horizontal pixel input coordinate to the closest matching string layout line."""
        closest_string = None
        closest_distance = float('inf')

        for i in range(self.string_count):
            distance = abs(mouse_x - self.get_string_x(i))
            if distance < closest_distance:
                closest_distance = distance
                closest_string = i

        if max_distance is not None and closest_distance > max_distance:
            return None

        return closest_string

    def _get_fret_at_y(self, mouse_y: float) -> Optional[int]:
        """Maps a vertical pixel coordinate input to its matching fret matrix box index."""
        if mouse_y < self.top_margin - 5:
            return 0
        
        relative_y = mouse_y - self.top_margin
        fret = int(relative_y / self.fret_spacing) + 1

        if fret < 1 or fret > self.fret_count:
            return None
        
        return fret

    def _reset_drag_states(self) -> None:
        """Clears temporary cache values of states during drag-and-drop movements."""
        self.drag_start_fret = None
        self.drag_start_string = None
        self.current_drag_string = None
        self.update()

    def on_base_fret_change(self, new_base_fret: int) -> None:
        """Handles updates to the base fret, adjusting notes relatively to maintain visual form."""
        if new_base_fret < 1 or new_base_fret == self.chord.base_fret:
            return
        
        fret_delta = new_base_fret - self.chord.base_fret
        self.chord.base_fret = new_base_fret

        self._shift_single_notes(fret_delta)
        self._shift_barre_structures(fret_delta)
        self.update()

    def hasHeightForWidth(self) -> bool:
        """Informs Qt that the widget's height depends on its width."""
        return True

    def heightForWidth(self, width: int) -> int:
        """Defines the widget's proportions (4:5 ratio for standard guitar neck aspect)."""
        return int(width * 1.25)