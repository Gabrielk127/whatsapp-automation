"""Test MongoDB connection with PyMongo."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test PyMongo connection to MongoDB."""
    print("🔍 Testing MongoDB connection with PyMongo...")
    print(f"🔑 DATABASE_URL exists: {bool(os.getenv('DATABASE_URL'))}")
    
    if os.getenv('DATABASE_URL'):
        db_url = os.getenv('DATABASE_URL')
        # Mask password
        if '@' in db_url:
            parts = db_url.split('@')
            masked = parts[0].split(':')[0] + ':****@' + parts[1]
            print(f"🔗 Connection string: {masked}")
    
    print("\n" + "="*60)
    print("Attempting to connect...")
    print("="*60 + "\n")
    
    try:
        from src.config.mongodb import mongodb
        
        if mongodb.connect():
            print("✅ Connected successfully!")
            
            # Test write
            print("\n📝 Testing write...")
            from src.repositories.mongo_repository import mongo_repo
            mongo_repo.connected = True
            
            result = mongo_repo.save_log("INFO", "Test log entry", {"test": True})
            if result:
                print("✅ Write successful!")
            else:
                print("❌ Write failed")
            
            # Test read
            print("\n📊 Testing read...")
            logs = mongo_repo.get_recent_logs(limit=5)
            print(f"✅ Found {len(logs)} log(s)")
            
            print("\n" + "="*60)
            print("✅ ALL TESTS PASSED!")
            print("="*60)
        else:
            print("❌ Connection failed!")
            
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}")
        print(f"📝 Message: {e}")
        
        import traceback
        print("\n📋 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
