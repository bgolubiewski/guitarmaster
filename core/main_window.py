# core/main_window.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel
from PyQt6.QtCore import Qt
from ui.pages.chord_library_page import ChordLibraryPage

class MainWindow(QMainWindow):
    """
    The primary application shell window. Orchestrates top-level navigation,
    manages multi-page sub-modules via a dynamic QStackedWidget layout, 
    and handles global UI state restrictions during item modification.
    """
    def __init__(self, service):
        """
        Initializes backend dependencies, structural UI references, and coordinates setup operations.
        
        :param service: ChordService instance managing data workflows.
        """
        super().__init__()
        self.service = service

        self.stack = None
        self.chord_library_page = None
        self.songs_page = None
        self.btn_nav_chords = None
        self.btn_nav_songs = None
        
        self._setup_ui()

    def _setup_ui(self):
        """
        Configures global geometry parameters, mounts header menus, and links sub-page viewports.
        """
        self.setWindowTitle("GuitarMaster")
        self.resize(1300, 900)
        self.setMinimumSize(800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Upper Top Navigation Header Panel
        self._setup_navigation(main_layout)
        
        # Core Content Window Stack
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # Index 0: Main Chord Library Feature Screen
        self.chord_library_page = ChordLibraryPage(self.service)
        self.stack.addWidget(self.chord_library_page)
        
        # Index 1: Songs & Lyrics Milestone Placeholder Screen
        self.songs_page = self._create_songs_placeholder()
        self.stack.addWidget(self.songs_page)
        
        # Intercept state change signals from the chords context to block menu actions
        self.chord_library_page.edit_mode_changed.connect(self.set_navigation_locked)
        
        # Default application view configurations
        self._update_navigation_styles(0)
        self._setup_statusbar()

    def _setup_navigation(self, parent_layout: QVBoxLayout):
        """
        Assembles actionable menu components within the persistent dark navigation strip.
        """
        nav_bar = QWidget()
        nav_bar.setObjectName('navBar')
    
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(20, 10, 20, 10)
        
        self.btn_nav_chords = QPushButton("Chords Library")
        self.btn_nav_chords.setObjectName('navButton')
        self.btn_nav_chords.clicked.connect(lambda: self._switch_page(0))
        nav_layout.addWidget(self.btn_nav_chords)

        self.btn_nav_songs = QPushButton("Songs")
        self.btn_nav_songs.setObjectName('navButton')
        self.btn_nav_songs.clicked.connect(lambda: self._switch_page(1))
        nav_layout.addWidget(self.btn_nav_songs)
        
        nav_layout.addStretch()
        parent_layout.addWidget(nav_bar)

    def _create_songs_placeholder(self) -> QWidget:
        """
        Generates clean temporary fallback layouts for upcoming feature release versions.
        """
        page = QWidget()
        page.setObjectName('placeholderPage')
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl = QLabel("Songs & Lyrics Module\n\n(Feature planned for the next version update)")
        lbl.setObjectName('placeholderLabel')
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        return page

    def _switch_page(self, index: int):
        """
        Switches the visible stacked viewport index and updates structural focus cues.
        """
        self.stack.setCurrentIndex(index)
        self._update_navigation_styles(index)

    def _update_navigation_styles(self, active_index: int):
        """
        Re-evaluates specific inline styles across navigation elements based on application focus.
        """
        for index, btn in enumerate((self.btn_nav_chords, self.btn_nav_songs)):
            is_active = (index == active_index)
            btn.setProperty('active', is_active)

            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
    def set_navigation_locked(self, is_locked: bool):
        """
        Locks top-bar navigation tabs during active form mutations to prevent accidental page-change data loss.
        """
        self.btn_nav_chords.setEnabled(not is_locked)
        self.btn_nav_songs.setEnabled(not is_locked)

    def _setup_statusbar(self):
        """
        Initializes the standard technical footer readout container along the bottom edge.
        """
        sb = self.statusBar()
        sb.setObjectName('mainStatusBar')

        lbl = QLabel("version v1.0 - 2026 ")
        lbl.setObjectName('statusBarVersion')
        sb.addPermanentWidget(lbl)