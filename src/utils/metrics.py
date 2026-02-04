"""Session metrics tracking for WhatsApp automation."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
from collections import defaultdict


@dataclass
class SessionMetrics:
    """
    Metrics tracker for a sending session.
    
    Tracks all relevant metrics during a WhatsApp message sending session,
    including successes, failures, and error types.
    """
    
    # Session timing
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    # Contact and phone counts
    total_contacts: int = 0
    total_phones_processed: int = 0
    
    # Message counts
    messages_sent: int = 0
    messages_failed: int = 0
    
    # Error counts
    invalid_phones: int = 0
    not_found_phones: int = 0
    
    # Error tracking by type
    errors_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    def record_success(self):
        """Record a successful message send."""
        self.messages_sent += 1
    
    def record_failure(self, error_type: str = "unknown"):
        """
        Record a failed message send.
        
        Args:
            error_type: Type of error that occurred
        """
        self.messages_failed += 1
        self.errors_by_type[error_type] += 1
    
    def record_invalid_phone(self):
        """Record an invalid phone number."""
        self.invalid_phones += 1
    
    def record_not_found(self):
        """Record a phone not found on WhatsApp."""
        self.not_found_phones += 1
    
    def record_contact_processed(self):
        """Record a contact being processed."""
        self.total_contacts += 1
    
    def record_phone_processed(self):
        """Record a phone number being processed."""
        self.total_phones_processed += 1
    
    def finalize(self):
        """Mark session as complete and record end time."""
        self.end_time = datetime.utcnow()
    
    def get_duration_seconds(self) -> float:
        """Get session duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    def get_success_rate(self) -> float:
        """Get success rate as a percentage (0-100)."""
        total_attempts = self.messages_sent + self.messages_failed
        if total_attempts == 0:
            return 0.0
        return (self.messages_sent / total_attempts) * 100
    
    def get_messages_per_minute(self) -> float:
        """Get messages sent per minute."""
        duration = self.get_duration_seconds()
        if duration == 0:
            return 0.0
        return (self.messages_sent / duration) * 60
    
    def get_summary(self) -> Dict:
        """
        Get comprehensive summary of metrics.
        
        Returns:
            Dictionary with all metrics and calculated statistics
        """
        return {
            "duration_seconds": round(self.get_duration_seconds(), 2),
            "duration_minutes": round(self.get_duration_seconds() / 60, 2),
            "total_contacts": self.total_contacts,
            "total_phones_processed": self.total_phones_processed,
            "messages_sent": self.messages_sent,
            "messages_failed": self.messages_failed,
            "invalid_phones": self.invalid_phones,
            "not_found_phones": self.not_found_phones,
            "success_rate_percent": round(self.get_success_rate(), 2),
            "messages_per_minute": round(self.get_messages_per_minute(), 2),
            "errors_by_type": dict(self.errors_by_type),
        }
    
    def __str__(self) -> str:
        """String representation of metrics."""
        summary = self.get_summary()
        return (
            f"SessionMetrics("
            f"duration={summary['duration_minutes']:.1f}min, "
            f"contacts={self.total_contacts}, "
            f"sent={self.messages_sent}, "
            f"failed={self.messages_failed}, "
            f"success_rate={summary['success_rate_percent']:.1f}%"
            f")"
        )
