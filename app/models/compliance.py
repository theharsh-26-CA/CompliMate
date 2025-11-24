from datetime import datetime
from . import db

class ComplianceMaster(db.Model):
    __tablename__ = 'compliance_master'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    base_due_date = db.Column(db.String(20))  # Stored as "DD" or "DD-MM"
    frequency = db.Column(db.String(50))  # Monthly, Quarterly, Annually
    category = db.Column(db.String(50), index=True)  # GST, Income Tax, MCA, etc.
    
    is_active = db.Column(db.Boolean, default=True)
    
    overrides = db.relationship('ComplianceOverride', backref='compliance', lazy='dynamic')
    records = db.relationship('ComplianceRecord', backref='compliance_master', lazy='dynamic')

class ComplianceOverride(db.Model):
    __tablename__ = 'compliance_override'
    
    id = db.Column(db.Integer, primary_key=True)
    compliance_id = db.Column(db.Integer, db.ForeignKey('compliance_master.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False, index=True)
    new_due_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(255))
    is_permanent = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ComplianceRecord(db.Model):
    __tablename__ = 'compliance_record'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False, index=True)
    compliance_id = db.Column(db.Integer, db.ForeignKey('compliance_master.id'), nullable=False)
    
    status = db.Column(db.String(20), default='Pending', index=True)  # Pending, Completed, Overdue
    due_date = db.Column(db.Date, nullable=False, index=True)
    completed_date = db.Column(db.Date)
    financial_year = db.Column(db.String(9), index=True)  # e.g., "2023-2024"
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    documents = db.relationship('Document', backref='compliance_record', lazy='dynamic')
