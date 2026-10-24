# core/app.py
from services.chord_service import ChordService
from core.main_window import MainWindow

class App:
    """
    Application coordinator responsible for bootstrapping core business services,
    loading the persistent database layer, and mounting the primary user interface window.
    """
    def __init__(self) -> None:
        # Initialize the data logic layer and populate records from the disk
        self.chord_service = ChordService()
        self.chord_service.load_data_from_database()

        # Spawn the root window shell framework and pass down the service layer
        self.window = MainWindow(self.chord_service)
    
    def run(self) -> None:
        """
        Displays the main application window workspace.
        """
        self.window.show()