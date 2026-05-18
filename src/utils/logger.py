"""
Logging configuration
"""

import logging
import logging.handlers
import os
from datetime import datetime


def setup_logger(name: str, log_dir: str = "logs") -> logging.Logger:
    """
    Setup logger with file and console handlers
    
    Args:
        name: Logger name
        log_dir: Directory for log files
        
    Returns:
        Configured logger instance
    """
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # File handler
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
