from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User
from app.utils.decorators import log_audit
from urllib.parse import urlparse
from datetime import datetime

bp = Blueprint('auth', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Your account has been deactivated', 'error')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=request.form.get('remember_me'))
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        log_audit('LOGIN', f'User logged in: {email}')
        
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            # Route based on role
            if user.is_super_admin:
                next_page = url_for('admin.dashboard')
            else:
                next_page = url_for('dashboard.index')
        
        return redirect(next_page)
        
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))
            
        user = User(email=email, name=name, role='practitioner_admin')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        log_audit('REGISTER', f'New user registered: {email}')
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    log_audit('LOGOUT', f'User logged out')
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))
