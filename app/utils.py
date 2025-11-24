import re
import jwt
import datetime
from flask import current_app

def validate_pan(pan):
    pattern = r"[A-Z]{5}[0-9]{4}[A-Z]{1}"
    return bool(re.match(pattern, pan))

def validate_gstin(gstin):
    pattern = r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}"
    return bool(re.match(pattern, gstin))

def extract_pan_from_gstin(gstin):
    if validate_gstin(gstin):
        return gstin[2:12]
    return None

def generate_share_token(company_id, expires_in=3600*24*30): # 30 days default
    payload = {
        'company_id': company_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_share_token(token):
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['company_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
