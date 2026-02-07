"""Custom exceptions for WhatsApp automation."""


class WhatsAppException(Exception):
    """Base exception for all WhatsApp automation errors."""
    
    def __init__(self, message: str, context: dict = None):
        """
        Initialize exception with message and optional context.
        
        Args:
            message: Error message
            context: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
    
    def __str__(self):
        if self.context:
            return f"{self.message} | Context: {self.context}"
        return self.message


class AuthenticationException(WhatsAppException):
    """Exception raised when authentication fails."""
    pass


class PhoneValidationException(WhatsAppException):
    """Exception raised when phone number validation fails."""
    
    def __init__(self, phone: str, reason: str, context: dict = None):
        """
        Initialize phone validation exception.
        
        Args:
            phone: The invalid phone number
            reason: Reason for validation failure
            context: Optional additional context
        """
        message = f"Invalid phone number: {phone} - {reason}"
        super().__init__(message, context)
        self.phone = phone
        self.reason = reason


class MessageSendException(WhatsAppException):
    """Exception raised when message sending fails."""
    
    def __init__(self, phone: str, message_num: int, reason: str, context: dict = None):
        """
        Initialize message send exception.
        
        Args:
            phone: Phone number where send failed
            message_num: Message number that failed
            reason: Reason for send failure
            context: Optional additional context
        """
        message = f"Failed to send message {message_num} to {phone}: {reason}"
        super().__init__(message, context)
        self.phone = phone
        self.message_num = message_num
        self.reason = reason


class PhoneNotFoundException(WhatsAppException):
    """Exception raised when phone number is not found on WhatsApp."""
    
    def __init__(self, phone: str, context: dict = None):
        """
        Initialize phone not found exception.
        
        Args:
            phone: Phone number not found
            context: Optional additional context
        """
        message = f"Phone number not found on WhatsApp: {phone}"
        super().__init__(message, context)
        self.phone = phone


class RateLimitException(WhatsAppException):
    """Exception raised when rate limit is hit."""
    
    def __init__(self, retry_after: int = None, context: dict = None):
        """
        Initialize rate limit exception.
        
        Args:
            retry_after: Seconds to wait before retry
            context: Optional additional context
        """
        message = f"Rate limit exceeded"
        if retry_after:
            message += f" - retry after {retry_after}s"
        super().__init__(message, context)
        self.retry_after = retry_after


class DatabaseException(WhatsAppException):
    """Exception raised when database operations fail."""
    
    def __init__(self, operation: str, reason: str, context: dict = None):
        """
        Initialize database exception.
        
        Args:
            operation: Database operation that failed
            reason: Reason for failure
            context: Optional additional context
        """
        message = f"Database {operation} failed: {reason}"
        super().__init__(message, context)
        self.operation = operation
        self.reason = reason


class BrowserException(WhatsAppException):
    """Exception raised when browser operations fail."""
    
    def __init__(self, operation: str, reason: str, context: dict = None):
        """
        Initialize browser exception.
        
        Args:
            operation: Browser operation that failed
            reason: Reason for failure
            context: Optional additional context
        """
        message = f"Browser {operation} failed: {reason}"
        super().__init__(message, context)
        self.operation = operation
        self.reason = reason
