"""WhatsApp module configuration."""
import os

# Absolute path to session file
STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'state.json'))

# Excel file with contacts
EXCEL_FILE = 'contatos.xlsx'

# Message templates
MESSAGE_TEMPLATE_1 = "Olá {name}, tudo bem? Sou a Simone, corretora da imobiliária Armangni."
MESSAGE_TEMPLATE_2 = "Tenho um cliente interessado na compra do seu imóvel no {condominio}!"
MESSAGE_TEMPLATE_3 = "Você tem interesse na venda?"

# Condominium name (fill in here)
CONDOMINIO = "Residencial Example"

# Phone columns in Excel
PHONE_COLUMNS = ['Telefone 1', 'Telefone 2', 'Telefone 3', 'Telefone 4', 'Telefone 5']

# Delays (seconds)
DELAY_MIN = 5
DELAY_MAX = 10
DELAY_BETWEEN_MESSAGES = 5

# User Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
