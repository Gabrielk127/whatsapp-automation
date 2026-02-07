"""Log management utilities for rotation, cleanup, and analysis."""

import os
import json
import csv
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from loguru import logger


class LogManager:
    """Manages log files with rotation, cleanup, and export capabilities."""
    
    def __init__(self, log_dir: str = "logs", max_age_days: int = 30):
        """
        Initialize log manager.
        
        Args:
            log_dir: Directory where logs are stored
            max_age_days: Maximum age of logs to keep (older logs are deleted)
        """
        self.log_dir = Path(log_dir)
        self.max_age_days = max_age_days
        self.log_dir.mkdir(exist_ok=True)
    
    def rotate_logs(self, max_size_mb: int = 10):
        """
        Rotate log files if they exceed max size.
        
        Args:
            max_size_mb: Maximum size in MB before rotation
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        
        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_size > max_size_bytes:
                # Create rotated filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                rotated_name = f"{log_file.stem}_{timestamp}.log.gz"
                rotated_path = self.log_dir / rotated_name
                
                # Compress and rotate
                with open(log_file, 'rb') as f_in:
                    with gzip.open(rotated_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Clear original file
                log_file.write_text("")
                
                logger.info(f"📦 Rotated log: {log_file.name} → {rotated_name}")
    
    def cleanup_old_logs(self):
        """Delete log files older than max_age_days."""
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        deleted_count = 0
        
        for log_file in self.log_dir.glob("*.log*"):
            # Get file modification time
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            if file_time < cutoff_date:
                log_file.unlink()
                deleted_count += 1
                logger.debug(f"🗑️ Deleted old log: {log_file.name}")
        
        if deleted_count > 0:
            logger.info(f"🧹 Cleaned up {deleted_count} old log files")
    
    def parse_structured_logs(self, log_file: str) -> List[Dict[str, Any]]:
        """
        Parse structured JSON logs from log file.
        
        Args:
            log_file: Path to log file
            
        Returns:
            List of parsed log entries
        """
        log_path = self.log_dir / log_file
        
        if not log_path.exists():
            logger.warning(f"Log file not found: {log_file}")
            return []
        
        structured_logs = []
        
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Try to extract JSON from log line
                if '|' in line:
                    try:
                        # Split on first | to get JSON part
                        json_part = line.split('|', 1)[1].strip()
                        log_data = json.loads(json_part)
                        structured_logs.append(log_data)
                    except (json.JSONDecodeError, IndexError):
                        continue
        
        return structured_logs
    
    def filter_logs(
        self,
        log_file: str,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter structured logs by criteria.
        
        Args:
            log_file: Path to log file
            event_type: Filter by event type (e.g., 'message_attempt')
            status: Filter by status (e.g., 'success', 'failed')
            start_time: Filter logs after this time
            end_time: Filter logs before this time
            
        Returns:
            Filtered list of log entries
        """
        logs = self.parse_structured_logs(log_file)
        filtered = logs
        
        if event_type:
            filtered = [log for log in filtered if log.get('event') == event_type]
        
        if status:
            filtered = [log for log in filtered if log.get('status') == status]
        
        if start_time:
            filtered = [
                log for log in filtered
                if datetime.fromisoformat(log.get('timestamp', '')) >= start_time
            ]
        
        if end_time:
            filtered = [
                log for log in filtered
                if datetime.fromisoformat(log.get('timestamp', '')) <= end_time
            ]
        
        return filtered
    
    def export_logs_json(self, log_file: str, output_file: str, **filters):
        """
        Export filtered logs to JSON file.
        
        Args:
            log_file: Source log file
            output_file: Output JSON file path
            **filters: Filter criteria (event_type, status, etc.)
        """
        logs = self.filter_logs(log_file, **filters)
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Exported {len(logs)} logs to {output_file}")
    
    def export_logs_csv(self, log_file: str, output_file: str, **filters):
        """
        Export filtered logs to CSV file.
        
        Args:
            log_file: Source log file
            output_file: Output CSV file path
            **filters: Filter criteria (event_type, status, etc.)
        """
        logs = self.filter_logs(log_file, **filters)
        
        if not logs:
            logger.warning("No logs to export")
            return
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get all unique keys from logs
        all_keys = set()
        for log in logs:
            all_keys.update(log.keys())
        
        fieldnames = sorted(all_keys)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(logs)
        
        logger.info(f"📊 Exported {len(logs)} logs to {output_file}")
    
    def get_log_statistics(self, log_file: str) -> Dict[str, Any]:
        """
        Get statistics from structured logs.
        
        Args:
            log_file: Path to log file
            
        Returns:
            Dictionary with log statistics
        """
        logs = self.parse_structured_logs(log_file)
        
        if not logs:
            return {}
        
        # Count by event type
        events_count = {}
        for log in logs:
            event = log.get('event', 'unknown')
            events_count[event] = events_count.get(event, 0) + 1
        
        # Count by status
        status_count = {}
        for log in logs:
            status = log.get('status')
            if status:
                status_count[status] = status_count.get(status, 0) + 1
        
        # Get time range
        timestamps = [
            datetime.fromisoformat(log.get('timestamp', ''))
            for log in logs if log.get('timestamp')
        ]
        
        time_range = None
        if timestamps:
            time_range = {
                'start': min(timestamps).isoformat(),
                'end': max(timestamps).isoformat()
            }
        
        return {
            'total_logs': len(logs),
            'events_count': events_count,
            'status_count': status_count,
            'time_range': time_range
        }
    
    def aggregate_session_summaries(self, log_file: str) -> List[Dict[str, Any]]:
        """
        Extract all session summaries from logs.
        
        Args:
            log_file: Path to log file
            
        Returns:
            List of session summary entries
        """
        return self.filter_logs(log_file, event_type='session_summary')
