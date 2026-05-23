import os
import logging

# Determine the backend root directory dynamically
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGS_DIR = os.path.join(BACKEND_ROOT, "logs")

# Ensure the logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

def get_custom_logger(name: str, log_file: str) -> logging.Logger:
    """
    Creates a customized logger that prints log events to both the terminal (StreamHandler)
    and a specific log file in the backend/logs directory (FileHandler).
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding duplicate handlers if the logger is retrieved multiple times
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # File Handler (logs saved to the dedicated log file)
        file_path = os.path.join(LOGS_DIR, log_file)
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Stream Handler (logs displayed in the terminal)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger
