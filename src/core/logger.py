import logging
import os
from config import APP_DATA_DIR, APP_NAME

def setup_logger():
    # Ensure the app data directory exists
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    log_file_path = os.path.join(APP_DATA_DIR, 'app.log')

    # Create logger
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.DEBUG)

    # Create file handler which logs even debug messages
    fh = logging.FileHandler(log_file_path)
    fh.setLevel(logging.DEBUG)

    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger

logger = setup_logger()
