# main.py
import sys
from PyQt6.QtWidgets import QApplication
from core.app import App
from assets.theme import load_stylesheet

def main() -> None:
    """
    Main application entry point. Initializes the low-level Qt subsystem,
    configures global theme visuals, bootstraps components, and launches the runtime event loop.
    """
    app = QApplication(sys.argv)
    
    app.setStyle("Fusion")
    load_stylesheet(app)

    application = App()
    application.run()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()