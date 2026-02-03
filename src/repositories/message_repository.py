"""Repository for managing SentMessage using Prisma."""

import asyncio
from typing import Optional

from prisma.models import SentMessage
from prisma.types import SentMessageCreateInput

from src.config.prisma_config import prisma


class MessageRepository:
    """
    Repository for managing SentMessage entries.
    Implements Singleton pattern.
    Maintains a persistent connection to the database.
    """

    _instance: Optional["MessageRepository"] = None
    _initialized: bool = False

    def __new__(cls) -> "MessageRepository":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.prisma_client = prisma
            self._connection_task = None
            MessageRepository._initialized = True

    async def ensure_connected(self):
        """Ensure Prisma client is connected."""
        if not self.prisma_client.is_connected():
            try:
                await self.prisma_client.connect()
                print("✅ Prisma connected successfully")
            except Exception as e:
                print(f"❌ Error connecting to Prisma: {e}")
                raise

    async def add_message(self, name: str, phone: str, status: str) -> SentMessage:
        """Add a new sent message entry."""
        try:
            await self.ensure_connected()
            message_data: SentMessageCreateInput = {
                "name": name,
                "phones": [phone],  # phones is now an array
                "status": status,
            }
            message = await self.prisma_client.sentmessage.create(data=message_data)
            print(f"✅ Message saved: {name} ({phone}) - {status}")
            return message
        except Exception as e:
            print(f"❌ Error in add_message: {type(e).__name__}: {e}")
            raise

    async def add_message_batch(self, name: str, phones: list, status: str) -> SentMessage:
        """Add a sent message entry with multiple phones."""
        try:
            await self.ensure_connected()
            message_data: SentMessageCreateInput = {
                "name": name,
                "phones": phones,  # phones is an array
                "status": status,
            }
            message = await self.prisma_client.sentmessage.create(data=message_data)
            print(f"✅ Message batch saved: {name} - {len(phones)} phones - {status}")
            return message
        except Exception as e:
            print(f"❌ Error in add_message_batch: {type(e).__name__}: {e}")
            raise

    def add_message_batch_sync(self, name: str, phones: list, status: str) -> Optional[SentMessage]:
        """Synchronous wrapper for add_message_batch."""
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                return loop.run_until_complete(self.add_message_batch(name, phones, status))
            else:
                # If loop is already running, use threading approach
                import threading
                result = [None]
                exception = [None]
                
                def run_in_thread():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        result[0] = new_loop.run_until_complete(self.add_message_batch(name, phones, status))
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
                return loop.run_until_complete(self.add_message_batch(name, phones, status))
            finally:
                loop.close()

    def add_message_sync(self, name: str, phone: str, status: str) -> Optional[SentMessage]:
        """
        Synchronous wrapper for add_message.
        Uses a simple approach without threading to avoid event loop issues.
        """
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            
            # If we're in the main thread and loop is not running, use it directly
            if not loop.is_running():
                return loop.run_until_complete(self.add_message(name, phone, status))
            else:
                # If loop is already running, we need to run in a new thread
                # But we'll use a simpler approach: create a new event loop in current thread
                import concurrent.futures
                import threading
                
                result = [None]
                exception = [None]
                
                def run_in_thread():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        result[0] = new_loop.run_until_complete(self.add_message(name, phone, status))
                        new_loop.close()
                    except Exception as e:
                        exception[0] = e
                
                thread = threading.Thread(target=run_in_thread, daemon=False)
                thread.start()
                thread.join(timeout=30)  # Wait max 30 seconds
                
                if exception[0]:
                    raise exception[0]
                return result[0]
                
        except RuntimeError:
            # No event loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.add_message(name, phone, status))
            finally:
                loop.close()

    async def close_connection(self):
        """Close the Prisma connection."""
        if self.prisma_client.is_connected():
            try:
                await self.prisma_client.disconnect()
                print("✅ Prisma disconnected")
            except Exception as e:
                print(f"⚠️ Error disconnecting: {e}")
