"""Structured logging utilities for WhatsApp automation."""
import json
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger


class StructuredLogger:
    """
    Wrapper for structured logging with context.
    
    Provides methods to log events with structured data that can be
    easily parsed and analyzed programmatically.
    """
    
    @staticmethod
    def log_message_attempt(
        contact_name: str,
        phone: str,
        message_number: int,
        total_messages: int,
        status: str,
        error: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None
    ):
        """
        Log a message sending attempt with structured data.
        
        Args:
            contact_name: Name of the contact
            phone: Phone number
            message_number: Current message number (1, 2, 3)
            total_messages: Total messages to send
            status: Status of the attempt (success, failed, invalid, not_found)
            error: Optional error message
            extra_context: Optional additional context data
        """
        context = {
            "event": "message_attempt",
            "contact_name": contact_name,
            "phone": phone,
            "message_number": message_number,
            "total_messages": total_messages,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if error:
            context["error"] = error
        
        if extra_context:
            context.update(extra_context)
        
        # Log with appropriate level
        if status == "success":
            logger.success(f"Message sent | {json.dumps(context, ensure_ascii=False)}")
        elif status in ["failed", "error"]:
            logger.error(f"Message failed | {json.dumps(context, ensure_ascii=False)}")
        elif status in ["invalid", "not_found"]:
            logger.warning(f"Message skipped | {json.dumps(context, ensure_ascii=False)}")
        else:
            logger.info(f"Message attempt | {json.dumps(context, ensure_ascii=False)}")
    
    @staticmethod
    def log_contact_processing(
        contact_name: str,
        total_phones: int,
        status: str = "started"
    ):
        """
        Log start of contact processing.
        
        Args:
            contact_name: Name of the contact
            total_phones: Total phone numbers for this contact
            status: Processing status (started, completed, failed)
        """
        context = {
            "event": "contact_processing",
            "contact_name": contact_name,
            "total_phones": total_phones,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if status == "started":
            logger.info(f"Processing contact | {json.dumps(context, ensure_ascii=False)}")
        elif status == "completed":
            logger.success(f"Contact completed | {json.dumps(context, ensure_ascii=False)}")
        else:
            logger.error(f"Contact failed | {json.dumps(context, ensure_ascii=False)}")
    
    @staticmethod
    def log_session_summary(
        total_contacts: int,
        total_phones_processed: int,
        total_messages_sent: int,
        total_failures: int,
        invalid_phones: int,
        not_found_phones: int,
        duration_seconds: float,
        errors_by_type: Optional[Dict[str, int]] = None
    ):
        """
        Log session summary with metrics.
        
        Args:
            total_contacts: Total contacts processed
            total_phones_processed: Total phone numbers processed
            total_messages_sent: Total messages successfully sent
            total_failures: Total failed attempts
            invalid_phones: Number of invalid phone numbers
            not_found_phones: Number of phones not found on WhatsApp
            duration_seconds: Session duration in seconds
            errors_by_type: Optional dictionary of error types and counts
        """
        total_attempts = total_messages_sent + total_failures
        success_rate = (total_messages_sent / total_attempts * 100) if total_attempts > 0 else 0
        messages_per_minute = (total_messages_sent / duration_seconds * 60) if duration_seconds > 0 else 0
        
        context = {
            "event": "session_summary",
            "total_contacts": total_contacts,
            "total_phones_processed": total_phones_processed,
            "total_messages_sent": total_messages_sent,
            "total_failures": total_failures,
            "invalid_phones": invalid_phones,
            "not_found_phones": not_found_phones,
            "duration_seconds": round(duration_seconds, 2),
            "duration_minutes": round(duration_seconds / 60, 2),
            "success_rate_percent": round(success_rate, 2),
            "messages_per_minute": round(messages_per_minute, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if errors_by_type:
            context["errors_by_type"] = errors_by_type
        
        logger.info(f"Session completed | {json.dumps(context, ensure_ascii=False)}")
    
    @staticmethod
    def log_authentication(status: str, error: Optional[str] = None):
        """
        Log authentication event.
        
        Args:
            status: Authentication status (started, success, failed)
            error: Optional error message
        """
        context = {
            "event": "authentication",
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if error:
            context["error"] = error
        
        if status == "success":
            logger.success(f"Authentication successful | {json.dumps(context, ensure_ascii=False)}")
        elif status == "failed":
            logger.error(f"Authentication failed | {json.dumps(context, ensure_ascii=False)}")
        else:
            logger.info(f"Authentication {status} | {json.dumps(context, ensure_ascii=False)}")
    
    @staticmethod
    def log_database_operation(
        operation: str,
        status: str,
        record_count: Optional[int] = None,
        error: Optional[str] = None
    ):
        """
        Log database operation.
        
        Args:
            operation: Operation type (save, update, delete, query)
            status: Operation status (success, failed)
            record_count: Optional number of records affected
            error: Optional error message
        """
        context = {
            "event": "database_operation",
            "operation": operation,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if record_count is not None:
            context["record_count"] = record_count
        
        if error:
            context["error"] = error
        
        if status == "success":
            logger.debug(f"Database operation | {json.dumps(context, ensure_ascii=False)}")
        else:
            logger.error(f"Database operation failed | {json.dumps(context, ensure_ascii=False)}")
