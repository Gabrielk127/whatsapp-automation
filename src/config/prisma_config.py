""" Prisma client configuration module."""

from prisma import Prisma

prisma = Prisma()


async def connect_prisma():
    """Connect Prisma client"""
    if not prisma.is_connected():
        await prisma.connect()


async def disconnect_prisma():
    """Disconnect Prisma client"""
    if prisma.is_connected():
        await prisma.disconnect()
