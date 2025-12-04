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
    
    # Flask-Login настройки
    REMEMBER_COOKIE_DURATION = 604800  # 7 дней в секундах
    REMEMBER_COOKIE_SECURE = False  # В продакшене поставить True (требует HTTPS)
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # В продакшене поставить True (требует HTTPS)
    
    # WTForms настройки
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # CSRF токен не истекает
