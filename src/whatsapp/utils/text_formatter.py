"""Utilities for text formatting."""
import pandas as pd


def format_name(name):
    """
    Convert uppercase name to lowercase with first letter capitalized.
    
    Takes only the first name (first word).
    
    Args:
        name: Name to format (may be uppercase)
        
    Returns:
        str: First name formatted with initial capital
        
    Example:
        format_name("GABRIEL FERNANDES") -> "Gabriel"
        format_name("ANA SILVA") -> "Ana"
    """
    if pd.isna(name) or not name:
        return "Cliente"
    
    # Convert to string and remove extra spaces
    name_str = str(name).strip()
    
    # Convert to lowercase
    name_lower = name_str.lower()
    
    # Take only the first name (first word)
    first_name = name_lower.split()[0]
    
    # Capitalize the first letter
    formatted_name = first_name.capitalize()
    
    return formatted_name
