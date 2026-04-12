"""Firebase connection configuration using firebase-admin."""
import os
import firebase_admin
from firebase_admin import credentials, firestore
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Firebase:
    """Firebase connection manager."""
    
    _instance = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self) -> bool:
        """
        Initialize Firebase Admin SDK.
        """
        if self._db is not None:
            return True
            
        try:
            # Opção 1: Variáveis de ambiente individuais (Melhor para Vercel/Produção)
            project_id = os.getenv("FIREBASE_PROJECT_ID")
            private_key = os.getenv("FIREBASE_PRIVATE_KEY")
            client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
            
            if project_id and private_key and client_email:
                logger.info("🔐 Inicializando Firebase via variáveis de ambiente...")
                # Corrige quebras de linha na chave privada se necessário
                private_key = private_key.replace("\\n", "\n")
                
                cred = credentials.Certificate({
                    "type": "service_account",
                    "project_id": project_id,
                    "private_key": private_key,
                    "client_email": client_email,
                    "token_uri": "https://oauth2.googleapis.com/token",
                })
            else:
                # Opção 2: Arquivo JSON (Local)
                key_path = os.getenv("FIREBASE_KEY_PATH", "firebase-key.json")
                if not os.path.isabs(key_path):
                    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                    key_path = os.path.join(project_root, key_path)
                
                if not os.path.exists(key_path):
                    # Tenta encontrar o arquivo que o usuário enviou se o padrão não existir
                    possible_file = "whatsapp-automation-leads-firebase-adminsdk-fbsvc-a9685c1a6c - cópia.json"
                    key_path = os.path.join(os.path.dirname(key_path), possible_file)
                
                if not os.path.exists(key_path):
                    logger.error("❌ Credenciais do Firebase não encontradas no .env nem no arquivo JSON")
                    return False
                
                logger.info(f"📂 Inicializando Firebase via arquivo: {os.path.basename(key_path)}")
                cred = credentials.Certificate(key_path)

            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            
            self._db = firestore.client()
            logger.success(f"✅ Conectado ao Firebase Firestore: {firebase_admin.get_app().project_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao Firebase: {e}")
            return False
            
    @property
    def db(self):
        """Get Firestore client instance."""
        if self._db is None:
            self.connect()
        return self._db
        
    def is_connected(self) -> bool:
        """Check if connected to Firebase."""
        return self._db is not None

# Global instance
firebase = Firebase()
