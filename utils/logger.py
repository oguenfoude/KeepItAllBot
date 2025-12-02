"""
Logging configuration with rotating file handler and console output.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from config.settings import LOGS_PATH


def setup_logger(name: str = "bot") -> logging.Logger:
    """
    Set up a logger with rotating file handler and console output.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Log format
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (rotating, max 5MB, keep 3 backups)
    file_handler = RotatingFileHandler(
        LOGS_PATH / f"{name}.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Error file handler (separate file for errors only)
    error_handler = RotatingFileHandler(
        LOGS_PATH / f"{name}_errors.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger


# Default logger instance
logger = setup_logger("bot")
