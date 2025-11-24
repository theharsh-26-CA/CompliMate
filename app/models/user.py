from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='practitioner_admin', index=True)
    # Roles: super_admin, practitioner_admin, practitioner_staff, company_user
    
    # For Company Users
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # For Practitioners
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    companies = db.relationship('Company', foreign_keys='Company.practitioner_id', 
                               backref='practitioner', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    @property
    def is_super_admin(self):
        return self.role == 'super_admin'
        
    @property
    def is_practitioner_admin(self):
        return self.role == 'practitioner_admin'
        
    @property
    def is_practitioner_staff(self):
        return self.role == 'practitioner_staff'
        
    @property
    def is_company_user(self):
        return self.role == 'company_user'
        
    @property
    def is_practitioner(self):
        return self.role in ['practitioner_admin', 'practitioner_staff']

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    details = db.Column(db.String(255))
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref='audit_logs', lazy=True)
