"""This module provides a simple logging setup using loguru."""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_file_dir: Path | None = None, log_level: str = 'INFO') -> None:
    """Setup loguru configuration for the entire application.

    Args:
        log_file_dir: Optional directory path for log files. If provided, creates debug.log
        log_level: Minimum log level for console output (default: INFO)
    """
    # Remove default handler
    logger.remove()

    # Add console handler with custom format
    logger.add(
        sys.stdout, format='<green>{time:YYYY-MM-DD HH:mm:ss}</green> - {message}', level=log_level, colorize=True
    )

    # Add file handler if log directory is provided
    if log_file_dir:
        log_file_path = Path(log_file_dir) / 'debug.log'
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(log_file_path),
            format='{time:YYYY-MM-DD HH:mm:SS} - {name} - {level} - {message}',
            level='DEBUG',
            rotation='10 MB',
            retention='7 days',
            compression='zip',
        )


def get_logger(name: str):
    """Get the loguru logger instance.

    Note: loguru uses a singleton logger, so the name parameter is kept
    for compatibility but doesn't create separate logger instances.

    Args:
        name: Logger name (kept for compatibility)

    Returns:
        The loguru logger instance
    """
    return logger
