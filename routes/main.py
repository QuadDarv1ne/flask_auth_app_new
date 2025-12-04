from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, current_user
from app import db
from forms import UpdateProfileForm, ChangePasswordForm, ContactForm, TwoFactorSetupForm, TwoFactorVerifyForm
from utils.logging import log_user_action
from utils.performance import cache_response
import os
from werkzeug.utils import secure_filename
import pyqrcode
import io
import base64

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@cache_response(timeout=300)  # Кэшируем главную страницу на 5 минут
def index():
    """Главная страница"""
    return render_template('main/index.html', title='Главная')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Личный кабинет пользователя"""
    return render_template('main/dashboard.html', title='Личный кабинет', user=current_user)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Страница профиля пользователя"""
    profile_form = UpdateProfileForm(current_user.username, current_user.email)
    password_form = ChangePasswordForm()
    twofa_form = TwoFactorSetupForm()
    
    # Handle profile form submission (when accessed via GET or POST but not from password form)
    if request.method == 'POST' and 'submit' in request.form and profile_form.validate_on_submit():
        old_username = current_user.username
        current_user.username = profile_form.username.data
        current_user.email = profile_form.email.data
        
        # Handle avatar upload
        if profile_form.avatar.data:
            avatar_file = profile_form.avatar.data
            filename = secure_filename(avatar_file.filename)
            if filename:
                # Create avatars directory if it doesn't exist
                avatar_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
                os.makedirs(avatar_dir, exist_ok=True)
                
                # Generate unique filename
                name, ext = os.path.splitext(filename)
                unique_filename = f"{current_user.id}_{secure_filename(name)}{ext}"
                filepath = os.path.join(avatar_dir, unique_filename)
                
                # Save the file
                avatar_file.save(filepath)
                
                # Update user's avatar filename
                current_user.set_avatar(unique_filename)
        
        db.session.commit()
        
        log_user_action(
            current_user.username,
            'profile_updated',
            f'Old username: {old_username}, New email: {current_user.email}'
        )
        
        flash('Ваш профиль успешно обновлен!', 'success')
        return redirect(url_for('main.profile'))
    
    # Handle 2FA setup form
    if request.method == 'POST' and 'enable_2fa' in request.form and twofa_form.validate_on_submit():
        if not current_user.is_2fa_enabled:
            # Enable 2FA and generate secret
            secret = current_user.enable_2fa()
            # Generate QR code for setup
            qr_uri = current_user.get_totp_uri()
            qr_code = pyqrcode.create(qr_uri)
            buffer = io.BytesIO()
            qr_code.svg(buffer, scale=4)
            qr_code_svg = buffer.getvalue().decode('utf-8')
            session['qr_code'] = qr_code_svg
            session['totp_secret'] = secret
            return redirect(url_for('main.setup_2fa'))
    
    # Handle 2FA disable form
    if request.method == 'POST' and 'disable_2fa' in request.form:
        current_user.disable_2fa()
        db.session.commit()
        flash('Двухфакторная аутентификация отключена.', 'success')
        return redirect(url_for('main.profile'))
    
    # Populate forms with current data
    profile_form.username.data = current_user.username
    profile_form.email.data = current_user.email
    
    return render_template('main/profile.html', 
                         title='Профиль',
                         user=current_user,
                         profile_form=profile_form,
                         password_form=password_form,
                         twofa_form=twofa_form)

@main_bp.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Настройка 2FA"""
    # Check if we have QR code in session
    qr_code = session.get('qr_code')
    totp_secret = session.get('totp_secret')
    
    if not qr_code or not totp_secret:
        flash('Необходимо сначала начать настройку 2FA.', 'warning')
        return redirect(url_for('main.profile'))
    
    form = TwoFactorVerifyForm()
    if form.validate_on_submit():
        # Verify the token
        if current_user.verify_totp(str(form.token.data)):
            flash('Двухфакторная аутентификация успешно настроена!', 'success')
            # Clear session data
            session.pop('qr_code', None)
            session.pop('totp_secret', None)
            return redirect(url_for('main.profile'))
        else:
            flash('Неверный код. Попробуйте еще раз.', 'danger')
    
    return render_template('main/setup_2fa.html', 
                         title='Настройка 2FA',
                         user=current_user,
                         form=form,
                         qr_code=qr_code,
                         totp_secret=totp_secret)

@main_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Изменение пароля пользователя"""
    password_form = ChangePasswordForm()
    
    if password_form.validate_on_submit():
        # Проверка текущего пароля
        if not current_user.check_password(password_form.current_password.data):
            flash('Неверный текущий пароль!', 'error')
            return redirect(url_for('main.profile'))
        
        # Установка нового пароля
        current_user.set_password(password_form.new_password.data)
        db.session.commit()
        
        log_user_action(
            current_user.username,
            'password_changed',
            'Password successfully updated'
        )
        
        flash('Пароль успешно изменен!', 'success')
        return redirect(url_for('main.profile'))
    
    # Handle form validation errors
    for field, errors in password_form.errors.items():
        for error in errors:
            flash(f'{getattr(password_form, field).label.text}: {error}', 'error')
    
    return redirect(url_for('main.profile'))

@main_bp.route('/about')
@cache_response(timeout=600)  # Кэшируем страницу "О нас" на 10 минут
def about():
    """Страница О нас"""
    return render_template('main/about.html', title='О нас')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Страница контактов"""
    form = ContactForm()
    
    if form.validate_on_submit():
        # Здесь можно добавить отправку email
        # или сохранение сообщения в БД
        
        log_user_action(
            form.email.data,
            'contact_form_submitted',
            f'Subject: {form.subject.data}'
        )
        
        flash('Спасибо за ваше сообщение! Мы свяжемся с вами в ближайшее время.', 'success')
        return redirect(url_for('main.contact'))
    
    return render_template('main/contact.html', title='Контакты', form=form)