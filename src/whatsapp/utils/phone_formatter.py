"""Utilities for phone number processing."""
import re
import pandas as pd


def clean_phone_number(num):
    """
    Remove non-numeric characters and validate format.
    
    Ensures the number has the Brazil country code (55).
    
    Args:
        num: Raw phone number
        
    Returns:
        str: Cleaned number with country code, or None if invalid
        
    Example:
        clean_phone_number("(43) 99837-7239") -> "5543998377239"
        clean_phone_number(4398377239) -> "554398377239"
    """
    if pd.isna(num):
        return None
    
    s_num = str(num)
    # Remove everything that is not a digit
    clean = re.sub(r'\D', '', s_num)
    
    # Basic validation: needs at least area code + number (10 or 11 digits)
    if len(clean) < 10:
        return None
    
    # Add country code 55 if not present
    if not clean.startswith('55'):
        clean = '55' + clean
    
    return clean
