"""
Centralized logging configuration (PRD section 32: Logging).

Logs to console always, and additionally to a rotating file under
Backend/logs/ so history survives restarts without growing unbounded.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "app.log"), maxBytes=5 * 1024 * 1024, backupCount=3,
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger("app")
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.propagate = False

    return root_logger


logger = setup_logging()
