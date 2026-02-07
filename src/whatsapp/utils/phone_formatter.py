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


def is_mobile_phone(phone: str) -> bool:
    """
    Check if the phone number is a Brazilian mobile phone (not landline).
    
    Brazilian mobile phones:
    - Have 11 digits after country code (55): DDD (2) + 9 + number (8)
    - The 3rd digit after 55 (first after DDD) must be 9
    
    Brazilian landlines:
    - Have 10 digits after country code: DDD (2) + number (8)
    - The 3rd digit after 55 is NOT 9
    
    Args:
        phone: Cleaned phone number with country code (55)
        
    Returns:
        True if mobile, False if landline
        
    Example:
        is_mobile_phone("5543998377239") -> True  (mobile: 9 after DDD)
        is_mobile_phone("554333411775")  -> False (landline: 3 after DDD)
    """
    if not phone or not phone.startswith('55'):
        return False
    
    # Remove country code to analyze
    local_number = phone[2:]  # Remove '55'
    
    # Mobile: 11 digits (DDD + 9 + 8 digits)
    # Landline: 10 digits (DDD + 8 digits)
    if len(local_number) == 11:
        # Check if 3rd digit (after DDD) is 9
        return local_number[2] == '9'
    elif len(local_number) == 10:
        # 10 digits = landline
        return False
    
    return False

