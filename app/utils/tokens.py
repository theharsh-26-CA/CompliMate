import jwt
import datetime
from flask import current_app

def generate_share_token(company_id, expires_in=3600*24*30):
    """Generate a JWT token for sharing company dashboard"""
    payload = {
        'company_id': company_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in),
        'type': 'share_link'
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_share_token(token):
    """Verify and decode share token"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        if payload.get('type') != 'share_link':
            return None
        return payload['company_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_api_token(user_id, expires_in=3600*24*365):
    """Generate API token for API access"""
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in),
        'type': 'api_token'
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_api_token(token):
    """Verify API token"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        if payload.get('type') != 'api_token':
            return None
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
