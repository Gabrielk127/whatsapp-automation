"""Loguru handler for Firebase logging."""
import sys
from loguru import logger
from src.repositories.firebase_repository import firebase_repo

def setup_loguru(include_firebase: bool = False):
    """
    Setup Loguru logger.
    
    Args:
        include_firebase: If True, adds Firebase handler
    """
    logger.remove()
    
    # Console Handler
    console_format = (
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    logger.add(sys.stdout, format=console_format, level="DEBUG", colorize=True)
    
    # Firebase Handler
    if include_firebase:
        try:
            if firebase_repo.connect():
                def firebase_sink(message):
                    record = message.record
                    context = {
                        "location": f"{record['file'].name}:{record['line']}",
                        "function": record["function"],
                    }
                    firebase_repo.save_log(
                        level=record["level"].name,
                        message=record["message"],
                        context=context
                    )
                
                logger.add(firebase_sink, level="INFO")
                logger.info("📊 Firebase logging enabled")
        except Exception as e:
            logger.warning(f"Failed to configure Firebase logging: {e}")

# Maintain backward compatibility for setup function call
def setup_loguru_backend(include_db: bool = False):
    return setup_loguru(include_firebase=include_db)
