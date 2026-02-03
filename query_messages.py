"""Script to query and display all saved messages from the database."""

import asyncio
from src.repositories.message_repository import MessageRepository


async def query_all_messages():
    """Query and display all messages saved in the database."""
    repo = MessageRepository()
    
    try:
        await repo.ensure_connected()
        
        # Get all messages
        messages = await repo.prisma_client.sentmessage.find_many(order={"createdAt": "desc"})
        
        print("\n" + "="*80)
        print("📊 CONTATOS COM MENSAGENS ENVIADAS")
        print("="*80 + "\n")
        
        if not messages:
            print("❌ Nenhuma mensagem encontrada no banco de dados.\n")
            return
        
        total_contacts = len(messages)
        total_phones = sum(len(msg.phones) for msg in messages)
        
        print(f"Total de contatos: {total_contacts}")
        print(f"Total de telefones: {total_phones}\n")
        
        # Display each contact
        for idx, msg in enumerate(messages, 1):
            status_icon = "✅" if msg.status == "SENT" else "⚠️" if "PARTIAL" in msg.status else "❌"
            print(f"{idx}. {status_icon} {msg.name}")
            print(f"   Status: {msg.status}")
            print(f"   Telefones ({len(msg.phones)}):")
            
            for phone in msg.phones:
                print(f"      • {phone}")
            
            print(f"   Criado: {msg.createdAt}")
            print()
        
        # Summary by status
        print("="*80)
        print("📈 RESUMO POR STATUS")
        print("="*80 + "\n")
        
        status_count = {}
        for msg in messages:
            status = msg.status
            status_count[status] = status_count.get(status, 0) + 1
        
        for status in sorted(status_count.keys()):
            count = status_count[status]
            percentage = (count / total_contacts) * 100
            print(f"{status}: {count} contatos ({percentage:.1f}%)")
        
        print("\n" + "="*80 + "\n")
        
        await repo.close_connection()
        
    except Exception as e:
        print(f"❌ Erro: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(query_all_messages())
