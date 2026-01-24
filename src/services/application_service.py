"""Application orchestration service."""

from enum import Enum

from loguru import logger

from src.whatsapp import save_session, enviar_mensagens
from src.config.loguru_mongo_handler import setup_loguru


class AutomationMode(Enum):
    """Modos de automação disponíveis."""
    AUTHENTICATE = "authenticate"  # Apenas autenticação
    SEND = "send"  # Apenas envio
    FULL = "full"  # Autenticação + Envio


class ApplicationService:
    """Coordinate application workflow."""

    def __init__(self, mode: AutomationMode = AutomationMode.FULL, include_mongodb: bool = False) -> None:
        """
        Inicializa o serviço de aplicação.
        
        Args:
            mode: Modo de automação (AUTHENTICATE, SEND ou FULL)
            include_mongodb: Se True, inclui logging em MongoDB
        """
        self.mode = mode
        self.include_mongodb = include_mongodb

    def run_application(self) -> None:
        """Run full application flow."""
        try:
            logger.success("🚀 Iniciando WhatsApp Automation...")
            
            # Setup Loguru para WhatsApp
            setup_loguru(include_mongodb=self.include_mongodb)
            logger.info(f"🤖 Modo de automação: {self.mode.value.upper()}")
            
            # Executa automação de acordo com o modo
            if self.mode == AutomationMode.AUTHENTICATE:
                logger.info("🔐 Iniciando apenas autenticação...")
                save_session()
                logger.success("✅ Autenticação concluída!")
                
            elif self.mode == AutomationMode.SEND:
                logger.info("📤 Iniciando envio de mensagens...")
                enviar_mensagens()
                logger.success("✅ Envio concluído!")
                
            elif self.mode == AutomationMode.FULL:
                logger.info("🚀 Iniciando automação completa (Autenticação + Envio)...")
                logger.info("Etapa 1: Autenticação")
                save_session()
                logger.success("✅ Autenticação concluída!")
                
                logger.info("Etapa 2: Envio de mensagens")
                enviar_mensagens()
                logger.success("✅ Envio concluído!")
                
        except Exception as e:
            logger.error(f"❌ Erro durante a execução: {e}", exc_info=True)
            raise
        finally:
            logger.info("Application run completed.")

    def run_sync(self) -> None:
        """Run application synchronously."""
        self.run_application()
