from playwright.sync_api import sync_playwright
import time
import os

def save_session():
    # Define o caminho absoluto para o arquivo state.json
    state_file = os.path.join(os.path.dirname(__file__), '..', '..', 'state.json')
    state_file = os.path.abspath(state_file)
    
    print(f"Salvando sessão em: {state_file}")
    
    with sync_playwright() as p:
        # Headless=False para você ver o navegador e escanear o QR Code
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("Abriu o navegador. Acesse o WhatsApp Web e escaneie o QR Code.")
        print("Aguardando autenticação...")
        page.goto("https://web.whatsapp.com/")

        # Espera até que a lista de conversas carregue (indicando login sucesso)
        # O seletor #pane-side é a lista lateral de chats
        try:
            page.wait_for_selector("#pane-side", timeout=120000)  # 120 segundos para escanear
            print("✅ Login detectado!")
            time.sleep(3)  # Pequena pausa para garantir que tudo foi carregado
            
            # Salva os cookies, storage, localStorage, sessionStorage
            context.storage_state(path=state_file)
            print(f"✅ Sessão salva em '{state_file}'.")
            print("Você pode fechar o navegador. O arquivo state.json foi criado com sucesso!")
            
        except Exception as e:
            print(f"❌ Tempo esgotado ou erro ao detectar login: {e}")
            print("Certifique-se de que escaneou o QR Code corretamente.")

        browser.close()

if __name__ == "__main__":
    save_session()
