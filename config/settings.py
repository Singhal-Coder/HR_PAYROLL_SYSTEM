import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Constants
DB_NAME = os.getenv("DB_NAME", "hrms.db")
DB_PATH = os.path.join("database", DB_NAME)

# Admin Defaults
ADMIN_DEFAULT_USER = os.getenv("ADMIN_DEFAULT_USER", "admin")
ADMIN_DEFAULT_PASS = os.getenv("ADMIN_DEFAULT_PASS", "admin123")

# Network
OFFICE_WIFI_SSID = os.getenv("OFFICE_WIFI_SSID", "")

# App Settings
LATE_THRESHOLD = os.getenv("LATE_THRESHOLD_TIME", "10:00:00")

# Logging Configuration
LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'file_handler': {
            'level': os.getenv("LOG_LEVEL", "INFO"),
            'class': 'logging.FileHandler',
            'filename': os.getenv("LOG_FILE", "system.log"),
            'formatter': 'standard',
            'encoding': 'utf-8'
        },
        'stream_handler': {
            'level': os.getenv("LOG_LEVEL", "INFO"),
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        }
    },
    'root': {
        'handlers': ['file_handler', 'stream_handler'],
        'level': os.getenv("LOG_LEVEL", "INFO"),
    }
}