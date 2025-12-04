import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

class Config:
    """Конфигурация приложения Flask"""
    
    # Секретный ключ для сессий и CSRF защиты
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-please-change-in-production'
    
    # Конфигурация базы данных
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Установить True для отладки SQL запросов
    
    # Flask-Login настройки
    REMEMBER_COOKIE_DURATION = 604800  # 7 дней в секундах
    REMEMBER_COOKIE_SECURE = False  # В продакшене поставить True (требует HTTPS)
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # В продакшене поставить True (требует HTTPS)
    
    # WTForms настройки
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # CSRF токен не истекает
    WTF_CSRF_SSL_STRICT = True  # Строгая проверка CSRF для HTTPS
    
    # Flask-Mail настройки
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@flaskauth.com'
    
    # URL приложения (для генерации ссылок в email)
    APP_URL = os.environ.get('APP_URL') or 'http://localhost:5000'
    
    # Настройки производительности
    CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT') or 300)  # 5 минут
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB максимальный размер загружаемых файлов
    
    # Дополнительные настройки безопасности
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Настройки для продакшена (установить в True когда будет HTTPS)
    FORCE_HTTPS = os.environ.get('FORCE_HTTPS', 'false').lower() in ['true', 'on', '1']
