import re

def validate_pan(pan):
    """Validate PAN format"""
    if not pan:
        return False
    pattern = r"[A-Z]{5}[0-9]{4}[A-Z]{1}"
    return bool(re.match(pattern, pan.upper()))

def validate_gstin(gstin):
    """Validate GSTIN format"""
    if not gstin:
        return False
    pattern = r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}"
    return bool(re.match(pattern, gstin.upper()))

def extract_pan_from_gstin(gstin):
    """Extract PAN from GSTIN"""
    if validate_gstin(gstin):
        return gstin[2:12]
    return None

def validate_email(email):
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_cin(cin):
    """Validate CIN/LLPIN format (basic check)"""
    if not cin:
        return True  # CIN is optional
    # Basic pattern: L/U followed by digits
    pattern = r'[LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}'
    return bool(re.match(pattern, cin.upper()))
