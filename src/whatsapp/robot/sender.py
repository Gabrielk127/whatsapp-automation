"""Mass message sending script via Evolution API."""
import os
import time
import random
import pandas as pd
import requests
from datetime import datetime
from loguru import logger

from ..config import (
    EXCEL_FILE, MESSAGE_TEMPLATE_1, MESSAGE_TEMPLATE_2, MESSAGE_TEMPLATE_3,
    PHONE_COLUMNS, DELAY_MIN, DELAY_MAX, DELAY_BETWEEN_MESSAGES, CONDOMINIO,
    MAX_CONTACTS_PER_SESSION
)
from ..utils import clean_phone_number, format_name, is_mobile_phone
from ...repositories.firebase_repository import firebase_repo
from ...utils.metrics import SessionMetrics

class EvolutionSender:
    def __init__(self):
        self.api_url = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
        self.api_key = os.getenv("EVOLUTION_API_KEY")
        self.instance_name = os.getenv("EVOLUTION_INSTANCE_NAME")
        
        # O cabeçalho obrigatório da Evolution API
        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    def check_instance(self) -> bool:
        """
        Verifica se a instância está conectada e pronta para envio.
        """
        endpoint = f"{self.api_url}/instance/connectionState/{self.instance_name}"
        try:
            response = requests.get(endpoint, headers=self.headers)
            if response.status_code == 200:
                state = response.json().get("instance", {}).get("state")
                return state == "open"
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar instância: {e}")
            return False

    def check_number(self, phone: str) -> bool:
        """
        Verifica se o número existe no WhatsApp antes de tentar enviar.
        """
        endpoint = f"{self.api_url}/chat/whatsappNumbers/{self.instance_name}"
        payload = {"numbers": [phone]}
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            # Aceita 200 ou 201 como sucesso
            if response.status_code in [200, 201]:
                data = response.json()
                return data[0].get("exists", False) if data else False
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar número {phone}: {e}")
            return False

    def send_message(self, phone: str, message: str) -> tuple[bool, dict]:
        """
        Envia uma mensagem de texto usando a Evolution API com simulação de digitação.
        Retorna (sucesso, dados_da_resposta).
        """
        endpoint = f"{self.api_url}/message/sendText/{self.instance_name}"
        
        payload = {
            "number": phone,
            "text": message,
            "delay": 2000,         # Simula tempo de digitação (2 segundos)
            "presence": "composing" # Mostra "Digitando..." durante o delay
        }

        try:
            logger.info(f"Enviando mensagem para {phone} via API...")
            response = requests.post(endpoint, json=payload, headers=self.headers)
            
            # Aceita 200 ou 201 como sucesso no envio/fila
            if response.status_code in [200, 201]:
                return True, response.json()
            else:
                logger.error(f"Erro na API para {phone}: {response.text}")
                return False, {}
                
        except Exception as e:
            logger.error(f"Falha de conexão com a Evolution API: {str(e)}")
            return False, {}

