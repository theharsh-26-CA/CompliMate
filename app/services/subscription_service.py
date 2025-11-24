from datetime import datetime, timedelta
from app.models import db, Subscription, SubscriptionPlan, UsageCharge, Company

class SubscriptionService:
    """Handles subscription management and plan enforcement"""
    
    @staticmethod
    def get_active_subscription(user):
        """Get user's active subscription"""
        if user.subscription_id:
            return Subscription.query.get(user.subscription_id)
        return None
    
    @staticmethod
    def create_subscription(user, plan_id, stripe_subscription_id=None, stripe_customer_id=None):
        """Create a new subscription for a user"""
        plan = SubscriptionPlan.query.get_or_404(plan_id)
        
        subscription = Subscription(
            plan_id=plan.id,
            status='active',
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            next_billing_date=datetime.utcnow() + timedelta(days=30),
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        # Link user to subscription
        user.subscription_id = subscription.id
        db.session.commit()
        
        return subscription
    
    @staticmethod
    def can_add_company(subscription):
        """Check if user can add more companies based on their plan"""
        if not subscription:
            return False, "No active subscription"
            
        plan = subscription.plan
        
        # Count active companies under this subscription
        active_companies = Company.query.join(
            'practitioner'
        ).filter(
            Company.is_active == True,
            db.text('user.subscription_id = :sub_id')
        ).params(sub_id=subscription.id).count()
        
        if plan.companies_included == -1:  # Unlimited (Enterprise)
            return True, None
            
        if active_companies < plan.companies_included:
            return True, None
            
        # They can still add, but will be charged
        return True, f"Additional company will cost ₹{plan.extra_company_cost}"
    
    @staticmethod
    def get_company_count(subscription):
        """Get number of active companies for a subscription"""
        from app.models import User
        
        # Get all practitioners with this subscription
        users = User.query.filter_by(subscription_id=subscription.id).all()
        user_ids = [u.id for u in users]
        
        # Count their active companies
        count = Company.query.filter(
            Company.practitioner_id.in_(user_ids),
            Company.is_active == True
        ).count()
        
        return count
    
    @staticmethod
    def upgrade_plan(subscription, new_plan_id):
        """Upgrade/downgrade subscription plan"""
        subscription.plan_id = new_plan_id
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        return subscription
    
    @staticmethod
    def cancel_subscription(subscription, immediately=False):
        """Cancel a subscription"""
        if immediately:
            subscription.status = 'canceled'
            subscription.current_period_end = datetime.utcnow()
        else:
            subscription.cancel_at_period_end = True
        
        db.session.commit()
        return subscription
