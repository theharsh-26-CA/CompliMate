from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, send_file
from flask_login import login_required, current_user
from app.models import db, Company, ComplianceRecord, Document, ComplianceMaster
from app.utils.validators import validate_pan, validate_gstin, extract_pan_from_gstin, validate_cin
from app.utils.tokens import generate_share_token, verify_share_token
from app.utils.decorators import role_required, log_audit, subscription_required
from app.services.subscription_service import SubscriptionService
from app.services.billing_service import BillingService
import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime

bp= Blueprint('dashboard', __name__)

@bp.route('/dashboard')
@login_required
def index():
    """Main dashboard router"""
    if current_user.is_super_admin:
        return redirect(url_for('admin.dashboard'))
    elif current_user.is_company_user:
        return redirect(url_for('dashboard.company_view', company_id=current_user.company_id))
    else:
        return practitioner_dashboard()

@login_required
def practitioner_dashboard():
    """Practitioner dashboard"""
    subscription = SubscriptionService.get_active_subscription(current_user)
    companies = Company.query.filter_by(
        practitioner_id=current_user.id,
        is_active=True
    ).all()
    
    # Get compliance stats
    total_compliances = 0
    pending_count = 0
    overdue_count = 0
    
    for company in companies:
        records = ComplianceRecord.query.filter_by(company_id=company.id).all()
        total_compliances += len(records)
        pending_count += sum(1 for r in records if r.status == 'Pending')
        overdue_count += sum(1 for r in records if r.status == 'Overdue')
    
    # Usage info
    usage = None
    if subscription:
        usage = BillingService.get_subscription_usage(subscription)
    
    return render_template('dashboard/practitioner.html',
                         companies=companies,
                         subscription=subscription,
                         usage=usage,
                         total_compliances=total_compliances,
                         pending_count=pending_count,
                         overdue_count=overdue_count)

@bp.route('/company/add', methods=['GET', 'POST'])
@login_required
@role_required('practitioner_admin', 'practitioner_staff')
@subscription_required
def add_company():
    """Add a new company"""
    subscription = SubscriptionService.get_active_subscription(current_user)
    can_add, message = SubscriptionService.can_add_company(subscription)
    
    if not can_add:
        flash(message, 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        cin = request.form.get('cin')
        gstin = request.form.get('gstin')
        pan = request.form.get('pan')
        
        # Validation
        if gstin:
            if not validate_gstin(gstin):
                flash('Invalid GSTIN format', 'error')
                return redirect(url_for('dashboard.add_company'))
            extracted_pan = extract_pan_from_gstin(gstin)
            if pan and pan != extracted_pan:
                flash('Provided PAN does not match GSTIN', 'error')
                return redirect(url_for('dashboard.add_company'))
            pan = extracted_pan
        
        if not validate_pan(pan):
            flash('Invalid PAN format', 'error')
            return redirect(url_for('dashboard.add_company'))
        
        if cin and not validate_cin(cin):
            flash('Invalid CIN format', 'error')
            return redirect(url_for('dashboard.add_company'))
        
        # Create company
        company = Company(
            name=name,
            cin=cin,
            gstin=gstin,
            pan=pan,
            practitioner_id=current_user.id,
            is_active=True
        )
        db.session.add(company)
        db.session.commit()
        
        # Check if ad-hoc charge needed
        if message and 'cost' in message.lower():
            BillingService.charge_extra_company(subscription, name)
            flash(f'Company added. {message}', 'warning')
        else:
            flash('Company added successfully', 'success')
        
        log_audit('ADD_COMPANY', f'Added company: {name}')
        return redirect(url_for('dashboard.index'))
    
    return render_template('dashboard/add_company.html', message=message)

@bp.route('/company/<int:company_id>')
@login_required
def company_view(company_id):
    """View company dashboard"""
    company = Company.query.get_or_404(company_id)
    
    # RBAC Check
    if current_user.is_practitioner and company.practitioner_id != current_user.id:
        abort(403)
    if current_user.is_company_user and current_user.company_id != company.id:
        abort(403)
    
    records = ComplianceRecord.query.filter_by(company_id=company.id).order_by(
        ComplianceRecord.due_date
    ).all()
    
    documents = Document.query.filter_by(company_id=company.id).order_by(
        Document.uploaded_at.desc()
    ).limit(10).all()
    
    return render_template('dashboard/company.html',
                         company=company,
                         records=records,
                         documents=documents,
                         readonly=False)

@bp.route('/company/<int:company_id>/share')
@login_required
@role_required('practitioner_admin')
def share_company(company_id):
    """Generate share link for company"""
    company = Company.query.get_or_404(company_id)
    
    if company.practitioner_id != current_user.id:
        abort(403)
    
    token = generate_share_token(company.id)
    link = url_for('dashboard.shared_view', token=token, _external=True)
    
    log_audit('SHARE_DASHBOARD', f'Shared dashboard for {company.name}')
    
    return render_template('dashboard/share_link.html', link=link, company=company)

@bp.route('/shared/<token>')
def shared_view(token):
    """View shared company dashboard"""
    company_id = verify_share_token(token)
    
    if not company_id:
        flash('Invalid or expired link', 'error')
        return redirect(url_for('auth.login'))
    
    company = Company.query.get_or_404(company_id)
    records = ComplianceRecord.query.filter_by(company_id=company.id).all()
    documents = Document.query.filter_by(company_id=company.id).order_by(
        Document.uploaded_at.desc()
    ).limit(10).all()
    
    return render_template('dashboard/company.html',
                         company=company,
                         records=records,
                         documents=documents,
                         readonly=True)

@bp.route('/company/<int:company_id>/upload', methods=['POST'])
@login_required
def upload_document(company_id):
    """Upload document"""
    company = Company.query.get_or_404(company_id)
    
    # RBAC Check
    if current_user.is_practitioner and company.practitioner_id != current_user.id:
        abort(403)
    if current_user.is_company_user and current_user.company_id != company.id:
        abort(403)
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('dashboard.company_view', company_id=company_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('dashboard.company_view', company_id=company_id))
    
    if file:
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(company.id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Add timestamp to filename to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        doc = Document(
            company_id=company.id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type,
            uploaded_by=current_user.id
        )
        db.session.add(doc)
        db.session.commit()
        
        log_audit('UPLOAD_DOCUMENT', f'Uploaded {filename} for {company.name}')
        flash('File uploaded successfully', 'success')
    
    return redirect(url_for('dashboard.company_view', company_id=company_id))
