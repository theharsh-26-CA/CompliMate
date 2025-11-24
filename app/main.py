from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import db, Company, User, ComplianceRecord, Document, ComplianceMaster
from app.utils import validate_pan, validate_gstin, extract_pan_from_gstin, generate_share_token, verify_share_token
from app.decorators import role_required, log_audit
import os
from werkzeug.utils import secure_filename
from flask import current_app

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_practitioner:
        companies = Company.query.filter_by(practitioner_id=current_user.id).all()
        return render_template('practitioner_dashboard.html', companies=companies)
    elif current_user.is_company_user:
        return redirect(url_for('main.company_dashboard', company_id=current_user.company_id))
    else:
        return "Unauthorized Role", 403

@main.route('/company/add', methods=['GET', 'POST'])
@login_required
@role_required('practitioner')
def add_company():
        
    if request.method == 'POST':
        name = request.form.get('name')
        cin = request.form.get('cin')
        gstin = request.form.get('gstin')
        pan = request.form.get('pan')
        
        if gstin:
            if not validate_gstin(gstin):
                flash('Invalid GSTIN format')
                return redirect(url_for('main.add_company'))
            extracted_pan = extract_pan_from_gstin(gstin)
            if pan and pan != extracted_pan:
                flash('Provided PAN does not match GSTIN')
                return redirect(url_for('main.add_company'))
            pan = extracted_pan
        
        if not validate_pan(pan):
            flash('Invalid PAN format')
            return redirect(url_for('main.add_company'))
            
        company = Company(
            name=name,
            cin=cin,
            gstin=gstin,
            pan=pan,
            practitioner_id=current_user.id
        )
        db.session.add(company)
        db.session.commit()
        log_audit('ADD_COMPANY', f"Added company {name}")
        flash('Company added successfully')
        return redirect(url_for('main.dashboard'))
        
    return render_template('add_company.html')

@main.route('/company/<int:company_id>')
@login_required
def company_dashboard(company_id):
    company = Company.query.get_or_404(company_id)
    
    # RBAC Check
    if current_user.is_practitioner and company.practitioner_id != current_user.id:
        abort(403)
    if current_user.is_company_user and current_user.company_id != company.id:
        abort(403)
        
    records = ComplianceRecord.query.filter_by(company_id=company.id).all()
    return render_template('company_dashboard.html', company=company, records=records)

@main.route('/company/<int:company_id>/share')
@login_required
@role_required('practitioner')
def share_company(company_id):
    company = Company.query.get_or_404(company_id)
    if company.practitioner_id != current_user.id:
        abort(403)
    
    token = generate_share_token(company.id)
    log_audit('SHARE_DASHBOARD', f"Shared dashboard for {company.name}")
    link = url_for('main.shared_view', token=token, _external=True)
    return render_template('share_link.html', link=link, company=company)

@main.route('/shared/<token>')
def shared_view(token):
    company_id = verify_share_token(token)
    if not company_id:
        return "Invalid or Expired Link", 403
        
    company = Company.query.get_or_404(company_id)
    records = ComplianceRecord.query.filter_by(company_id=company.id).all()
    return render_template('company_dashboard.html', company=company, records=records, readonly=True)

@main.route('/company/<int:company_id>/upload', methods=['POST'])
@login_required
def upload_document(company_id):
    company = Company.query.get_or_404(company_id)
    
    # RBAC Check
    if current_user.is_practitioner and company.practitioner_id != current_user.id:
        abort(403)
    if current_user.is_company_user and current_user.company_id != company.id:
        abort(403)
        
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('main.company_dashboard', company_id=company_id))
        
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('main.company_dashboard', company_id=company_id))
        
    if file:
        filename = secure_filename(file.filename)
        # Structure: uploads/company_id/filename
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(company.id))
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        doc = Document(
            company_id=company.id,
            filename=filename,
            file_path=file_path,
            uploaded_by=current_user.id
        )
        db.session.add(doc)
        db.session.commit()
        log_audit('UPLOAD_DOCUMENT', f"Uploaded {filename} for {company.name}")
        flash('File uploaded successfully')
        
    return redirect(url_for('main.company_dashboard', company_id=company_id))
