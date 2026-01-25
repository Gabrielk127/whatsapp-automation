"""Script de envio de mensagens em massa via WhatsApp."""
import pandas as pd
from playwright.sync_api import sync_playwright
import urllib.parse
import time
import random
import os
import atexit
import signal
from loguru import logger

from ..config import (
    STATE_FILE, ARQUIVO_EXCEL, MENSAGEM_BASE, MENSAGEM_BASE_2,
    COLUNAS_TELEFONE, DELAY_MIN, DELAY_MAX, DELAY_ENTRE_MENSAGENS, USER_AGENT
)
from ..utils import limpar_numero, formatar_nome

# Variáveis globais para cleanup
_context = None
_browser = None


def _salvar_sessao_e_limpar():
    """
    Fecha o contexto persistente (com launch_persistent_context, a sessão é salva automaticamente).
    
    O contexto persistente do Playwright salva automaticamente:
    - Cookies
    - LocalStorage
    - SessionStorage
    - IndexedDB
    - Service Workers
    
    Tudo é persistido no diretório .whatsapp_profile
    """
    global _context, _browser
    
    if _context:
        try:
            _context.close()
            logger.debug("✅ Contexto persistente fechado (sessão salva automaticamente)")
        except Exception as e:
            logger.debug(f"Erro ao fechar contexto: {e}")
    
    if _browser:
        try:
            _browser.close()
            logger.debug("Navegador fechado")
        except Exception as e:
            logger.debug(f"Erro ao fechar navegador: {e}")


def _handle_interrupt(signum, frame):
    """Handler para Ctrl+C."""
    logger.warning("⏸️  Interrupção detectada. Salvando sessão...")
    _salvar_sessao_e_limpar()
    exit(0)


# Registra o handler para Ctrl+C
signal.signal(signal.SIGINT, _handle_interrupt)
atexit.register(_salvar_sessao_e_limpar)


