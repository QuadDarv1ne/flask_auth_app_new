"""Модуль дополнительных функций безопасности"""

import hashlib
import secrets
import time
from functools import wraps
from flask import request, current_app, abort, session
from flask_login import current_user


def generate_secure_token(length=32):
    """Генерация криптографически безопасного токена"""
    return secrets.token_urlsafe(length)


def hash_sensitive_data(data):
    """Хеширование чувствительных данных"""
    return hashlib.sha256(data.encode()).hexdigest()


def rate_limit_sensitive_operations(max_attempts=5, window=300):
    """
    Декоратор для ограничения частоты чувствительных операций
    
    Args:
        max_attempts: Максимальное количество попыток
        window: Временное окно в секундах
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Создаем ключ на основе IP и типа операции
            operation_key = f"sensitive_op_{request.remote_addr}_{f.__name__}"
            
            # Получаем или инициализируем данные по операции
            if 'rate_limits' not in session:
                session['rate_limits'] = {}
            
            now = time.time()
            operation_data = session['rate_limits'].get(operation_key, {
                'attempts': 0,
                'last_attempt': 0
            })
            
            # Очищаем старые попытки
            if now - operation_data['last_attempt'] > window:
                operation_data['attempts'] = 0
            
            # Проверяем лимит
            if operation_data['attempts'] >= max_attempts:
                current_app.logger.warning(
                    f"Rate limit exceeded for sensitive operation {f.__name__} "
                    f"from IP {request.remote_addr}"
                )
                abort(429, "Слишком много попыток. Попробуйте позже.")
            
            # Увеличиваем счетчик попыток
            operation_data['attempts'] += 1
            operation_data['last_attempt'] = now
            session['rate_limits'][operation_key] = operation_data
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_password_confirmation(f):
    """
    Декоратор для операций, требующих подтверждения паролем
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Для чувствительных операций требуется повторный ввод пароля
        # Эта проверка должна выполняться в самих маршрутах
        return f(*args, **kwargs)
    return decorated_function


def sanitize_input(input_string):
    """
    Базовая санитизация входных данных
    """
    if not isinstance(input_string, str):
        return input_string
    
    # Удаляем потенциально опасные символы
    dangerous_chars = ['<', '>', '&lt;', '&gt;', 'javascript:', 'vbscript:']
    sanitized = input_string
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()


def validate_password_strength(password):
    """
    Проверка сложности пароля
    
    Args:
        password: Пароль для проверки
        
    Returns:
        tuple: (is_valid, message)
    """
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"
    
    if not any(c.isupper() for c in password):
        return False, "Пароль должен содержать хотя бы одну заглавную букву"
    
    if not any(c.islower() for c in password):
        return False, "Пароль должен содержать хотя бы одну строчную букву"
    
    if not any(c.isdigit() for c in password):
        return False, "Пароль должен содержать хотя бы одну цифру"
    
    return True, "Пароль соответствует требованиям"


def detect_suspicious_activity(activity_type, details=''):
    """
    Логирование подозрительной активности
    
    Args:
        activity_type: Тип активности
        details: Дополнительные детали
    """
    from utils.logging import log_security_event
    
    ip_address = request.remote_addr
    username = getattr(current_user, 'username', 'anonymous')
    
    log_security_event(
        event_type=activity_type,
        username=username,
        ip_address=ip_address,
        details=details
    )
    
    # Можно добавить дополнительные меры, например:
    # - Блокировку IP
    # - Уведомление администратора
    # - Требование дополнительной аутентификации


def is_safe_redirect_url(url, allowed_hosts=None):
    """
    Проверка, что URL перенаправления безопасен
    
    Args:
        url: URL для проверки
        allowed_hosts: Список разрешенных хостов
        
    Returns:
        bool: True если URL безопасен
    """
    from urllib.parse import urlparse
    
    if not url:
        return False
    
    if allowed_hosts is None:
        allowed_hosts = [request.host]
    
    parsed = urlparse(url)
    
    # Разрешаем относительные URL
    if not parsed.netloc:
        return True
    
    # Проверяем, что хост в списке разрешенных
    return parsed.netloc in allowed_hosts