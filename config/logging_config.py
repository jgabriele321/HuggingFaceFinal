#!/usr/bin/env python3
"""
Enhanced logging configuration for SmolAgent debugging
"""

import os
import logging
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

def configure_logging():
    """Configure detailed logging for all components"""
    
    # Root logger configuration - capture everything
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Output to console
            logging.FileHandler(logs_dir / "debug.log", mode="w")  # Fresh log file each run
        ]
    )
    
    # Configure specific module loggers
    loggers = {
        "OpenRouterAgent": logging.DEBUG,
        "SmolAgent": logging.DEBUG,
        "final_answer_processor": logging.DEBUG,
        "tool_validator": logging.DEBUG,
        "YouTubeTool": logging.DEBUG,
    }
    
    # Set individual logger levels
    for logger_name, level in loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        
        # Add file handler for each module
        file_handler = logging.FileHandler(logs_dir / f"{logger_name.lower()}.log", mode="w")
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
        # Add debug info
        logger.debug(f"Logger {logger_name} initialized at level {logging.getLevelName(level)}")
    
    # Set smolagents to DEBUG level
    try:
        smolagents_logger = logging.getLogger("smolagents")
        smolagents_logger.setLevel(logging.DEBUG)
        smolagents_file_handler = logging.FileHandler(logs_dir / "smolagents.log", mode="w")
        smolagents_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        smolagents_logger.addHandler(smolagents_file_handler)
    except Exception as e:
        logging.error(f"Failed to configure smolagents logger: {e}")
    
    logging.info("Enhanced logging configuration applied") 