import sys
import os
from PyQt6.QtWidgets import QApplication

# Add path handling for packaged executable
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    base_path = sys._MEIPASS
    sys.path.append(os.path.join(base_path, 'src'))
else:
    # Running in normal Python environment
    base_path = os.path.dirname(__file__)

from gui import SignaturePDFGUI

def main():
    app = QApplication(sys.argv)
    
    # Enable High-DPI scaling (handled automatically in PyQt6, but good practice to ensure clean styles)
    app.setStyle("Fusion")
    
    window = SignaturePDFGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()