"""WhatsApp Module - Mass message sending automation."""
from .robot import save_session, send_messages
from .config import (
    STATE_FILE, EXCEL_FILE, MESSAGE_TEMPLATE_1, MESSAGE_TEMPLATE_2, MESSAGE_TEMPLATE_3,
    PHONE_COLUMNS, DELAY_MIN, DELAY_MAX, DELAY_BETWEEN_MESSAGES, CONDOMINIO
)
from .utils import clean_phone_number, format_name

__all__ = [
    'save_session',
    'send_messages',
    'STATE_FILE',
    'EXCEL_FILE',
    'MESSAGE_TEMPLATE_1',
    'MESSAGE_TEMPLATE_2',
    'MESSAGE_TEMPLATE_3',
    'CONDOMINIO',
    'PHONE_COLUMNS',
    'DELAY_MIN',
    'DELAY_MAX',
    'DELAY_BETWEEN_MESSAGES',
    'clean_phone_number',
    'format_name',
]
