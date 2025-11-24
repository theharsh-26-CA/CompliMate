from datetime import datetime
from . import db

class Company(db.Model):
    __tablename__ = 'company'
    
    id = db.Column(db.Integer, primary_key=True)
    practitioner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    cin = db.Column(db.String(21), unique=True, nullable=True)  # Corporate Identity Number
    pan = db.Column(db.String(10), nullable=False, index=True)
    gstin = db.Column(db.String(15), index=True)
    
    is_active = db.Column(db.Boolean, default=True)
    deactivated_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    compliance_records = db.relationship('ComplianceRecord', backref='company', lazy='dynamic')
    documents = db.relationship('Document', backref='company', lazy='dynamic')
    users = db.relationship('User', foreign_keys='User.company_id', 
                           backref='company_ref', lazy='dynamic')
