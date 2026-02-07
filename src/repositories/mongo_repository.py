"""MongoDB Repository for logs and whatsapp automation data."""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from src.config.mongodb import mongodb


class MongoRepository:
    """Repository for MongoDB operations."""
    
    def __init__(self):
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to MongoDB."""
        self.connected = mongodb.connect()
        return self.connected
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.connected and mongodb.is_connected()
    
    # ==================== LOGS COLLECTION ====================
    
    def save_log(self, level: str, message: str, context: Dict[str, Any] = None) -> bool:
        """
        Save a log entry to the 'logs' collection.
        
        Args:
            level: Log level (INFO, ERROR, WARNING, SUCCESS, DEBUG)
            message: Log message
            context: Additional context data
            
        Returns:
            True if saved successfully
        """
        if not self.is_connected():
            return False
        
        try:
            log_entry = {
                "timestamp": datetime.utcnow(),
                "level": level,
                "message": message,
                "context": context or {}
            }
            mongodb.db.logs.insert_one(log_entry)
            return True
        except Exception as e:
            print(f"❌ Error saving log: {e}")
            return False
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent log entries."""
        if not self.is_connected():
            return []
        
        try:
            logs = list(mongodb.db.logs.find().sort("timestamp", -1).limit(limit))
            # Convert ObjectId to string for JSON serialization
            for log in logs:
                log["_id"] = str(log["_id"])
            return logs
        except Exception as e:
            print(f"❌ Error fetching logs: {e}")
            return []
    
    # ==================== WHATSAPP AUTOMATION COLLECTION ====================
    
    def save_contact(
        self,
        name: str,
        status: str,
        phones_found: int,  # This is "Mobile Phones"
        phones_sent: int,
        phones: List[str],
        condominio: str = None,
        phones_total: int = 0,  # Raw count from Excel
        phones_valid: int = 0,  # Valid format (inc. landlines)
        error: str = None
    ) -> bool:
        """
        Save contact automation result to 'whatsapp_automation' collection.
        """
        if not self.is_connected():
            return False
        
        try:
            contact_entry = {
                "name": name,
                "status": status,
                "phones_found": phones_found,  # Mobile
                "phones_sent": phones_sent,
                "phones": phones,
                "phones_total": phones_total,
                "phones_valid": phones_valid,
                "condominio": condominio,
                "error": error,
                "timestamp": datetime.utcnow()
            }
            mongodb.db.whatsapp_automation.insert_one(contact_entry)
            return True
        except Exception as e:
            print(f"❌ Error saving contact: {e}")
            return False
    
    def get_recent_contacts(self, limit: int = 50) -> List[Dict]:
        """Get recent contact automation results."""
        if not self.is_connected():
            return []
        
        try:
            contacts = list(
                mongodb.db.whatsapp_automation.find()
                .sort("timestamp", -1)
                .limit(limit)
            )
            for contact in contacts:
                contact["_id"] = str(contact["_id"])
            return contacts
        except Exception as e:
            print(f"❌ Error fetching contacts: {e}")
            return []
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for the current session."""
        if not self.is_connected():
            return {}
        
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_contacts": {"$sum": 1},
                        "total_phones_found": {"$sum": "$phones_found"},
                        "total_phones_sent": {"$sum": "$phones_sent"},
                        "success_count": {
                            "$sum": {"$cond": [{"$eq": ["$status", "SUCCESS"]}, 1, 0]}
                        },
                        "error_count": {
                            "$sum": {"$cond": [{"$eq": ["$status", "ERROR"]}, 1, 0]}
                        },
                        "partial_count": {
                            "$sum": {"$cond": [{"$eq": ["$status", "PARTIAL"]}, 1, 0]}
                        }
                    }
                }
            ]
            result = list(mongodb.db.whatsapp_automation.aggregate(pipeline))
            if result:
                stats = result[0]
                del stats["_id"]
                return stats
            return {}
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}
    
    def get_stats_by_condominio(self) -> List[Dict]:
        """Get statistics grouped by condominium for comparison."""
        if not self.is_connected():
            return []
        
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$condominio",
                        "total_contacts": {"$sum": 1},
                        "phones_found": {"$sum": "$phones_found"},
                        "phones_sent": {"$sum": "$phones_sent"},
                        "success_count": {
                            "$sum": {"$cond": [{"$eq": ["$status", "SUCCESS"]}, 1, 0]}
                        },
                        "error_count": {
                            "$sum": {"$cond": [{"$eq": ["$status", "ERROR"]}, 1, 0]}
                        },
                        "partial_count": {
                            "$sum": {"$cond": [{"$eq": ["$status", "PARTIAL"]}, 1, 0]}
                        }
                    }
                },
                {"$sort": {"total_contacts": -1}},
                {"$limit": 100}
            ]
            result = list(mongodb.db.whatsapp_automation.aggregate(pipeline))
            # Format result
            stats = []
            for r in result:
                condominio = r["_id"] or "Unknown"
                phones_found = r["phones_found"] or 0
                phones_sent = r["phones_sent"] or 0
                success_rate = (phones_sent / phones_found * 100) if phones_found > 0 else 0
                stats.append({
                    "condominio": condominio,
                    "total_contacts": r["total_contacts"],
                    "phones_found": phones_found,
                    "phones_sent": phones_sent,
                    "success_rate": round(success_rate, 1),
                    "success_count": r["success_count"],
                    "partial_count": r["partial_count"],
                    "error_count": r["error_count"]
                })
            return stats
        except Exception as e:
            print(f"❌ Error getting stats by condominio: {e}")
            return []
    
    def get_funnel_stats(self) -> Dict[str, int]:
        """Get funnel statistics (Phones processed -> Valid -> Mobile -> Sent)."""
        if not self.is_connected():
            return {}
        
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_imported": {"$sum": "$phones_total"},  # Raw phones in excel
                        "valid_phones": {"$sum": "$phones_valid"},    # Parsed ok
                        "mobile_phones": {"$sum": "$phones_found"},   # Is mobile
                        "start_sent": {"$sum": "$phones_found"},      # Attempted (same as mobile for now)
                        "phones_sent": {"$sum": "$phones_sent"}       # Delivered
                    }
                }
            ]
            result = list(mongodb.db.whatsapp_automation.aggregate(pipeline))
            if result:
                stats = result[0]
                del stats["_id"]
                return stats
            return {
                "total_imported": 0,
                "valid_phones": 0,
                "mobile_phones": 0,
                "phones_sent": 0
            }
        except Exception as e:
            print(f"❌ Error getting funnel stats: {e}")
            return {}
            
    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Get daily message stats for the last N days."""
        if not self.is_connected():
            return []
        
        try:
            # Calculate start date
            start_date = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d", 
                                "date": "$timestamp"
                            }
                        },
                        "count": {"$sum": "$phones_sent"}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            result = list(mongodb.db.whatsapp_automation.aggregate(pipeline))
            
            # Format result
            stats = []
            for r in result:
                stats.append({
                    "date": r["_id"],
                    "count": r["count"]
                })
            return stats
            
        except Exception as e:
            print(f"❌ Error getting daily stats: {e}")
            return []

    # ==================== REAL-TIME SESSION METADATA ====================

    def init_session(self, total_rows: int) -> bool:
        """Initialize session metadata with total rows to process."""
        if not self.is_connected():
            return False
        
        try:
            # Upsert current session metadata
            mongodb.db.session_metadata.update_one(
                {"_id": "current_session"},
                {"$set": {
                    "total_rows": total_rows,
                    "start_time": datetime.utcnow(),
                    "status": "RUNNING",
                    "last_update": datetime.utcnow()
                }},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"❌ Error initializing session: {e}")
            return False

    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Calculate real-time speed and ETA."""
        if not self.is_connected():
            return {}
        
        try:
            # Get total target
            metadata = mongodb.db.session_metadata.find_one({"_id": "current_session"})
            if not metadata:
                return {}
            
            total_rows = metadata.get("total_rows", 0)
            
            # Get processed count
            processed_count = mongodb.db.whatsapp_automation.count_documents({})
            
            # Calculate speed (based on last 10 minutes)
            ten_mins_ago = datetime.utcnow() - multiprocessing.timedelta(minutes=10)
            recent_count = mongodb.db.whatsapp_automation.count_documents({
                "timestamp": {"$gte": ten_mins_ago}
            })
            
            # Speed logic
            # If we have recent data, calculate rate
            contacts_per_minute = 0
            if recent_count > 0:
                # Get time range of recent docs
                newest = list(mongodb.db.whatsapp_automation.find().sort("timestamp", -1).limit(1))
                oldest_recent = list(mongodb.db.whatsapp_automation.find({"timestamp": {"$gte": ten_mins_ago}}).sort("timestamp", 1).limit(1))
                
                if newest and oldest_recent:
                    time_diff = (newest[0]["timestamp"] - oldest_recent[0]["timestamp"]).total_seconds()
                    if time_diff > 0:
                        contacts_per_minute = (recent_count / time_diff) * 60
            
            # Calculate ETA
            remaining = max(0, total_rows - processed_count)
            eta_seconds = 0
            if contacts_per_minute > 0:
                eta_seconds = (remaining / contacts_per_minute) * 60
            
            return {
                "contacts_per_minute": round(contacts_per_minute, 1),
                "remaining": remaining,
                "total": total_rows,
                "processed": processed_count,
                "eta_seconds": int(eta_seconds)
            }
            
        except Exception as e:
            print(f"❌ Error getting realtime metrics: {e}")
            return {}


# Global instance
mongo_repo = MongoRepository()
