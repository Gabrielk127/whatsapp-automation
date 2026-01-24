"""Utilitários para processamento de números de telefone."""
import re
import pandas as pd


def limpar_numero(num):
    """
    Remove caracteres não numéricos e valida formato.
    
    Garante que o número tem o DDI 55 (Brasil).
    
    Args:
        num: Número de telefone bruto
        
    Returns:
        str: Número limpo com DDI, ou None se inválido
        
    Exemplo:
        limpar_numero("(43) 99837-7239") -> "5543998377239"
        limpar_numero(4398377239) -> "554398377239"
    """
    if pd.isna(num):
        return None
    
    s_num = str(num)
    # Remove tudo que não é dígito
    clean = re.sub(r'\D', '', s_num)
    
    # Validação básica: precisa ter pelo menos DDD + numero (10 ou 11 dígitos)
    if len(clean) < 10:
        return None
    
    # Adiciona DDI 55 se não tiver
    if not clean.startswith('55'):
        clean = '55' + clean
    
    return clean
