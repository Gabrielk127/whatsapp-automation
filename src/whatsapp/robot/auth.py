"""Script de autenticação do WhatsApp Web."""
from playwright.sync_api import sync_playwright
import time
import os
from loguru import logger
from ..config import STATE_FILE


def save_session():
    """
    Faz login no WhatsApp Web e salva a sessão usando contexto persistente.
    
    Exibe o QR Code no navegador. O usuário deve escanear com seu telefone.
    A sessão é persistida automaticamente em um diretório de perfil de usuário.
    """
    logger.info(f"🔐 Iniciando autenticação do WhatsApp Web")
    
    # Cria diretório de perfil persistente
    user_data_dir = os.path.join(os.path.dirname(STATE_FILE), '.whatsapp_profile')
    os.makedirs(user_data_dir, exist_ok=True)
    logger.info(f"📁 Perfil persistente: {user_data_dir}")
    
    with sync_playwright() as p:
        # Usa launch_persistent_context para criar um perfil de usuário persistente
        # Similar ao que o Chrome faz, isso garante melhor persistência de cookies e storage
        logger.info("🌐 Abrindo navegador com contexto persistente...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            locale="pt-BR",
            timezone_id="America/Sao_Paulo"
        )
        
        page = context.new_page()
        
        logger.info("⏳ Navegando para WhatsApp Web...")
        page.goto("https://web.whatsapp.com/")

        # Espera até que a lista de conversas carregue (indicando login sucesso)
        # O seletor #pane-side é a lista lateral de chats
        try:
            logger.info("📲 Escaneie o QR Code com seu telefone (máximo 120 segundos)...")
            page.wait_for_selector("#pane-side", timeout=120000)  # 120 segundos para escanear
            logger.success("✅ Login detectado!")
            
            # Aguarda 5 segundos para garantir que todos os cookies sejam gravados no disco
            logger.info("⏱️  Aguardando 5 segundos para persistência total...")
            time.sleep(5)
            
            logger.success(f"✅ Sessão persistida em '{user_data_dir}'")
            logger.info("✅ Você pode fechar o navegador. A autenticação foi concluída com sucesso!")
            logger.info("💡 Na próxima execução, a sessão será carregada automaticamente.")
            
        except Exception as e:
            logger.error(f"❌ Timeout ou erro ao detectar login: {e}")
            logger.warning("Certifique-se de que:")
            logger.warning("  1. Escaneou o QR Code com seu telefone")
            logger.warning("  2. Aguardou a página carregar completamente")
            logger.warning("  3. Tem conexão com internet estável")

        context.close()


if __name__ == "__main__":
    save_session()
