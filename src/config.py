import os

APP_NAME = "SignaturePDF"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Himangshu Singh"

# OS-Specific Identifiers
APP_NAME_LOWER = APP_NAME.lower().replace(" ", "")
WINDOWS_APP_ID = f"{APP_NAME_LOWER}.app.version.1"

# App Data Directories
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), f".{APP_NAME_LOWER}")
SIGNATURES_DIR = os.path.join(APP_DATA_DIR, "signatures")

def ensure_app_data_dirs():
    os.makedirs(SIGNATURES_DIR, exist_ok=True)
