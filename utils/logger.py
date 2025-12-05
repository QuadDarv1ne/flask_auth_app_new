"""
Логирование и мониторинг приложения Flask Auth App
"""
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


# Создание директории для логов
LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)


def setup_logging(app):
    """Инициализация логирования приложения."""
    
    # Уровень логирования из config
    log_level = app.config.get('LOG_LEVEL', logging.INFO)
    
    # Форматтер логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Логер приложения
    logger = logging.getLogger('flask_auth_app')
    logger.setLevel(log_level)
    
    # Очистка существующих handlers
    logger.handlers = []
    
    # Файловый handler (ротация по размеру)
    log_file = LOG_DIR / 'app.log'
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Консольный handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Отдельный логер для ошибок
    error_log_file = LOG_DIR / 'errors.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10485760,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # Логер для безопасности
    security_logger = logging.getLogger('flask_auth_app.security')
    security_log_file = LOG_DIR / 'security.log'
    security_handler = logging.handlers.RotatingFileHandler(
        security_log_file,
        maxBytes=5242880,  # 5MB
        backupCount=10
    )
    security_handler.setFormatter(formatter)
    security_logger.addHandler(security_handler)
    
    # Логер для БД
    db_logger = logging.getLogger('flask_auth_app.database')
    db_log_file = LOG_DIR / 'database.log'
    db_handler = logging.handlers.RotatingFileHandler(
        db_log_file,
        maxBytes=5242880,
        backupCount=5
    )
    db_handler.setFormatter(formatter)
    db_logger.addHandler(db_handler)
    
    # Отключение отладочных логов внешних библиотек в production
    if app.config.get('ENV') == 'production':
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('flask').setLevel(logging.WARNING)
    
    return logger, security_logger, db_logger


class AppLogger:
    """Удобный класс для логирования."""
    
    def __init__(self, app):
        self.app = app
        self.logger, self.security_logger, self.db_logger = setup_logging(app)
    
    def info(self, message):
        """Логирование информационного сообщения."""
        self.logger.info(message)
    
    def warning(self, message):
        """Логирование предупреждения."""
        self.logger.warning(message)
    
    def error(self, message, exc_info=False):
        """Логирование ошибки."""
        self.logger.error(message, exc_info=exc_info)
    
    def debug(self, message):
        """Логирование отладочного сообщения."""
        self.logger.debug(message)
    
    def security_event(self, event_type, user_id=None, details=None):
        """Логирование события безопасности."""
        message = f"[SECURITY] {event_type}"
        if user_id:
            message += f" | User: {user_id}"
        if details:
            message += f" | Details: {details}"
        self.security_logger.warning(message)
    
    def login_attempt(self, email, success, ip_address=None):
        """Логирование попытки входа."""
        status = "успешен" if success else "неудачен"
        message = f"Login attempt {status} | Email: {email}"
        if ip_address:
            message += f" | IP: {ip_address}"
        self.security_logger.info(message)
    
    def unauthorized_access(self, resource, user_id=None, ip_address=None):
        """Логирование попытки несанкционированного доступа."""
        message = f"Unauthorized access attempt | Resource: {resource}"
        if user_id:
            message += f" | User: {user_id}"
        if ip_address:
            message += f" | IP: {ip_address}"
        self.security_logger.warning(message)
    
    def database_query(self, query_type, table=None, duration=None):
        """Логирование запроса к БД."""
        message = f"DB {query_type.upper()}"
        if table:
            message += f" | Table: {table}"
        if duration:
            message += f" | Duration: {duration}ms"
        self.db_logger.debug(message)
    
    def database_error(self, query_type, table=None, error=None):
        """Логирование ошибки БД."""
        message = f"DB ERROR: {query_type.upper()}"
        if table:
            message += f" | Table: {table}"
        if error:
            message += f" | Error: {error}"
        self.db_logger.error(message)


# Контекстный menager для логирования времени выполнения
import time
from contextlib import contextmanager


@contextmanager
def log_execution_time(logger, operation_name):
    """Контекстный менеджер для логирования времени выполнения."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = (time.time() - start_time) * 1000  # Время в миллисекундах
        if duration > 1000:  # Логировать только операции > 1 сек
            logger.warning(f"{operation_name} took {duration:.2f}ms")
        else:
            logger.debug(f"{operation_name} took {duration:.2f}ms")


# Декоратор для логирования функций
def log_function(logger=None, level='info'):
    """Декоратор для логирования вызовов функций."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = logging.getLogger('flask_auth_app')
            
            log_func = getattr(logger, level, logger.info)
            func_name = f"{func.__module__}.{func.__name__}"
            
            log_func(f"Calling {func_name}")
            try:
                result = func(*args, **kwargs)
                log_func(f"Completed {func_name}")
                return result
            except Exception as e:
                logger.error(f"Error in {func_name}: {str(e)}", exc_info=True)
                raise
        
        return wrapper
    return decorator