def send_messages():
    """
    Main loop to send messages using Evolution API.
    """
    logger.info("🔌 Connecting to Firebase...")
    db_connected = firebase_repo.connect()
    
    if db_connected:
        logger.success("✅ Firebase connected!")
    else:
        logger.warning("⚠️ Continuing without database...")

    sender = EvolutionSender()
    
    # 🛡️ VERIFICAÇÃO DE SAÚDE DA INSTÂNCIA
    logger.info("🔍 Verificando status da instância...")
    if not sender.check_instance():
        logger.error("❌ Instância não está conectada! Abra o Manager e verifique o QR Code.")
        return

    session_metrics = SessionMetrics()

    # Load "blacklist" of previously successful phones
    successful_phones_set = firebase_repo.get_all_successful_phones() if db_connected else set()
    logger.info(f"🛡️ Loaded {len(successful_phones_set)} previously successful phones from database (Duplicates Check).")

    
    # Load data
    try:
        df = pd.read_excel(EXCEL_FILE)
        logger.info(f"📊 File '{EXCEL_FILE}' loaded. {len(df)} contacts found.")
    except FileNotFoundError:
        logger.error(f"Error: File '{EXCEL_FILE}' not found.")
        return

    # Resume logic from Firebase
    start_index = 0
    if db_connected:
        last_name = firebase_repo.get_last_processed_contact_name()
        if last_name:
            matching_indices = df.index[
                df['Nome'].astype(str).str.strip().str.lower() == str(last_name).strip().lower()
            ].tolist()
            if matching_indices:
                start_index = matching_indices[-1] + 1
                logger.info(f"⏩ Resuming from index {start_index} after '{last_name}'")

    df_remaining = df.iloc[start_index:]
    df_remaining = df_remaining.head(MAX_CONTACTS_PER_SESSION)
    logger.info(f"🚀 Processing {len(df_remaining)} contacts (Limit: {MAX_CONTACTS_PER_SESSION})...")

    # Geração de Batch ID para agrupamento profissional
    now_str = datetime.now().strftime("%Y%m%d_%H%M")
    batch_id = f"BATCH_{CONDOMINIO}_{now_str}"
    logger.info(f"📁 Batch ID da sessão: {batch_id}")

    # Inicializa sessão no Firebase para o Dashboard (Componente Sessão Ativa)
    if db_connected:
        firebase_repo.init_session(
            total_rows=len(df), # Consideramos o total original para a barra de progresso real
            delay_min=DELAY_MIN,
            delay_max=DELAY_MAX,
            delay_between=DELAY_BETWEEN_MESSAGES
        )

    for index, row in df_remaining.iterrows():
        raw_name = row['Nome'] if not pd.isna(row['Nome']) else "Cliente"
        name = format_name(raw_name)
        excel_row = int(index) + 2 # +1 for 0-index, +1 for header row
        
        # Contagem de métricas para o Dashboard
        row_phones_total = 0
        row_phones_found = 0
        all_potential_phones = []

        for col in PHONE_COLUMNS:
            if col in df.columns and not pd.isna(row[col]):
                val = str(row[col]).strip()
                if val:
                    row_phones_total += 1
                    phone = clean_phone_number(val)
                    if phone:
                        all_potential_phones.append(phone)
                        if is_mobile_phone(phone):
                            row_phones_found += 1
        
        phones_to_send_raw = [p for p in all_potential_phones if is_mobile_phone(p)]
        
        # Filtro de Duplicados
        phones_to_send = []
        for p in phones_to_send_raw:
            if p in successful_phones_set:
                logger.info(f"⏩ Pulando {p} - já contatado com sucesso anteriormente.")
            else:
                phones_to_send.append(p)

        # Se havia telefones válidos, mas todos já foram contatados
        if not phones_to_send and len(phones_to_send_raw) > 0:
            logger.warning(f"⏩ {raw_name} ignorado completamente: Todos os telefones já haviam sido contatados antes.")
            if db_connected:
                firebase_repo.save_contact(
                    name=raw_name,
                    status="ALREADY_CONTACTED",
                    phones_found=row_phones_found,
                    phones_sent=0,
                    phones=phones_to_send_raw,
                    condominio=CONDOMINIO,
                    phones_total=row_phones_total,
                    phones_valid=len(phones_to_send_raw),
                    batch_id=batch_id,
                    row_index=excel_row,
                    error="Already contacted"
                )
            continue
        
        # Se não há telefones válidos no Excel (formatos soltos ou em branco)
        if not phones_to_send:
            logger.warning(f"⏩ Skipping {raw_name}: No valid mobile phone found.")
            if db_connected:
                firebase_repo.save_contact(
                    name=raw_name,
                    status="NOT_FOUND",
                    phones_found=row_phones_found,
                    phones_sent=0,
                    phones=all_potential_phones,
                    condominio=CONDOMINIO,
                    phones_total=row_phones_total,
                    phones_valid=0,
                    batch_id=batch_id,
                    row_index=excel_row,
                    error="No valid mobile phone"
                )
            continue

        phones_sent_success = 0
        successful_phones = []
        last_msg_id = None
        whatsapp_found_count = 0
        
        for phone_idx, phone_to_send in enumerate(phones_to_send):
            logger.info(f"🧐 Verificando se {phone_to_send} tem WhatsApp (Telefone {phone_idx+1}/{len(phones_to_send)})...")
            is_valid_on_whatsapp = sender.check_number(phone_to_send)
            
            if not is_valid_on_whatsapp:
                logger.warning(f"❌ {phone_to_send} não está no WhatsApp.")
                continue

            whatsapp_found_count += 1
            
            # Montar mensagens
            msg1 = MESSAGE_TEMPLATE_1.format(name=name)
            msg2 = MESSAGE_TEMPLATE_2.format(name=name, condominio=CONDOMINIO)
            msg3 = MESSAGE_TEMPLATE_3.format(name=name)
            
            logger.info(f"📱 Processing {name} ({phone_to_send})")
            
            success = True
            for msg in [msg1, msg2, msg3]:
                res, response_data = sender.send_message(phone_to_send, msg)
                if res:
                    last_msg_id = response_data.get("key", {}).get("id") or last_msg_id
                else:
                    success = False
                    break
                time.sleep(1)

            if success:
                phones_sent_success += 1
                successful_phones.append(phone_to_send)
                logger.success(f"✅ Success for {name} ({phone_to_send})!")
            else:
                logger.error(f"❌ Error for {name} ({phone_to_send})")
                
            # O SEGREDO CONTRA BANIMENTOS: As pausas
            wait_time = random.randint(DELAY_MIN, DELAY_MAX) if success else DELAY_BETWEEN_MESSAGES
            if phone_idx < len(phones_to_send) - 1 or phones_sent_success > 0:
                logger.info(f"💤 Aguardando {wait_time} segundos para o próximo disparo...")
                time.sleep(wait_time)

        # Após tentar todos os telefones do contato, decidir status final
        if phones_sent_success == 0:
            status = "ERROR" if whatsapp_found_count > 0 else "NOT_FOUND"
            session_metrics.record_failure("api_error")
        elif phones_sent_success < len(phones_to_send):
            status = "PARTIAL"
            session_metrics.record_success() 
        else:
            status = "SUCCESS"
            session_metrics.record_success()

        # Salva no Firebase para a Vercel ler
        if db_connected:
            firebase_repo.save_contact(
                name=raw_name,
                status=status,
                phones_found=row_phones_found,
                phones_sent=phones_sent_success,
                phones=successful_phones if phones_sent_success > 0 else phones_to_send,
                condominio=CONDOMINIO,
                phones_total=row_phones_total,
                phones_valid=len(phones_to_send),
                batch_id=batch_id,
                message_id=last_msg_id,
                row_index=excel_row,
                content=msg1[:100] + "..." if phones_sent_success > 0 else None
            )

    logger.success("🎉 All contacts processed!")

if __name__ == "__main__":
    send_messages()
