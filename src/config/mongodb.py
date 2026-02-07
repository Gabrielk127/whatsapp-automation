"""MongoDB connection configuration using PyMongo."""

import os
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MongoDB:
    """Simple MongoDB connection manager."""
    
    _instance = None
    _client: MongoClient = None
    _db: Database = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self) -> bool:
        """
        Connect to MongoDB.
        
        Returns:
            True if connected successfully, False otherwise.
        """
        if self._client is not None:
            return True
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return False
        
        try:
            self._client = MongoClient(database_url)
            # Test connection
            self._client.admin.command('ping')
            
            # Extract database name from URL
            db_name = database_url.split("/")[-1].split("?")[0]
            self._db = self._client[db_name]
            
            print(f"✅ Connected to MongoDB database: {db_name}")
            return True
        except ConnectionFailure as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Error connecting to MongoDB: {e}")
            return False
    
    @property
    def db(self) -> Database:
        """Get database instance."""
        if self._db is None:
            self.connect()
        return self._db
    
    @property
    def client(self) -> MongoClient:
        """Get client instance."""
        return self._client
    
    def is_connected(self) -> bool:
        """Check if connected to MongoDB."""
        return self._client is not None and self._db is not None
    
    def disconnect(self):
        """Disconnect from MongoDB."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            print("🔌 Disconnected from MongoDB")


# Global instance
mongodb = MongoDB()
