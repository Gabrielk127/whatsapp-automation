import pandas as pd
from playwright.sync_api import sync_playwright
import urllib.parse
import time
import random
import re
import os

# --- CONFIGURAÇÕES ---
ARQUIVO_EXCEL = 'contatos.xlsx'
MENSAGEM_BASE = "Olá {nome}, tudo bem? Vi seu contato em nossa base."
COLUNAS_TELEFONE = ['Tel1', 'Tel2', 'Tel3', 'Tel4', 'Tel5'] # Ajuste conforme seu Excel
DELAY_MIN = 20  # Segundos (Aumentado)
DELAY_MAX = 45  # Segundos (Aumentado)

# Define o caminho absoluto para o arquivo state.json
STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'state.json'))

def limpar_numero(num):
    """Remove caracteres não numéricos e garante string."""
    if pd.isna(num): return None
    s_num = str(num)
    # Remove tudo que não é dígito
    clean = re.sub(r'\D', '', s_num)
    # Validação básica: precisa ter pelo menos DDD + numero (10 ou 11 digitos)
    # Idealmente deve ter o DDI (55). Se sua base não tem 55, adicione aqui:
    if len(clean) < 10: return None
    if not clean.startswith('55'): 
        clean = '55' + clean
    return clean

def enviar_mensagens():
    # Carregar dados
    try:
        df = pd.read_excel(ARQUIVO_EXCEL)
    except FileNotFoundError:
        print(f"Erro: O arquivo '{ARQUIVO_EXCEL}' não foi encontrado.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        # Tenta carregar a sessão existente
        context = None
        if os.path.exists(STATE_FILE):
            print(f"✅ Arquivo state.json encontrado: {STATE_FILE}")
            file_size = os.path.getsize(STATE_FILE)
            print(f"   Tamanho: {file_size} bytes")
            
            try:
                print("   Tentando carregar sessão...")
                context = browser.new_context(storage_state=STATE_FILE)
                print("   ✅ Sessão carregada!")
            except Exception as e:
                print(f"   ❌ Erro ao carregar sessão: {e}")
                print("   Criando nova sessão...")
                context = None
        
        # Se não conseguiu carregar, cria uma nova
        if context is None:
            print("🔄 Criando nova sessão...")
            context = browser.new_context()
        
        page = context.new_page()
        
        # User Agent para evitar detecção simples
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        })

        print("Acessando WhatsApp Web...")
        page.goto("https://web.whatsapp.com/")
        
        # Aguarda a lista de chats carregar OU espera que o usuário escaneie o QR
        try:
            print("⏳ Aguardando autenticação (máximo 2 minutos para escanear QR Code)...")
            page.wait_for_selector("#pane-side", timeout=120000)
            print("✅ WhatsApp carregado e autenticado!")
            time.sleep(5)  # Aguarda um pouco para garantir que tudo foi carregado
            
            # Salva a sessão com debug detalhado
            print(f"\n📝 Salvando sessão...")
            try:
                # Garante que o diretório existe
                os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
                
                # Salva o estado do contexto
                context.storage_state(path=STATE_FILE)
                
                # Verifica se o arquivo foi criado
                time.sleep(1)  # Aguarda um pouco para garantir que foi escrito em disco
                if os.path.exists(STATE_FILE):
                    file_size = os.path.getsize(STATE_FILE)
                    print(f"✅ Sessão salva com sucesso! ({file_size} bytes)")
                    print(f"   Arquivo: {STATE_FILE}")
                else:
                    print(f"❌ Erro: Arquivo não foi criado em {STATE_FILE}")
                    
            except Exception as e:
                print(f"❌ Erro ao salvar sessão: {e}")
                print(f"   Tipo de erro: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"❌ Erro ao conectar ao WhatsApp: {e}")
            browser.close()
            return
        
        # User Agent para evitar detecção simples
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        })

        print("Carregando WhatsApp...")
        try:
            page.goto("https://web.whatsapp.com/")
            page.wait_for_selector("#pane-side", timeout=40000)
            print("WhatsApp carregado. Iniciando disparos...")
        except Exception as e:
            print(f"Erro ao carregar WhatsApp: {e}")
            browser.close()
            return

        total_enviados = 0

        for count, (index, row) in enumerate(df.iterrows(), 1):
            nome = row['Nome'] if not pd.isna(row['Nome']) else "Cliente"
            
            # Itera sobre as colunas de telefone definidas
            for col_tel in COLUNAS_TELEFONE:
                if col_tel not in df.columns: continue
                
                telefone_bruto = row[col_tel]
                telefone = limpar_numero(telefone_bruto)
                
                if not telefone: continue

                try:
                    mensagem = MENSAGEM_BASE.format(nome=nome)
                    msg_encoded = urllib.parse.quote(mensagem)
                    
                    # URL Injection
                    link = f"https://web.whatsapp.com/send?phone={telefone}&text={msg_encoded}"
                    print(f"[{count}] Processando {nome} - {telefone}...")
                    
                    page.goto(link)

                    # --- Lógica de Decisão (Race Condition) ---
                    # Seletores ESPECÍFICOS para o campo de MENSAGEM (não de pesquisa)
                    # Vamos usar os seletores mais específicos primeiro
                    seletor_input = 'div[data-lexical-editor="true"][aria-label*="Digitar"]'
                    seletor_input_alt = 'div[data-lexical-editor="true"]'
                    seletor_input_fallback = 'div[aria-placeholder="Digite uma mensagem"]'
                    seletor_erro = 'div[data-animate-modal-popup="true"]'
                    
                    try:
                        # Aguarda a página carregar o chat ou o erro
                        page.wait_for_load_state("networkidle")
                        
                        # Tenta encontrar o campo de mensagem com seletores cada vez menos específicos
                        input_box = None
                        
                        try:
                            input_box = page.wait_for_selector(seletor_input, timeout=10000)
                        except:
                            pass
                        
                        if not input_box:
                            try:
                                input_box = page.wait_for_selector(seletor_input_alt, timeout=10000)
                            except:
                                pass
                        
                        if not input_box:
                            try:
                                input_box = page.wait_for_selector(seletor_input_fallback, timeout=10000)
                            except:
                                pass
                        
                        if input_box:
                            # Verifica se encontrou o elemento certo (da conversa, não da pesquisa)
                            aria_label = input_box.get_attribute("aria-label") or ""
                            print(f"   🔎 Elemento encontrado - aria-label: '{aria_label}'")
                            
                            # Se achou o campo, vamos garantir que o texto está lá
                            print("   ⏳ Aguardando processamento do texto...")
                            time.sleep(3)
                            
                            # Verifica se tem texto no campo (da URL)
                            text_content = input_box.text_content()
                            print(f"   📝 Conteúdo do campo (URL): '{text_content}'")
                            
                            # Se o campo está vazio, digita manualmente
                            if not text_content or text_content.strip() == "":
                                print(f"   ⌨️ Campo vazio - digitando mensagem manualmente...")
                                
                                # Garante que o campo está focado e clica múltiplas vezes
                                input_box.click()
                                time.sleep(0.3)
                                input_box.click()
                                time.sleep(0.3)
                                input_box.focus()
                                time.sleep(0.5)
                                
                                # Digita a mensagem
                                page.keyboard.type(mensagem)
                                time.sleep(2)
                                
                                print(f"   ✍️ Mensagem digitada: '{mensagem}'")
                            else:
                                print(f"   ✅ Texto já está no campo (via URL)")
                            
                            # Agora envia pressionando Enter
                            print("   🔍 Enviando mensagem...")
                            input_box.focus()
                            time.sleep(0.5)
                            page.keyboard.press("Enter")
                            print(f"   ⏸️ Aguardando confirmação de envio...")
                            time.sleep(2)
                            
                            # Verifica se o campo ficou vazio (indicativo de que foi enviado)
                            text_after = input_box.text_content()
                            if text_after is None:
                                text_after = ""
                                
                            if text_after == "" or text_after.strip() == "":
                                print(f"   ✅ Mensagem enviada para {telefone}")
                                total_enviados += 1
                            else:
                                print(f"   ⚠️ Campo ainda tem texto: '{text_after}' - Tentando novamente...")
                                # Seleciona tudo e apaga
                                page.keyboard.press("Control+A")
                                time.sleep(0.2)
                                page.keyboard.press("Delete")
                                time.sleep(1)
                        else:
                            print(f"   ❌ Não foi encontrado campo de mensagem")
                        
                        # --- DELAY DE SEGURANÇA ---
                        tempo_espera = random.randint(DELAY_MIN, DELAY_MAX)
                        print(f"   💤 Aguardando {tempo_espera}s...")
                        time.sleep(tempo_espera)

                    except Exception as e_wait:
                        print(f"   ⚠️ Erro ao processar chat: {e_wait}")

                except Exception as e:
                    print(f"   ❌ Erro crítico no envio: {e}")

        print(f"\nFim do processamento. Total enviados: {total_enviados}")
        browser.close()

if __name__ == "__main__":
    enviar_mensagens()
