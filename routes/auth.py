from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import db
from models import User
from forms import LoginForm, RegistrationForm
from utils.logging import log_user_action, log_security_event

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа в систему"""
    form = LoginForm()
    
    if form.validate_on_submit():
        # Поиск пользователя в базе данных
        user = User.query.filter_by(username=form.username.data).first()
        
        # Проверка пользователя и пароля
        if user is None or not user.check_password(form.password.data):
            log_security_event(
                'failed_login',
                username=form.username.data,
                ip_address=request.remote_addr,
                details='Invalid username or password'
            )
            flash('Неверное имя пользователя или пароль', 'error')
            return redirect(url_for('auth.login'))
        
        # Вход пользователя
        login_user(user, remember=form.remember_me.data)
        user.update_last_login()
        
        # Логирование успешного входа
        log_user_action(
            user.username,
            'logged_in',
            f'IP: {request.remote_addr}, Remember: {form.remember_me.data}'
        )
        
        flash(f'Добро пожаловать, {user.username}!', 'success')
        
        # Перенаправление на страницу, с которой пользователь пришел
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Вход', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации нового пользователя"""
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Создание нового пользователя
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        # Сохранение в базу данных
        db.session.add(user)
        db.session.commit()
        
        # Логирование регистрации
        log_user_action(
            user.username, 
            'registered', 
            f'Email: {user.email}, IP: {request.remote_addr}'
        )
        
        flash('Поздравляем! Вы успешно зарегистрированы.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Регистрация', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    username = current_user.username if hasattr(current_user, 'username') else 'Unknown'
    log_user_action(username, 'logged_out', f'IP: {request.remote_addr}')
    
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.index'))
