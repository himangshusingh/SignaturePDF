import os
import sys
import ctypes

# Ensure we can import from src/ when PyInstaller runs this hook
try:
    base_path = sys._MEIPASS
except Exception:
    base_path = os.path.dirname(os.path.abspath(__file__))

src_path = os.path.join(base_path, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import config

def set_app_id():
    # Set Windows AppUserModelID to ensure the taskbar icon is not grouped with Python
    if os.name == 'nt':
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(config.WINDOWS_APP_ID)
        except Exception:
            pass

set_app_id()
