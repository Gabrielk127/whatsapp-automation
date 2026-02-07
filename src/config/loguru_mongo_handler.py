"""Loguru handler for MongoDB logging using the new PyMongo setup."""

import sys
from loguru import logger
from src.repositories.mongo_repository import mongo_repo


def setup_loguru(include_mongodb: bool = False):
    """
    Setup Loguru logger.
    
    Args:
        include_mongodb: If True, adds MongoDB handler (connects to MongoDB)
    """
    logger.remove()
    
    # Console Handler only
    console_format = (
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    logger.add(sys.stdout, format=console_format, level="DEBUG", colorize=True)
    
    # MongoDB Handler (optional)
    if include_mongodb:
        try:
            if mongo_repo.connect():
                # Add handler that writes logs to MongoDB
                def mongo_sink(message):
                    record = message.record
                    context = {
                        "location": f"{record['file'].name}:{record['line']}",
                        "function": record["function"],
                    }
                    mongo_repo.save_log(
                        level=record["level"].name,
                        message=record["message"],
                        context=context
                    )
                
                logger.add(mongo_sink, level="INFO")
                logger.info("📊 MongoDB logging enabled")
        except Exception as e:
            logger.warning(f"Failed to configure MongoDB logging: {e}")
