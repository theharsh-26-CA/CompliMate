from datetime import datetime
from . import db

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plan'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # Starter, Professional, Enterprise
    price = db.Column(db.Float, nullable=False)  # Monthly price in INR
    companies_included = db.Column(db.Integer, nullable=False)  # Number of companies included
    extra_company_cost = db.Column(db.Float, nullable=False)  # Cost per additional company
    features = db.Column(db.JSON)  # JSON array of features
    is_active = db.Column(db.Boolean, default=True)
    stripe_price_id = db.Column(db.String(100))  # Stripe Price ID
    
    subscriptions = db.relationship('Subscription', backref='plan', lazy='dynamic')

class Subscription(db.Model):
    __tablename__ = 'subscription'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'), nullable=False)
    
    status = db.Column(db.String(20), default='active')  # active, past_due, canceled, trialing
    current_period_start = db.Column(db.DateTime, nullable=False)
    current_period_end = db.Column(db.DateTime, nullable=False)
    
    # Stripe Integration
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    stripe_customer_id = db.Column(db.String(100))
    
    # Billing
    next_billing_date = db.Column(db.DateTime)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='subscription', lazy='dynamic')
    invoices = db.relationship('Invoice', backref='subscription', lazy='dynamic', 
                               order_by='Invoice.created_at.desc()')
    usage_charges = db.relationship('UsageCharge', backref='subscription', lazy='dynamic')

class Invoice(db.Model):
    __tablename__ = 'invoice'
    
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=False)
    
    invoice_number = db.Column(db.String(50), unique=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    
    # Breakdown
    base_amount = db.Column(db.Float)  # Plan cost
    usage_amount = db.Column(db.Float)  # Ad-hoc charges
    tax_amount = db.Column(db.Float, default=0)
    
    # Stripe
    stripe_invoice_id = db.Column(db.String(100))
    stripe_payment_intent_id = db.Column(db.String(100))
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)

class UsageCharge(db.Model):
    __tablename__ = 'usage_charge'
    
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=False)
    
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, default=1)  # Number of extra companies
    unit_price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    
    charged_at = db.Column(db.DateTime, default=datetime.utcnow)
    invoiced = db.Column(db.Boolean, default=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=True)
