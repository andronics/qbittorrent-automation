"""
Centralized logging configuration for qBittorrent automation
Provides consistent logging setup across all modules and triggers
"""

import sys
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.config import Config

# Standard log formats
LOG_FORMAT_SIMPLE = '%(asctime)s | %(levelname)-8s | %(message)s'
LOG_FORMAT_DETAILED = '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def setup_logging(config: 'Config', trace_mode: bool = False):
    """
    Setup logging configuration with fallback to console-only

    Configures both file and console handlers with standardized format.
    Falls back gracefully to console-only logging if file logging fails.

    Args:
        config: Configuration object with logging settings
        trace_mode: If True, use detailed format with module/function/line context
    """
    log_level = config.get_log_level()

    # Select format based on trace mode
    log_format = LOG_FORMAT_DETAILED if trace_mode else LOG_FORMAT_SIMPLE

    # Try to setup file logging
    file_handler = None
    try:
        log_file = config.get_log_file()
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(log_format, datefmt=DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
    except (PermissionError, OSError) as e:
        # Fall back to console-only logging
        print(f"Cannot setup file logging: {e}", file=sys.stderr)
        print(f"Continuing with console-only logging", file=sys.stderr)

    # Console handler (always works)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_formatter = logging.Formatter(log_format, datefmt=DATE_FORMAT)
    console_handler.setFormatter(console_formatter)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    if file_handler:
        logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance configured for the module
    """
    return logging.getLogger(name)
