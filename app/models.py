from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='practitioner') # practitioner, company_user, staff
    
    # For Company Users
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # Relationships
    companies = db.relationship('Company', foreign_keys='Company.practitioner_id', backref='practitioner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    @property
    def is_practitioner(self):
        return self.role == 'practitioner'
        
    @property
    def is_company_user(self):
        return self.role == 'company_user'

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False) # LOGIN, UPLOAD, UPDATE, VIEW
    details = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs', lazy=True)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    practitioner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    cin = db.Column(db.String(21), unique=True) # Corporate Identity Number
    pan = db.Column(db.String(10), nullable=False)
    gstin = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    compliance_records = db.relationship('ComplianceRecord', backref='company', lazy=True)
    documents = db.relationship('Document', backref='company', lazy=True)
    users = db.relationship('User', foreign_keys='User.company_id', backref='company_ref', lazy=True)

class ComplianceMaster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    base_due_date = db.Column(db.String(20)) # Stored as "DD-MM" or cron-like format
    frequency = db.Column(db.String(50)) # Monthly, Quarterly, Annually
    category = db.Column(db.String(50)) # GST, Income Tax, MCA, etc.
    
    overrides = db.relationship('ComplianceOverride', backref='compliance', lazy=True)

class ComplianceOverride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    compliance_id = db.Column(db.Integer, db.ForeignKey('compliance_master.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    new_due_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(255)) # e.g., "Extended by Notification X"
    is_permanent = db.Column(db.Boolean, default=False) # If true, might update master

class ComplianceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    compliance_id = db.Column(db.Integer, db.ForeignKey('compliance_master.id'), nullable=False)
    
    status = db.Column(db.String(20), default='Pending') # Pending, Completed, Overdue
    due_date = db.Column(db.Date, nullable=False) # The actual calculated due date for this instance
    completed_date = db.Column(db.Date)
    financial_year = db.Column(db.String(9)) # e.g., "2023-2024"
    
    documents = db.relationship('Document', backref='compliance_record', lazy=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    compliance_record_id = db.Column(db.Integer, db.ForeignKey('compliance_record.id'), nullable=True)
    
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Could be practitioner or company user
