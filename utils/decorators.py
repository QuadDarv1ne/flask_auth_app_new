"""
Декораторы для Flask приложения
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """
    Декоратор для ограничения доступа только администраторам
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Для доступа к этой странице необходимо войти в систему.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            flash('У вас нет прав доступа к этой странице.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def check_confirmed(f):
    """
    Декоратор для проверки подтверждения email
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if hasattr(current_user, 'email_confirmed') and not current_user.email_confirmed:
            flash('Пожалуйста, подтвердите ваш email адрес.', 'warning')
            return redirect(url_for('auth.unconfirmed'))
        
        return f(*args, **kwargs)
    return decorated_function


def anonymous_required(f):
    """
    Декоратор для страниц доступных только неавторизованным пользователям
    (например, страницы входа и регистрации)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            flash('Вы уже вошли в систему.', 'info')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function
