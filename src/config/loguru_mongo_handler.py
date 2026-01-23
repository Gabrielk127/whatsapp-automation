"""Loguru handler for MongoDB logging using multiprocessing."""

import atexit
import json
import multiprocessing
from datetime import datetime

from loguru import logger

from src.repositories.log_repository import LogRepository


class MongoDBLoguruHandler:
    """Loguru handler for writing logs to MongoDB using multiprocessing."""

    def __init__(self, log_repository: LogRepository):
        self.log_repository = log_repository
        self.queue = multiprocessing.Queue()
        self.worker = multiprocessing.Process(
            target=self._worker_func, args=(self.queue,)
        )
        self.worker.start()
        atexit.register(self._cleanup)

    def _cleanup(self):
        self.queue.put(None)
        self.worker.join(timeout=5)

    def _worker_func(self, queue):
        repo = LogRepository()
        while True:
            log_data = queue.get()
            if log_data is None:
                break
            try:
                repo.add_log_sync(log_data)  # type: ignore
            except RuntimeError as e:
                print(f"Runtime error writing log to MongoDB: {e}")

    def write(self, message):
        """Write a log message to the MongoDB repository."""
        record = message.record
        context_data = {
            "location": record["file"].name + ":" + str(record["line"]),
            "function": record["function"],
        }

        log_data = {
            "level": record["level"].name,
            "message": record["message"],
            "time": record["time"],
            "context": json.dumps(context_data),
        }
        self.queue.put(log_data)


def setup_loguru(log_repository: LogRepository):
    """Setup Loguru logger with MongoDB handler using multiprocessing."""
    handler = MongoDBLoguruHandler(log_repository)
    logger.add(handler.write, level="DEBUG")
