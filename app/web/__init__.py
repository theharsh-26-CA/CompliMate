# Web blueprints
from .auth import bp as auth_bp
from .dashboard import bp as dashboard_bp
from .admin import bp as admin_bp
from .billing import bp as billing_bp

__all__ = ['auth_bp', 'dashboard_bp', 'admin_bp', 'billing_bp']
