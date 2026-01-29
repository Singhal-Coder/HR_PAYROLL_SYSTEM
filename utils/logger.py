import logging.config
from config.settings import LOG_CONFIG

def setup_logging():
    """
    Application wide logging setup karta hai.
    """
    logging.config.dictConfig(LOG_CONFIG)