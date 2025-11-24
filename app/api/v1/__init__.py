"""API v1 Blueprint"""
from flask import Blueprint, jsonify, request, abort
from app.models import db, Company, ComplianceRecord, User
from app.utils.decorators import log_audit
from flask_login import login_required, current_user

api_bp = Blueprint('api_v1', __name__)

@api_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'version': '1.0.0'}), 200

@api_bp.route('/companies')
@login_required
def list_companies():
    """List companies for current user"""
    if current_user.is_super_admin:
        companies = Company.query.all()
    elif current_user.is_practitioner:
        companies = Company.query.filter_by(practitioner_id=current_user.id).all()
    else:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'companies': [{
            'id': c.id,
            'name': c.name,
            'pan': c.pan,
            'is_active': c.is_active
        } for c in companies]
    }), 200

@api_bp.route('/companies/<int:company_id>/compliances')
@login_required
def company_compliances(company_id):
    """Get compliance records for a company"""
    company = Company.query.get_or_404(company_id)
    
    # Check access
    if not current_user.is_super_admin:
        if current_user.is_practitioner and company.practitioner_id != current_user.id:
            abort(403)
        if current_user.is_company_user and current_user.company_id != company.id:
            abort(403)
    
    records = ComplianceRecord.query.filter_by(company_id=company.id).all()
    
    return jsonify({
        'company': company.name,
        'compliances': [{
            'id': r.id,
            'name': r.compliance_master.name,
            'due_date': r.due_date.isoformat(),
            'status': r.status,
            'financial_year': r.financial_year
        } for r in records]
    }), 200

@api_bp.route('/stats')
@login_required
def stats():
    """Get system stats"""
    if not current_user.is_super_admin:
        abort(403)
    
    total_companies = Company.query.count()
    total_users = User.query.count()
    active_compliances = ComplianceRecord.query.filter_by(status='Pending').count()
    
    return jsonify({
        'total_companies': total_companies,
        'total_users': total_users,
        'active_compliances': active_compliances
    }), 200
