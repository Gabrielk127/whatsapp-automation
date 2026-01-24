"""Módulo robot - Scripts de automação do WhatsApp."""
from .auth import save_session
from .sender import enviar_mensagens

__all__ = ['save_session', 'enviar_mensagens']
