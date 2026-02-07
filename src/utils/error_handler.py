"""Error handling utilities with retry logic and context tracking."""

import time
import functools
import traceback
from typing import Callable, Any, Optional, Type
from loguru import logger

from src.whatsapp.exceptions import WhatsAppException


class ErrorContext:
    """Tracks error context for debugging and analysis."""
    
    def __init__(self, operation: str, **kwargs):
        """
        Initialize error context.
        
        Args:
            operation: Name of the operation being performed
            **kwargs: Additional context data
        """
        self.operation = operation
        self.context = kwargs
        self.errors = []
    
    def add_error(self, error: Exception, attempt: int):
        """
        Add error to context.
        
        Args:
            error: The exception that occurred
            attempt: Attempt number when error occurred
        """
        self.errors.append({
            'attempt': attempt,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        })
    
    def get_summary(self) -> dict:
        """Get summary of error context."""
        return {
            'operation': self.operation,
            'context': self.context,
            'total_errors': len(self.errors),
            'errors': self.errors
        }


def retry_on_exception(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator to retry function on exception with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay between retries
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function called on each retry
    
    Example:
        @retry_on_exception(max_attempts=3, initial_delay=1.0)
        def send_message():
            # code that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"⚠️ {func.__name__} failed (attempt {attempt}/{max_attempts}): {e}"
                    )
                    logger.info(f"   Retrying in {delay:.1f}s...")
                    
                    if on_retry:
                        on_retry(attempt, e, delay)
                    
                    time.sleep(delay)
                    delay *= backoff_factor
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def handle_exception(
    operation: str,
    reraise: bool = True,
    log_level: str = "error",
    **context_kwargs
):
    """
    Decorator to handle exceptions with context tracking.
    
    Args:
        operation: Name of the operation being performed
        reraise: Whether to reraise the exception after handling
        log_level: Log level to use (debug, info, warning, error)
        **context_kwargs: Additional context to track
    
    Example:
        @handle_exception(operation="send_message", contact="John", phone="123")
        def send_message():
            # code that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            error_context = ErrorContext(operation, **context_kwargs)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_context.add_error(e, attempt=1)
                
                # Log with appropriate level
                log_func = getattr(logger, log_level, logger.error)
                log_func(
                    f"❌ Error in {operation}: {type(e).__name__}: {e}"
                )
                logger.debug(f"   Context: {error_context.get_summary()}")
                
                if reraise:
                    raise
                
                return None
        
        return wrapper
    return decorator


class ErrorRecovery:
    """Strategies for error recovery."""
    
    @staticmethod
    def should_retry(exception: Exception) -> bool:
        """
        Determine if an exception should trigger a retry.
        
        Args:
            exception: The exception to check
            
        Returns:
            True if should retry, False otherwise
        """
        from src.whatsapp.exceptions import (
            RateLimitException,
            BrowserException,
            DatabaseException
        )
        
        # Always retry rate limits and transient browser errors
        if isinstance(exception, (RateLimitException, BrowserException)):
            return True
        
        # Retry database errors (might be transient connection issues)
        if isinstance(exception, DatabaseException):
            return True
        
        # Don't retry validation errors
        from src.whatsapp.exceptions import PhoneValidationException
        if isinstance(exception, PhoneValidationException):
            return False
        
        # For generic exceptions, check message for transient error indicators
        error_msg = str(exception).lower()
        transient_indicators = [
            'timeout', 'connection', 'network', 'temporary',
            'unavailable', 'busy', 'overload'
        ]
        
        return any(indicator in error_msg for indicator in transient_indicators)
    
    @staticmethod
    def get_retry_delay(exception: Exception, attempt: int) -> float:
        """
        Calculate retry delay based on exception type and attempt number.
        
        Args:
            exception: The exception that occurred
            attempt: Current attempt number
            
        Returns:
            Delay in seconds before retry
        """
        from src.whatsapp.exceptions import RateLimitException
        
        # Use retry_after if specified in RateLimitException
        if isinstance(exception, RateLimitException) and exception.retry_after:
            return exception.retry_after
        
        # Exponential backoff: 1s, 2s, 4s, 8s, ...
        return min(2 ** (attempt - 1), 60)  # Cap at 60 seconds


def safe_execute(func: Callable, *args, default=None, log_errors=True, **kwargs) -> Any:
    """
    Safely execute a function, returning default value on error.
    
    Args:
        func: Function to execute
        *args: Positional arguments for function
        default: Default value to return on error
        log_errors: Whether to log errors
        **kwargs: Keyword arguments for function
        
    Returns:
        Function result or default value on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.debug(f"Error in {func.__name__}: {e}")
        return default
