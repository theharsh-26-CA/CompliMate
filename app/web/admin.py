from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app.models import db, User, Company, Subscription, SubscriptionPlan, AuditLog, Invoice
from app.utils.decorators import admin_required, log_audit
from sqlalchemy import func, desc
from datetime import datetime, timedelta

bp = Blueprint('admin', __name__)

@bp.route('/')
@login_required
@admin_required
def dashboard():
    """Super Admin Dashboard"""
    # System Stats
    total_users = User.query.count()
    total_practitioners = User.query.filter(
        User.role.in_(['practitioner_admin', 'practitioner_staff'])
    ).count()
    total_companies = Company.query.count()
    active_subscriptions = Subscription.query.filter_by(status='active').count()
    
    # Revenue stats
    total_revenue = db.session.query(func.sum(Invoice.amount)).filter_by(status='paid').scalar() or 0
    
    # Recent activity
    recent_logs = AuditLog.query.order_by(desc(AuditLog.timestamp)).limit(20).all()
    
    # Subscription distribution
    subscription_stats = db.session.query(
        SubscriptionPlan.name,
        func.count(Subscription.id).label('count')
    ).join(Subscription).filter(
        Subscription.status == 'active'
    ).group_by(SubscriptionPlan.name).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_practitioners=total_practitioners,
                         total_companies=total_companies,
                         active_subscriptions=active_subscriptions,
                         total_revenue=total_revenue,
                         recent_logs=recent_logs,
                         subscription_stats=subscription_stats)

@bp.route('/users')
@login_required
@admin_required
def users():
    """Manage all users"""
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', None)
    
    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    users_pagination = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin/users.html', users=users_pagination)

@bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    """Activate/deactivate user"""
    user = User.query.get_or_404(user_id)
    
    if user.is_super_admin:
        flash('Cannot deactivate super admin', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    action = 'activated' if user.is_active else 'deactivated'
    log_audit('USER_STATUS_CHANGE', f'User {user.email} {action}')
    flash(f'User {action} successfully', 'success')
    
    return redirect(url_for('admin.users'))

@bp.route('/subscriptions')
@login_required
@admin_required
def subscriptions():
    """View all subscriptions"""
    page = request.args.get('page', 1, type=int)
    
    subscriptions_pagination = Subscription.query.order_by(
        desc(Subscription.created_at)
    ).paginate(page=page, per_page=50, error_out=False)
    
    return render_template('admin/subscriptions.html', 
                         subscriptions=subscriptions_pagination)

@bp.route('/subscriptions/<int:sub_id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_subscription(sub_id):
    """Cancel a subscription"""
    subscription = Subscription.query.get_or_404(sub_id)
    subscription.status = 'canceled'
    subscription.current_period_end = datetime.utcnow()
    db.session.commit()
    
    log_audit('SUBSCRIPTION_CANCEL', f'Subscription {sub_id} canceled by admin')
    flash('Subscription canceled', 'success')
    
    return redirect(url_for('admin.subscriptions'))

@bp.route('/plans')
@login_required
@admin_required
def plans():
    """Manage subscription plans"""
    all_plans = SubscriptionPlan.query.all()
    return render_template('admin/plans.html', plans=all_plans)

@bp.route('/plans/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_plan():
    """Create a new subscription plan"""
    if request.method == 'POST':
        plan = SubscriptionPlan(
            name=request.form['name'],
            price=float(request.form['price']),
            companies_included=int(request.form['companies_included']),
            extra_company_cost=float(request.form['extra_company_cost']),
            features=request.form.get('features', '').split('\n') if request.form.get('features') else [],
            is_active=True
        )
        db.session.add(plan)
        db.session.commit()
        
        log_audit('PLAN_CREATE', f'Created plan: {plan.name}')
        flash('Plan created successfully', 'success')
        return redirect(url_for('admin.plans'))
    
    return render_template('admin/create_plan.html')

@bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    """View audit logs"""
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', None)
    
    query = AuditLog.query
    if action_filter:
        query = query.filter_by(action=action_filter)
    
    logs_pagination = query.order_by(desc(AuditLog.timestamp)).paginate(
        page=page, per_page=100, error_out=False
    )
    
    return render_template('admin/audit_logs.html', logs=logs_pagination)

@bp.route('/impersonate/<int:user_id>')
@login_required
@admin_required
def impersonate(user_id):
    """Impersonate a user for support (requires additional security)"""
    # This is a sensitive feature - implement with caution
    # For now, just redirect to their dashboard
    flash('Impersonation feature - to be implemented with additional security', 'warning')
    return redirect(url_for('admin.users'))
