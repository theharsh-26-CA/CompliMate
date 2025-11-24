from functools import wraps
from flask import abort, request
from flask_login import current_user
from app.models import db, AuditLog

def role_required(*roles):
    """Decorator to require specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator for super admin only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.is_super_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def subscription_required(f):
    """Decorator to ensure user has active subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        
        if current_user.is_super_admin:
            return f(*args, **kwargs)
            
        from app.services.subscription_service import SubscriptionService
        subscription = SubscriptionService.get_active_subscription(current_user)
        
        if not subscription or subscription.status != 'active':
            abort(403, description="Active subscription required")
            
        return f(*args, **kwargs)
    return decorated_function

def log_audit(action, details=None):
    """Log an audit event"""
    try:
        if current_user.is_authenticated:
            log = AuditLog(
                user_id=current_user.id,
                action=action,
                details=details[:255] if details else None,
                ip_address=request.remote_addr if request else None
            )
            db.session.add(log)
            db.session.commit()
    except Exception as e:
        # Don't fail the request if logging fails
        print(f"Audit log error: {e}")
        db.session.rollback()
