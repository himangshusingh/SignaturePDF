import sys
import os
from ui.main_window import ApplicationGUI
from ui.styles import get_stylesheet
from config import ensure_app_data_dirs
from core.state_manager import global_state
from PyQt6.QtWidgets import QApplication

# Add path handling for packaged executable
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    base_path = sys._MEIPASS
    sys.path.append(os.path.join(base_path, 'src'))
else:
    # Running in normal Python environment
    base_path = os.path.dirname(__file__)

def main():
    ensure_app_data_dirs()
    app = QApplication(sys.argv)
    
    app.setStyle("Fusion")
    app.setStyleSheet(get_stylesheet(global_state.is_dark_theme))
    
    window = ApplicationGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()