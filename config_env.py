"""
Application configuration for different environments
"""
import os
from datetime import timedelta


class Config:
    """Base configuration."""
    
    # Secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    # Use absolute path for instance directory
    import os
    if not os.environ.get('DATABASE_URL'):
        instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(instance_dir, "app.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'timeout': 30},
    }
    
    # Session
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    REDIS_SOCKET_CONNECT_TIMEOUT = 2
    REDIS_SOCKET_TIMEOUT = 2
    
    # Fallback to memory storage if Redis is not available
    import redis
    try:
        # Try to connect to Redis
        r = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=REDIS_SOCKET_CONNECT_TIMEOUT, socket_timeout=REDIS_SOCKET_TIMEOUT)
        r.ping()
        REDIS_AVAILABLE = True
    except:
        REDIS_AVAILABLE = False
        # Use memory storage as fallback
        REDIS_URL = 'redis://localhost:6379/0'  # Still set the URL but it won't be used
        CACHE_TYPE = 'simple'  # Use simple cache instead of Redis
        RATELIMIT_STORAGE_URL = 'memory://'
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@example.com'
    
    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = REDIS_URL
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_DIR = 'logs'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 10
    
    # Security
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGITS = True
    PASSWORD_REQUIRE_SPECIAL = True
    
    # 2FA
    TWO_FACTOR_ENABLED = True
    TWO_FACTOR_ISSUER = 'Flask Auth App'
    
    # Cache
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    
    # WebSocket
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_LOGGER = True
    
    # API
    API_TITLE = 'Flask Auth App API'
    API_VERSION = '1.0'
    API_DESCRIPTION = 'RESTful API for Flask Auth App'


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = 'DEBUG'
    
    # Менее строгие требования для разработки
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True


class TestingConfig(Config):
    """Testing configuration."""
    
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    
    # Упрощённые требования для тестов
    PASSWORD_MIN_LENGTH = 4
    PASSWORD_REQUIRE_UPPERCASE = False
    PASSWORD_REQUIRE_LOWERCASE = False
    PASSWORD_REQUIRE_DIGITS = False
    PASSWORD_REQUIRE_SPECIAL = False


class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Строгие настройки безопасности для продакшна
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Обязательные переменные окружения
    SECRET_KEY = os.environ.get('SECRET_KEY', 'prod-secret-key-must-be-set')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///instance/app_prod.db')
    
    # Продакшн логирование
    LOG_LEVEL = 'WARNING'


class StagingConfig(ProductionConfig):
    """Staging configuration."""
    
    DEBUG = True
    LOG_LEVEL = 'INFO'


# Словарь конфигураций
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'staging': StagingConfig,
    'default': DevelopmentConfig
}


def get_config(env = None) -> Config:
    """
    Получить конфигурацию для окружения.
    
    Args:
        env: окружение (development, testing, production, staging) или класс конфигурации
    
    Returns:
        экземпляр конфигурации
    """
    # If env is a Config class, return it directly
    if env is not None and isinstance(env, type):
        # Check if it's a subclass of any Config class
        import config as config_module
        if issubclass(env, (Config, config_module.Config)):
            return env
    
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(env, config['default'])
