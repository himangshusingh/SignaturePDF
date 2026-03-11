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
    
    # Load bundled fonts
    from PyQt6.QtGui import QFontDatabase
    from assets import get_resource_path
    font_files = [
        get_resource_path(os.path.join('assets', 'DM_Mono', 'DMMono-Regular.ttf')),
        get_resource_path(os.path.join('assets', 'DM_Mono', 'DMMono-Medium.ttf')),
        get_resource_path(os.path.join('assets', 'DM_Mono', 'DMMono-Light.ttf')),
        get_resource_path(os.path.join('assets', 'Syne', 'Syne-Regular.ttf')),
        get_resource_path(os.path.join('assets', 'Syne', 'Syne-Medium.ttf')),
        get_resource_path(os.path.join('assets', 'Syne', 'Syne-SemiBold.ttf')),
        get_resource_path(os.path.join('assets', 'Syne', 'Syne-Bold.ttf')),
        get_resource_path(os.path.join('assets', 'Syne', 'Syne-ExtraBold.ttf')),
    ]
    for font_path in font_files:
        if os.path.exists(font_path):
            QFontDatabase.addApplicationFont(font_path)
    
    app.setStyle("Fusion")
    app.setStyleSheet(get_stylesheet(global_state.is_dark_theme))
    
    window = ApplicationGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()