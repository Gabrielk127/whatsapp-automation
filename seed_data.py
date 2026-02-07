import os
import random
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

# Load env
load_dotenv()

# Use DATABASE_URL to match app config
MONGO_URI = os.getenv("DATABASE_URL") or os.getenv("MONGO_URI") or "mongodb://localhost:27017/whatsapp_db"

def seed_data():
    try:
        print(f"🔌 Connecting to: {MONGO_URI.split('@')[-1] if '@' in MONGO_URI else MONGO_URI}")
        client = MongoClient(MONGO_URI)
        
        # Parse DB name from URI like the app does
        try:
            db_name = MONGO_URI.split("/")[-1].split("?")[0]
        except:
            db_name = "whatsapp_db"
            
        if not db_name:
            db_name = "whatsapp_db"
            
        print(f"📂 Target Database: {db_name}")
        db = client[db_name]
        
        print("🗑️  Cleaning old data...")
        db.whatsapp_automation.delete_many({})
        db.session_metadata.delete_many({})
        db.logs.delete_many({})
        
        print("🌱 Generating mock data...")
        
        contacts = []
        condominios = ["Residencial Flores", "Edifício Horizonte", "Vila Verde", "Solar do Parque"]
        
        # Generate 500 contacts over the last 7 days
        base_time = datetime.now(timezone.utc) - timedelta(days=7)
        
        current_time = base_time
        for i in range(500):
            # Time progression: spread over ~7 days (~20 mins avg gap)
            current_time += timedelta(minutes=random.randint(5, 30))
            timestamp = current_time
            
            # Random attributes
            condominio = random.choice(condominios)
            phones_total = random.randint(1, 4)
            phones_valid = phones_total - random.choice([0, 0, 1]) # Mostly valid
            
            # Status logic
            rand = random.random()
            if rand > 0.8:
                status = "ERROR"
                phones_found = 0
                phones_sent = 0
                error = "Invalid Number"
            elif rand > 0.6:
                status = "PARTIAL"
                phones_found = 2
                phones_sent = 1
                error = None
            else:
                status = "SUCCESS"
                phones_found = phones_valid
                phones_sent = phones_valid
                error = None
                
            contact = {
                "name": f"Contact {i+1}",
                "status": status,
                "phones_found": phones_found,
                "phones_sent": phones_sent,
                "phones": [f"551199999{k:04d}" for k in range(phones_sent)],
                "phones_total": phones_total,
                "phones_valid": phones_valid,
                "condominio": condominio,
                "error": error,
                "timestamp": timestamp
            }
            contacts.append(contact)
            
        if contacts:
            db.whatsapp_automation.insert_many(contacts)
            print(f"✅ Inserted {len(contacts)} contacts.")
        
        # Initialize session metadata for ETA
        db.session_metadata.update_one(
            {"_id": "current_session"},
            {"$set": {
                "total_rows": 1000,  # Simulate bigger file
                "start_time": base_time,
                "status": "RUNNING",
                "last_update": datetime.now(timezone.utc)
            }},
            upsert=True
        )
        print("✅ Session metadata initialized.")
        
        print("📝 Generating mock logs...")
        logs = []
        log_templates = [
            ("SUCCESS", "Mensagem enviada com sucesso para {name}"),
            ("PARTIAL", "Enviado parcialmente para {name} (1 de 2 números)"),
            ("ERROR", "Erro ao processar {name}: Número inválido"),
            ("INFO", "Iniciando processamento do condomínio {condominio}"),
            ("WARNING", "Conexão instável detectada, tentando novamente...")
        ]
        
        for i in range(20):
            # Logs for the last 30 minutes
            log_time = datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30))
            level, template = random.choice(log_templates)
            message = template.format(
                name=f"Contato {random.randint(1, 500)}",
                condominio=random.choice(condominios)
            )
            logs.append({
                "timestamp": log_time,
                "level": level,
                "message": message,
                "context": {}
            })
            
        if logs:
            db.logs.insert_many(logs)
            print(f"✅ Inserted {len(logs)} logs.")

        print("🚀 Dashboard ready! Refresh the page.")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")

if __name__ == "__main__":
    seed_data()