def enviar_mensagens():
    """
    Envia mensagens em massa via WhatsApp Web.
    
    Lê contatos do arquivo Excel (contatos.xlsx) e envia 2 mensagens para cada um.
    Usa launch_persistent_context para manter a autenticação entre execuções de forma mais confiável.
    
    Estrutura esperada do Excel:
        - Coluna 'Nome': Nome do contato (será formatado)
        - Colunas 'Tel1', 'Tel2', etc: Números de telefone
    """
    # Carregar dados
    try:
        df = pd.read_excel(ARQUIVO_EXCEL)
        logger.info(f"📊 Arquivo '{ARQUIVO_EXCEL}' carregado com sucesso. {len(df)} contatos encontrados.")
    except FileNotFoundError:
        logger.error(f"Erro: O arquivo '{ARQUIVO_EXCEL}' não foi encontrado.")
        return

    with sync_playwright() as p:
        global _browser, _context
        
        # Garante que o diretório de dados existe
        user_data_dir = os.path.join(os.path.dirname(STATE_FILE), '.whatsapp_profile')
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Usa launch_persistent_context para sessão mais confiável
        # Isso cria um perfil de usuário completo similar ao Chrome
        logger.info("🔄 Iniciando navegador com contexto persistente...")
        _context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            locale="pt-BR",
            timezone_id="America/Sao_Paulo"
        )
        
        _browser = None  # launch_persistent_context retorna o contexto, não o browser
        
        logger.success("✅ Contexto persistente criado!")
        page = _context.new_page()
        
        # User Agent
        page.set_extra_http_headers({"User-Agent": USER_AGENT})

        logger.info("🌐 Acessando WhatsApp Web...")
        page.goto("https://web.whatsapp.com/")
        
        # Aguarda a lista de chats carregar OU espera que o usuário escaneie o QR
        try:
            logger.info("⏳ Aguardando autenticação (máximo 2 minutos para escanear QR Code)...")
            page.wait_for_selector("#pane-side", timeout=120000)
            logger.success("✅ WhatsApp carregado e autenticado!")
            time.sleep(5)  # Aguarda um pouco para garantir que tudo foi carregado
            
            # ✅ Com launch_persistent_context, a sessão é salva automaticamente!
            logger.success("✅ Sessão será persistida automaticamente pelo navegador.")
                
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao WhatsApp: {e}")
            _salvar_sessao_e_limpar()
            return
        
        logger.info("Carregando WhatsApp...")
        try:
            page.goto("https://web.whatsapp.com/")
            page.wait_for_selector("#pane-side", timeout=40000)
            logger.success("✅ WhatsApp carregado. Iniciando disparos...")
        except Exception as e:
            logger.error(f"Erro ao carregar WhatsApp: {e}")
            _salvar_sessao_e_limpar()
            return

        total_enviados = 0

        for count, (index, row) in enumerate(df.iterrows(), 1):
            nome_bruto = row['Nome'] if not pd.isna(row['Nome']) else "Cliente"
            # Formata o nome: minúsculo com primeira letra maiúscula e só primeiro nome
            nome = formatar_nome(nome_bruto)
            
            logger.debug(f"DEBUG: Processando linha {count}: {nome_bruto} -> {nome}")
            
            # Itera sobre as colunas de telefone definidas
            for col_tel in COLUNAS_TELEFONE:
                if col_tel not in df.columns: 
                    logger.debug(f"DEBUG: Coluna {col_tel} não existe no Excel")
                    continue
                
                telefone_bruto = row[col_tel]
                logger.debug(f"DEBUG: Telefone bruto de {col_tel}: {telefone_bruto}")
                
                telefone = limpar_numero(telefone_bruto)
                logger.debug(f"DEBUG: Telefone limpo: {telefone}")
                
                if not telefone: 
                    logger.warning(f"⚠️ Telefone inválido para {nome}: {telefone_bruto}")
                    continue

                logger.success(f"✅ Telefone válido: {telefone}")

                # --- ENVIA 2 MENSAGENS POR CONTATO ---
                for num_msg in [1, 2]:
                    if num_msg == 1:
                        mensagem = MENSAGEM_BASE.format(nome=nome)
                        logger.info(f"[{count}] 📱 Processando {nome} - {telefone}... (Mensagem {num_msg}/2)")
                    else:
                        mensagem = MENSAGEM_BASE_2.format(nome=nome) if "{nome}" in MENSAGEM_BASE_2 else MENSAGEM_BASE_2
                        logger.info(f"   → Enviando segunda mensagem...")
                    
                    msg_encoded = urllib.parse.quote(mensagem)
                    
                    # URL Injection
                    link = f"https://web.whatsapp.com/send?phone={telefone}&text={msg_encoded}"
                    
                    # --- Lógica de Decisão (Race Condition) ---
                    # Seletores ESPECÍFICOS para o campo de MENSAGEM (não de pesquisa)
                    seletor_input = 'div[data-lexical-editor="true"][aria-label*="Digitar"]'
                    seletor_input_alt = 'div[data-lexical-editor="true"]'
                    seletor_input_fallback = 'div[aria-placeholder="Digite uma mensagem"]'
                    
                    try:
                        page.goto(link)
                        
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
                                input_box = page.wait_for_selector(seletor_input_fallback, timeout=25000)
                            except:
                                pass
                        
                        if input_box:
                            # Verifica se encontrou o elemento certo (da conversa, não da pesquisa)
                            aria_label = input_box.get_attribute("aria-label") or ""
                            logger.debug(f"   🔎 Elemento encontrado - aria-label: '{aria_label}'")
                            
                            # VALIDAÇÃO: Garante que NÃO é o campo de pesquisa
                            # O campo de pesquisa tem aria-label com "Pesquisar" ou vazio
                            # O campo de mensagem tem aria-label com "Digitar"
                            is_message_field = "digitar" in aria_label.lower()
                            is_search_field = "pesquisar" in aria_label.lower() or "search" in aria_label.lower()
                            
                            if is_search_field:
                                logger.warning(f"   ⚠️ Encontrado CAMPO DE PESQUISA, não de mensagem! Pulando...")
                                raise Exception("Campo de pesquisa detectado, tentando outro seletor")
                            
                            logger.debug(f"   ✅ Validado: É um campo de mensagem")
                            
                            # Se achou o campo, vamos garantir que o texto está lá
                            logger.debug("   ⏳ Aguardando processamento do texto...")
                            time.sleep(8)
                            
                            # Verifica se tem texto no campo (da URL)
                            text_content = input_box.text_content()
                            logger.debug(f"   📝 Conteúdo do campo (URL): '{text_content}'")
                            
                            # Se o campo está vazio, digita manualmente
                            if not text_content or text_content.strip() == "":
                                logger.info(f"   ⌨️ Campo vazio - digitando mensagem manualmente...")
                                
                                # Garante que o campo está focado e clica múltiplas vezes
                                input_box.click()
                                time.sleep(0.3)
                                input_box.click()
                                time.sleep(0.3)
                                input_box.focus()
                                time.sleep(0.5)
                                
                                # Limpa o campo antes de digitar (caso tenha algo)
                                input_box.fill("")
                                time.sleep(0.3)
                                
                                # Digita a mensagem usando fill() que é mais confiável que keyboard.type()
                                input_box.fill(mensagem)
                                time.sleep(5)
                                
                                logger.debug(f"   ✍️ Mensagem digitada via fill()")
                            else:
                                logger.debug(f"   ✅ Texto já está no campo (via URL)")
                            
                            # Agora envia pressionando Enter
                            logger.debug("   🔍 Enviando mensagem...")
                            input_box.focus()
                            time.sleep(1)
                            page.keyboard.press("Enter")
                            logger.debug(f"   ⏸️ Aguardando confirmação de envio...")
                            time.sleep(5)
                            
                            # Verifica se o campo ficou vazio (indicativo de que foi enviado)
                            text_after = input_box.text_content()
                            if text_after is None:
                                text_after = ""
                                
                            if text_after == "" or text_after.strip() == "":
                                logger.success(f"   ✅ Mensagem {num_msg} enviada para {telefone}")
                                total_enviados += 1
                            else:
                                logger.warning(f"   ⚠️ Campo ainda tem texto: '{text_after}' - Tentando novamente...")
                                # Seleciona tudo e apaga
                                page.keyboard.press("Control+A")
                                time.sleep(0.2)
                                page.keyboard.press("Delete")
                                time.sleep(1)
                        else:
                            logger.error(f"   ❌ Não foi encontrado campo de mensagem")
                        
                        # --- DELAY ENTRE MENSAGENS ---
                        if num_msg == 1:  # Se for a primeira mensagem, espera antes da segunda
                            tempo_espera = DELAY_ENTRE_MENSAGENS
                            logger.info(f"   💤 Aguardando {tempo_espera}s antes da 2ª mensagem...")
                            time.sleep(tempo_espera)
                        else:  # Se for a segunda mensagem, faz o delay grande antes do próximo contato
                            tempo_espera = random.randint(DELAY_MIN, DELAY_MAX)
                            logger.info(f"   💤 Aguardando {tempo_espera}s antes do próximo contato...")
                            time.sleep(tempo_espera)

                    except Exception as e_wait:
                        logger.error(f"   ⚠️ Erro ao processar chat: {e_wait}")

        logger.success(f"🎉 Fim do processamento. Total enviados: {total_enviados}")
        
        # Salva a sessão ANTES de fechar
        logger.info("💾 Salvando sessão...")
        try:
            _context.storage_state(path=STATE_FILE)
            time.sleep(1)  # Aguarda a escrita em disco
            
            # Verifica se foi salvo
            if os.path.exists(STATE_FILE) and os.path.getsize(STATE_FILE) > 100:
                logger.success(f"✅ Sessão salva com sucesso!")
            else:
                logger.warning("⚠️ Arquivo pode não ter sido salvo corretamente")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar sessão: {e}")
        
        # Fecha o contexto e navegador
        _salvar_sessao_e_limpar()


if __name__ == "__main__":
    enviar_mensagens()
