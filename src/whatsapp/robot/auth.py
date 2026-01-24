"""Script de autenticação do WhatsApp Web."""
from playwright.sync_api import sync_playwright
import time
from loguru import logger
from ..config import STATE_FILE


def save_session():
    """
    Faz login no WhatsApp Web e salva a sessão (cookies + storage).
    
    Exibe o QR Code no navegador. O usuário deve escanear com seu telefone.
    Após o login, o arquivo state.json é criado automaticamente.
    """
    logger.info(f"Salvando sessão em: {STATE_FILE}")
    
    with sync_playwright() as p:
        # Headless=False para você ver o navegador e escanear o QR Code
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        logger.info("Abriu o navegador. Acesse o WhatsApp Web e escaneie o QR Code.")
        logger.info("Aguardando autenticação...")
        page.goto("https://web.whatsapp.com/")

        # Espera até que a lista de conversas carregue (indicando login sucesso)
        # O seletor #pane-side é a lista lateral de chats
        try:
            page.wait_for_selector("#pane-side", timeout=120000)  # 120 segundos para escanear
            logger.success("✅ Login detectado!")
            time.sleep(3)  # Pequena pausa para garantir que tudo foi carregado
            
            # Salva os cookies, storage, localStorage, sessionStorage
            context.storage_state(path=STATE_FILE)
            logger.success(f"✅ Sessão salva em '{STATE_FILE}'.")
            logger.info("Você pode fechar o navegador. O arquivo state.json foi criado com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Tempo esgotado ou erro ao detectar login: {e}")
            logger.warning("Certifique-se de que escaneou o QR Code corretamente.")

        browser.close()


if __name__ == "__main__":
    save_session()
