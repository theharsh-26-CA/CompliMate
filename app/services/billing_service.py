from datetime import datetime
from app.models import db, Invoice, UsageCharge, Subscription

class BillingService:
    """Handles billing, invoices, and usage charges"""
    
    @staticmethod
    def create_usage_charge(subscription, description, quantity, unit_price):
        """Create a usage charge for ad-hoc billing"""
        charge = UsageCharge(
            subscription_id=subscription.id,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            amount=quantity * unit_price,
            charged_at=datetime.utcnow(),
            invoiced=False
        )
        
        db.session.add(charge)
        db.session.commit()
        
        return charge
    
    @staticmethod
    def charge_extra_company(subscription, company_name):
        """Charge for adding a company beyond plan limit"""
        plan = subscription.plan
        
        charge = BillingService.create_usage_charge(
            subscription,
            f"Additional company: {company_name}",
            1,
            plan.extra_company_cost
        )
        
        return charge
    
    @staticmethod
    def create_invoice(subscription, base_amount=None, stripe_invoice_id=None):
        """Create an invoice for a subscription"""
        plan = subscription.plan
        
        if base_amount is None:
            base_amount = plan.price
        
        # Calculate usage charges
        pending_charges = UsageCharge.query.filter_by(
            subscription_id=subscription.id,
            invoiced=False
        ).all()
        
        usage_amount = sum(charge.amount for charge in pending_charges)
        
        invoice = Invoice(
            subscription_id=subscription.id,
            invoice_number=f"INV-{subscription.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            base_amount=base_amount,
            usage_amount=usage_amount,
            amount=base_amount + usage_amount,
            tax_amount=0,
            status='pending',
            stripe_invoice_id=stripe_invoice_id,
            created_at=datetime.utcnow(),
            due_date=datetime.utcnow()
        )
        
        db.session.add(invoice)
        
        # Mark charges as invoiced
        for charge in pending_charges:
            charge.invoiced = True
            charge.invoice_id = invoice.id
        
        db.session.commit()
        
        return invoice
    
    @staticmethod
    def mark_invoice_paid(invoice, stripe_payment_intent_id=None):
        """Mark an invoice as paid"""
        invoice.status = 'paid'
        invoice.paid_at = datetime.utcnow()
        invoice.stripe_payment_intent_id = stripe_payment_intent_id
        
        db.session.commit()
        return invoice
    
    @staticmethod
    def get_subscription_usage(subscription):
        """Get current billing period usage"""
        plan = subscription.plan
        
        # Get company count
        from app.services.subscription_service import SubscriptionService
        company_count = SubscriptionService.get_company_count(subscription)
        
        # Calculate overage
        included = plan.companies_included
        extra_companies = max(0, company_count - included) if included != -1 else 0
        
        # Get pending charges
        pending_charges = UsageCharge.query.filter_by(
            subscription_id=subscription.id,
            invoiced=False
        ).all()
        
        return {
            'company_count': company_count,
            'companies_included': included,
            'extra_companies': extra_companies,
            'pending_charges': pending_charges,
            'pending_amount': sum(c.amount for c in pending_charges)
        }
