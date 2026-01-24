"""Módulo WhatsApp - Automação de envio de mensagens em massa."""
from .robot import save_session, enviar_mensagens
from .config import (
    STATE_FILE, ARQUIVO_EXCEL, MENSAGEM_BASE, MENSAGEM_BASE_2,
    COLUNAS_TELEFONE, DELAY_MIN, DELAY_MAX, DELAY_ENTRE_MENSAGENS
)
from .utils import limpar_numero, formatar_nome

__all__ = [
    'save_session',
    'enviar_mensagens',
    'STATE_FILE',
    'ARQUIVO_EXCEL',
    'MENSAGEM_BASE',
    'MENSAGEM_BASE_2',
    'COLUNAS_TELEFONE',
    'DELAY_MIN',
    'DELAY_MAX',
    'DELAY_ENTRE_MENSAGENS',
    'limpar_numero',
    'formatar_nome',
]
