from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, db
from forms import LoginForm, RegistrationForm, TwoFactorVerifyForm
from utils.email import send_confirmation_email
from utils.decorators import check_confirmed
from utils.metrics import increment_failed_logins, increment_successful_registrations
from app import limiter
import secrets
import pyotp

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
@limiter.limit("50 per hour")
def register():
    """Регистрация нового пользователя"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Проверка существующего пользователя
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Пользователь с таким email уже существует.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Создание нового пользователя
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            is_admin=False,
            email_confirmed=False
        )
        
        # Генерация токена подтверждения
        token = user.generate_email_confirm_token()
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Отправка email с подтверждением
            send_confirmation_email(user.email, token)
            
            # Увеличение счетчика успешных регистраций
            increment_successful_registrations()
            
            flash('Регистрация успешна! Проверьте ваш email для подтверждения.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration error: {e}')
            flash('Ошибка регистрации. Попробуйте еще раз.', 'danger')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
@limiter.limit("100 per hour")
def login():
    """Аутентификация пользователя"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and check_password_hash(user.password, form.password.data):
            if not user.email_confirmed:
                flash('Пожалуйста, подтвердите ваш email перед входом.', 'warning')
                return redirect(url_for('auth.unconfirmed'))
            
            # Check if 2FA is enabled
            if user.is_2fa_enabled:
                # Store user ID in session for 2FA verification
                session['2fa_user_id'] = user.id
                session['2fa_remember_me'] = form.remember_me.data
                return redirect(url_for('auth.verify_2fa'))
            
            # Regular login without 2FA
            login_user(user, remember=form.remember_me.data)
            user.update_last_login()
            next_page = request.args.get('next')
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            # Увеличение счетчика неудачных попыток входа
            increment_failed_logins()
            flash('Неверный email или пароль.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """Проверка 2FA кода"""
    # Check if user ID is in session
    user_id = session.get('2fa_user_id')
    if not user_id:
        flash('Необходимо сначала войти в систему.', 'warning')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    if not user:
        session.pop('2fa_user_id', None)
        flash('Ошибка аутентификации.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = TwoFactorVerifyForm()
    if form.validate_on_submit():
        # Verify TOTP token
        if user.verify_totp(str(form.token.data)):
            # Login user
            remember_me = session.get('2fa_remember_me', False)
            login_user(user, remember=remember_me)
            user.update_last_login()
            
            # Clear session
            session.pop('2fa_user_id', None)
            session.pop('2fa_remember_me', None)
            
            next_page = request.args.get('next')
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Неверный код 2FA.', 'danger')
    
    return render_template('auth/verify_2fa.html', form=form, user=user)

@auth_bp.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    """Подтверждение email по токену"""
    user = User.query.filter_by(email_confirm_token=token).first()
    
    if not user:
        flash('Неверный токен подтверждения.', 'danger')
        return redirect(url_for('auth.login'))
    
    user.confirm_email()
    flash('Ваш email успешно подтвержден!', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/unconfirmed')
@login_required
@check_confirmed
def unconfirmed():
    """Страница для неподтвержденных пользователей"""
    return render_template('auth/unconfirmed.html')

@auth_bp.route('/resend-confirmation')
@login_required
def resend_confirmation():
    """Повторная отправка email с подтверждением"""
    if current_user.email_confirmed:
        flash('Ваш email уже подтвержден.', 'info')
        return redirect(url_for('main.dashboard'))
    
    token = current_user.generate_email_confirm_token()
    send_confirmation_email(current_user.email, token)
    flash('Новое письмо с подтверждением отправлено на ваш email.', 'success')
    return redirect(url_for('auth.unconfirmed'))