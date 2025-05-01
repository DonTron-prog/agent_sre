"""
Helper utilities for the RAG component.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Union


def setup_logger(
    name: str = "code_rag",
    level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Set up a logger with the specified configuration.
    
    Args:
        name: Name of the logger
        level: Logging level (default: INFO)
        log_file: Optional path to log file
        format_string: Optional format string for log messages
        
    Returns:
        logging.Logger: Configured logger instance
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is provided
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Create a default logger instance
logger = setup_logger()