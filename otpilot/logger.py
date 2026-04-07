"""Rotating file logger for OTPilot.

This module configures OTPilot's primary rotating log file handler and
provides a helper to retrieve a configured logger instance.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

LOG_FILE: str = os.path.expanduser("~/.otpilot/otpilot.log")
LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def _has_rotating_handler(logger: logging.Logger, log_path: str) -> bool:
    """Check whether the logger already has a handler for ``log_path``.

    Args:
        logger (logging.Logger): Logger instance to inspect.
        log_path (str): Log file path to check for existing handlers.

    Returns:
        bool: ``True`` when a matching rotating handler is already attached.
    """
    normalized = os.path.abspath(log_path)
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            if os.path.abspath(getattr(handler, "baseFilename", "")) == normalized:
                return True
    return False


def get_logger(name: str = "otpilot") -> logging.Logger:
    """Return a configured rotating logger instance.

    Args:
        name (str): Logger name to retrieve.

    Returns:
        logging.Logger: Configured logger with rotating file handler attached.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not _has_rotating_handler(logger, LOG_FILE):
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)

    return logger
