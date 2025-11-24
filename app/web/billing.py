from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app.models import db, Subscription, SubscriptionPlan, Invoice
from app.services.subscription_service import SubscriptionService
from app.services.billing_service import BillingService
from app.utils.decorators import role_required, log_audit
from datetime import datetime

bp = Blueprint('billing', __name__)

@bp.route('/')
@login_required
@role_required('practitioner_admin')
def index():
    """Billing dashboard"""
    subscription = SubscriptionService.get_active_subscription(current_user)
    
    if not subscription:
        # Show available plans
        plans = SubscriptionPlan.query.filter_by(is_active=True).all()
        return render_template('billing/choose_plan.html', plans=plans)
    
    # Get usage and invoices
    usage = BillingService.get_subscription_usage(subscription)
    invoices = Invoice.query.filter_by(subscription_id=subscription.id).order_by(
        Invoice.created_at.desc()
    ).limit(12).all()
    
    return render_template('billing/index.html',
                         subscription=subscription,
                         usage=usage,
                         invoices=invoices)

@bp.route('/subscribe/<int:plan_id>', methods=['POST'])
@login_required
@role_required('practitioner_admin')
def subscribe(plan_id):
    """Subscribe to a plan"""
    existing_subscription = SubscriptionService.get_active_subscription(current_user)
    
    if existing_subscription:
        flash('You already have an active subscription', 'error')
        return redirect(url_for('billing.index'))
    
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    # For prototype, create subscription directly without Stripe
    # In production, this would redirect to Stripe Checkout
    subscription = SubscriptionService.create_subscription(current_user, plan.id)
    
    # Create first invoice
    invoice = BillingService.create_invoice(subscription)
    
    log_audit('SUBSCRIPTION_CREATE', f'Subscribed to {plan.name}')
    flash(f'Successfully subscribed to {plan.name}!', 'success')
    
    return redirect(url_for('billing.index'))

@bp.route('/change-plan/<int:plan_id>', methods=['POST'])
@login_required
@role_required('practitioner_admin')
def change_plan(plan_id):
    """Change subscription plan"""
    subscription = SubscriptionService.get_active_subscription(current_user)
    
    if not subscription:
        flash('No active subscription', 'error')
        return redirect(url_for('billing.index'))
    
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    if subscription.plan_id == plan_id:
        flash('You are already on this plan', 'warning')
        return redirect(url_for('billing.index'))
    
    SubscriptionService.upgrade_plan(subscription, plan_id)
    
    log_audit('SUBSCRIPTION_CHANGE', f'Changed plan to {plan.name}')
    flash(f'Plan changed to {plan.name}', 'success')
    
    return redirect(url_for('billing.index'))

@bp.route('/cancel', methods=['POST'])
@login_required
@role_required('practitioner_admin')
def cancel():
    """Cancel subscription"""
    subscription = SubscriptionService.get_active_subscription(current_user)
    
    if not subscription:
        flash('No active subscription', 'error')
        return redirect(url_for('billing.index'))
    
    SubscriptionService.cancel_subscription(subscription, immediately=False)
    
    log_audit('SUBSCRIPTION_CANCEL', 'Canceled subscription')
    flash('Subscription will be canceled at the end of the billing period', 'info')
    
    return redirect(url_for('billing.index'))

@bp.route('/invoice/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    """View invoice details"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Check access
    subscription = SubscriptionService.get_active_subscription(current_user)
    if not subscription or invoice.subscription_id != subscription.id:
        if not current_user.is_super_admin:
            abort(403)
    
    return render_template('billing/invoice.html', invoice=invoice)

@bp.route('/plans')
@login_required
def view_plans():
    """View all available plans"""
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    current_subscription = SubscriptionService.get_active_subscription(current_user)
    
    return render_template('billing/plans.html',
                         plans=plans,
                         current_subscription=current_subscription)
