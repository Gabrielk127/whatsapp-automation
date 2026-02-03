"""Application orchestration service."""

from enum import Enum

from loguru import logger

from src.whatsapp import save_session, send_messages
from src.config.loguru_mongo_handler import setup_loguru
from src.repositories.log_repository import LogRepository


class AutomationMode(Enum):
    """Available automation modes."""
    AUTHENTICATE = "authenticate"  # Authentication only
    SEND = "send"  # Send only
    FULL = "full"  # Authentication + Send


class ApplicationService:
    """Coordinate application workflow."""

    def __init__(self, mode: AutomationMode = AutomationMode.FULL, include_mongodb: bool = False) -> None:
        """
        Initialize application service.
        
        Args:
            mode: Automation mode (AUTHENTICATE, SEND or FULL)
            include_mongodb: If True, includes MongoDB logging
        """
        self.mode = mode
        self.include_mongodb = include_mongodb

    def run_application(self) -> None:
        """Run full application flow."""
        try:
            logger.success("🚀 Starting WhatsApp Automation...")
            
            # Setup Loguru for WhatsApp
            log_repository = LogRepository() if self.include_mongodb else None
            setup_loguru(include_mongodb=self.include_mongodb, log_repository=log_repository)
            logger.info(f"🤖 Automation mode: {self.mode.value.upper()}")
            
            # Execute automation according to mode
            if self.mode == AutomationMode.AUTHENTICATE:
                logger.info("🔐 Starting authentication only...")
                save_session()
                logger.success("✅ Authentication complete!")
                
            elif self.mode == AutomationMode.SEND:
                logger.info("📤 Starting message sending...")
                send_messages()
                logger.success("✅ Sending complete!")
                
            elif self.mode == AutomationMode.FULL:
                logger.info("🚀 Starting full automation (Authentication + Send)...")
                logger.info("Step 1: Authentication")
                save_session()
                logger.success("✅ Authentication complete!")
                
                logger.info("Step 2: Message sending")
                send_messages()
                logger.success("✅ Sending complete!")
                
        except Exception as e:
            logger.error(f"❌ Error during execution: {e}", exc_info=True)
            raise
        finally:
            logger.info("Application run completed.")

    def run_sync(self) -> None:
        """Run application synchronously."""
        self.run_application()
