"""Utilitários para formatação de texto."""
import pandas as pd


def formatar_nome(nome):
    """
    Converte nome em maiúsculo para minúsculo com primeira letra maiúscula.
    
    Pega só o primeiro nome (primeira palavra).
    
    Args:
        nome: Nome a formatar (pode estar em maiúsculo)
        
    Returns:
        str: Primeiro nome formatado com inicial maiúscula
        
    Exemplo:
        formatar_nome("GABRIEL FERNANDES") -> "Gabriel"
        formatar_nome("ANA SILVA") -> "Ana"
    """
    if pd.isna(nome) or not nome:
        return "Cliente"
    
    # Converte para string e remove espaços extras
    nome_str = str(nome).strip()
    
    # Converte para minúsculo
    nome_lower = nome_str.lower()
    
    # Pega só o primeiro nome (primeira palavra)
    primeiro_nome = nome_lower.split()[0]
    
    # Capitaliza a primeira letra
    nome_formatado = primeiro_nome.capitalize()
    
    return nome_formatado
