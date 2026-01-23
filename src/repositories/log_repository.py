""" Repository for managing logs using Prisma. MongoDB"""

from typing import List, Optional

from flask import Flask, jsonify
from prisma.models import Log
from prisma.types import LogCreateInput

from src.config.prisma_config import connect_prisma, disconnect_prisma, prisma
from src.utils.make_sync import make_sync

app = Flask(__name__)


class LogRepository:
    """

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

    async def _ensure_connected(self):
        await connect_prisma()

    async def add_log(self, log_data: LogCreateInput) -> Log:
        """Add a new log entry."""
        await self._ensure_connected()
        log = await self.prisma_client.log.create(data=log_data)
        return log

    @make_sync
    async def add_log_sync(self, log_data: LogCreateInput) -> Log:
        """Synchronous wrapper for add_log (for multiprocessing)."""
        return await self.add_log(log_data)

    async def get_all_logs(self) -> List[Log]:
        """Retrieve all logs, ordered by time descending."""
        await self._ensure_connected()
        logs = await self.prisma_client.log.find_many(order={"time": "desc"})
        return logs

    async def get_logs_by_level(self, level: str) -> List[Log]:
        """Retrieve logs filtered by level."""
        await self._ensure_connected()
        logs = await self.prisma_client.log.find_many(
            where={"level": level}, order={"time": "desc"}
        )
        return logs

    async def close_connection(self):
        """Close the Prisma connection."""
        await disconnect_prisma()

    async def get_last_logs(self, limit: int = 100) -> List[Log]:
        """Retrieve the last logs, ordered by time descending."""
        await self._ensure_connected()
        logs = await self.prisma_client.log.find_many(
            order={"time": "desc"}, take=limit
        )
        if logs is None:
            return []
        return logs or []

    @make_sync
    async def get_last_logs_sync(self, limit: int = 100) -> List[Log]:
        """Synchronous wrapper for get_last_logs (for multiprocessing)."""
        logs = await self.get_last_logs(limit)
        return list(logs) if logs else []


if __name__ == "__main__":
    app.run(debug=True)
