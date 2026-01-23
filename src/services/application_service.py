"""Application orchestration service."""

import asyncio

from loguru import logger

from src.config.loguru_mongo_handler import setup_loguru
from src.repositories.log_repository import LogRepository


class ApplicationService:
    """Coordinate application workflow."""

    def __init__(
        self,
    ) -> None:
        pass

    async def run_application(self) -> None:
        """Run full application flow."""
        try:
            setup_loguru(LogRepository())
            logger.success("Loguru setup completed successfully.")
        finally:
            logger.info("Application run completed.")

    def run_sync(self) -> None:
        """Run application"""
        asyncio.run(self.run_application())
