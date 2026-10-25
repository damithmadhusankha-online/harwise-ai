"""Centralized logging configuration for Harwise AI.

Application logs are written to logs/harwise.log.
Log rotation prevents unlimited file growth.
Warnings and errors are also displayed in the console.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "harwise.log"

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3


def get_logger(name: str = "harwise") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Reuse handlers previously configured by Harwise.
    if any(
        getattr(handler, "_harwise_managed", False)
        for handler in logger.handlers
    ):
        return logger

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT)

    # Store application logs with automatic file rotation.
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    file_handler._harwise_managed = True

    # Display only warnings and errors in the console.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    console_handler._harwise_managed = True

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
