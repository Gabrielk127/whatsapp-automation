"""Configurações do módulo WhatsApp."""
import os

# Caminho absoluto para o arquivo de sessão
STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'state.json'))

# Arquivo Excel com contatos
ARQUIVO_EXCEL = 'contatos.xlsx'

# Mensagens padrão
MENSAGEM_BASE = "Olá {nome}, tudo bem? Vi seu contato em nossa base."
MENSAGEM_BASE_2 = "Você tem interesse em saber mais? Posso enviar detalhes!"

# Colunas de telefone no Excel
COLUNAS_TELEFONE = ['Telefone 1', 'Telefone 2', 'Telefone 3', 'Telefone 4', 'Telefone 5']

# Delays (segundos) - AUMENTADOS PARA MELHOR INTERAÇÃO
DELAY_MIN = 45
DELAY_MAX = 75
DELAY_ENTRE_MENSAGENS = 10

# User Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
