"""Test script to verify database connectivity and SentMessage operations."""

import asyncio
from src.repositories.message_repository import MessageRepository


async def test_db_connection():
    """Test Prisma connection and SentMessage model."""
    print("🧪 Testing database connection and SentMessage model...\n")
    
    repo = MessageRepository()
    
    try:
        # Test 1: Add a test message
        print("Test 1: Adding a test message to database...")
        result = await repo.add_message(
            name="Test User",
            phone="5511999999999",
            status="TEST"
        )
        print(f"✅ Success! Message saved with ID: {result.id}")
        print(f"   Name: {result.name}")
        print(f"   Phone: {result.phone}")
        print(f"   Status: {result.status}")
        print(f"   Created: {result.created_at if hasattr(result, 'created_at') else result.createdAt if hasattr(result, 'createdAt') else 'N/A'}")
        
        # Test 2: Query all messages
        print("\nTest 2: Querying all messages...")
        await repo.ensure_connected()
        messages = await repo.prisma_client.sentmessage.find_many()
        print(f"✅ Found {len(messages)} message(s) in database")
        for msg in messages:
            print(f"   - {msg.name} ({msg.phone}): {msg.status}")
        
        await repo.close_connection()
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_db_connection())
