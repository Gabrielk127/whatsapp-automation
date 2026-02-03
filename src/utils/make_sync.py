"""Decorator to convert async functions to sync."""

import asyncio
from functools import wraps

import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()


def make_sync(async_func):
    """Decorator that converts an async function to sync."""
    @wraps(async_func)
    def sync_wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(async_func(*args, **kwargs))
    
    return sync_wrapper
