"""
Logging configuration for SAM package.

Sets up structured logging with console output and optional file output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> None:
    """
    Configure logging for the SAM package.

    Args:
        level: Logging level (default: logging.INFO)
        log_file: Optional path to log file. If None, only console output.
        format_string: Custom format string. If None, uses default format.

    Examples:
        >>> # Basic setup (console only)
        >>> setup_logging()

        >>> # With log file
        >>> setup_logging(log_file=Path('sam_downloads.log'))

        >>> # Debug level
        >>> setup_logging(level=logging.DEBUG)
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Create formatter
    formatter = logging.Formatter(format_string)

    # Get root logger for 'sam' package
    logger = logging.getLogger('sam')
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler (prints to stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info(f"Logging to file: {log_file}")

    # Don't propagate to root logger (avoids duplicate messages)
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a SAM module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance

    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("Downloading data...")
    """
    return logging.getLogger(name)


# Set up default logging on import
# This ensures console output works out of the box
setup_logging()
