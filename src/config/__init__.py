"""
FedSpeak Configuration Module
==============================

Configuration and logging setup.
"""

import os
import logging
import logging.handlers
import json
from pathlib import Path
from typing import Optional


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs log records as JSON objects for easy parsing.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        return json.dumps(log_data)


def setup_logging(log_dir: Optional[str] = None, level: str = 'INFO',
                  log_to_console: bool = True, log_to_file: bool = True) -> None:
    """
    Configure structured logging for FedSpeak.

    Sets up:
    - JSON formatting for file logs
    - Console logging (optional)
    - Daily log rotation
    - Appropriate log levels

    Args:
        log_dir: Directory for log files (default: from config or 'logs/')
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file

    Example:
        >>> setup_logging(level='DEBUG', log_to_console=True)
    """
    # Import here to avoid circular dependency
    from .settings import get_settings

    # Get log directory from config if not provided
    if log_dir is None:
        settings = get_settings()
        log_dir = settings.get('logging.log_dir', default='logs')

    # Ensure log directory exists
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    # File handler with JSON formatting and daily rotation
    if log_to_file:
        log_file = log_path / 'fedspeak.log'
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    # Console handler with standard formatting
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    logging.info(f"Logging configured: level={level}, log_dir={log_dir}, "
                f"console={log_to_console}, file={log_to_file}")


__all__ = ['JSONFormatter', 'setup_logging']
