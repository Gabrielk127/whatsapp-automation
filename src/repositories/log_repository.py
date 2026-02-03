""" Repository for managing logs using Prisma. MongoDB"""

import asyncio
from typing import List, Optional

from prisma.models import Log
from prisma.types import LogCreateInput

from src.config.prisma_config import prisma


class LogRepository:
    """
    Repository for managing Log entries.
    Implements Singleton pattern to ensure only one instance exists.
    """

    _instance: Optional["LogRepository"] = None
    _initialized: bool = False

    def __new__(cls) -> "LogRepository":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.prisma_client = prisma
            LogRepository._initialized = True

    async def ensure_connected(self):
        """Ensure Prisma client is connected."""
        if not self.prisma_client.is_connected():
            try:
                await self.prisma_client.connect()
            except Exception as e:
                print(f"Error connecting to Prisma: {e}")
                raise

    async def add_log(self, log_data: LogCreateInput) -> Log:
        """Add a new log entry."""
        await self.ensure_connected()
        log = await self.prisma_client.log.create(data=log_data)
        return log

    def add_log_sync(self, log_data: LogCreateInput) -> Optional[Log]:
        """Synchronous wrapper for add_log."""
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                return loop.run_until_complete(self.add_log(log_data))
            else:
                # If loop is already running, use threading approach
                import threading
                result = [None]
                exception = [None]
                
                def run_in_thread():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        result[0] = new_loop.run_until_complete(self.add_log(log_data))
                        new_loop.close()
                    except Exception as e:
                        exception[0] = e
                
                thread = threading.Thread(target=run_in_thread, daemon=False)
                thread.start()
                thread.join(timeout=30)
                
                if exception[0]:
                    raise exception[0]
                return result[0]
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.add_log(log_data))
            finally:
                loop.close()

    async def get_all_logs(self) -> List[Log]:
        """Retrieve all logs, ordered by time descending."""
        await self.ensure_connected()
        logs = await self.prisma_client.log.find_many(order={"time": "desc"})
        return logs

    async def get_logs_by_level(self, level: str) -> List[Log]:
        """Retrieve logs filtered by level."""
        await self.ensure_connected()
        logs = await self.prisma_client.log.find_many(
            where={"level": level}, order={"time": "desc"}
        )
        return logs

    async def get_last_logs(self, limit: int = 100) -> List[Log]:
        """Retrieve the last logs, ordered by time descending."""
        await self.ensure_connected()
        logs = await self.prisma_client.log.find_many(
            order={"time": "desc"}, take=limit
        )
        if logs is None:
            return []
        return logs or []

    async def close_connection(self):
        """Close the Prisma connection."""
        if self.prisma_client.is_connected():
            try:
                await self.prisma_client.disconnect()
            except Exception as e:
                print(f"Error disconnecting: {e}")
