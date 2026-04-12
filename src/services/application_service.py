"""Application orchestration service."""

from enum import Enum

from loguru import logger

from src.whatsapp import save_session, send_messages
from src.config.loguru_firebase_handler import setup_loguru



class AutomationMode(Enum):
    """Available automation modes."""
    AUTHENTICATE = "authenticate"  # Authentication only
    SEND = "send"  # Send only
    FULL = "full"  # Authentication + Send


class ApplicationService:
    """Coordinate application workflow."""

    def __init__(self, mode: AutomationMode = AutomationMode.FULL, include_firebase: bool = False) -> None:
        """
        Initialize application service.
        
        Args:
            mode: Automation mode (AUTHENTICATE, SEND or FULL)
            include_firebase: If True, includes Firebase logging
        """
        self.mode = mode
        self.include_firebase = include_firebase

    def run_application(self) -> None:
        """Run full application flow."""
        try:
            logger.success("🚀 Starting WhatsApp Automation...")
            
            # Setup Loguru for WhatsApp
            setup_loguru(include_firebase=self.include_firebase)
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
