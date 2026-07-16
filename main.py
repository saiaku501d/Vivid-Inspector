import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import SpriteComparerApp

def main():
    """
    Application entry point.
    Initializes the Qt Application and launches the main window.
    """
    app = QApplication(sys.argv)
    
    # Set global font settings
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    # Initialize and show the main UI component
    window = SpriteComparerApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()