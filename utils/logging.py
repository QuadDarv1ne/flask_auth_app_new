"""
Утилиты для логирования приложения
"""
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime


def setup_logging(app):
    """
    Настройка системы логирования приложения
    """
    if not app.debug:
        # Создаем директорию для логов
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Настройка файлового обработчика с ротацией
        file_handler = RotatingFileHandler(
            'logs/flask_auth.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        # Формат логов
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # Добавляем обработчик к логгеру приложения
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Flask Auth App startup')


def log_user_action(username, action, details=''):
    """
    Логирование действий пользователей
    
    Args:
        username: Имя пользователя
        action: Выполненное действие
        details: Дополнительные детали
    """
    from flask import current_app
    
    log_message = f"User '{username}' - {action}"
    if details:
        log_message += f" | Details: {details}"
    
    current_app.logger.info(log_message)


def log_security_event(event_type, username='', ip_address='', details=''):
    """
    Логирование событий безопасности
    
    Args:
        event_type: Тип события (failed_login, suspicious_activity, etc.)
        username: Имя пользователя
        ip_address: IP адрес
        details: Дополнительные детали
    """
    from flask import current_app
    
    log_message = f"SECURITY EVENT: {event_type}"
    if username:
        log_message += f" | User: {username}"
    if ip_address:
        log_message += f" | IP: {ip_address}"
    if details:
        log_message += f" | Details: {details}"
    
    current_app.logger.warning(log_message)


class RequestLogger:
    """
    Middleware для логирования HTTP запросов
    """
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        """
        Логирование каждого запроса
        """
        from flask import request
        
        # Логируем запрос
        self.app.logger.debug(
            f"{environ.get('REQUEST_METHOD')} {environ.get('PATH_INFO')} "
            f"from {environ.get('REMOTE_ADDR')}"
        )
        
        return self.app(environ, start_response)
