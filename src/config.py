import os

APP_NAME = "Signature PDF Tool"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Himangshu Singh"

# OS-Specific Identifiers
WINDOWS_APP_ID = "signaturepdf.app.version.1"

# App Data Directories
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".signaturepdf")
SIGNATURES_DIR = os.path.join(APP_DATA_DIR, "signatures")

def ensure_app_data_dirs():
    os.makedirs(SIGNATURES_DIR, exist_ok=True)
