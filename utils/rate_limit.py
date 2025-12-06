"""
API rate limiting middleware
"""
from functools import wraps
from flask import request, jsonify, g
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('flask_auth_app.ratelimit')


class RateLimitExceeded(Exception):
    """Исключение при превышении rate limit."""
    pass


class RateLimitStorage:
    """Хранилище для rate limiting."""
    
    def __init__(self):
        self.storage = {}
    
    def get(self, key: str) -> dict:
        """Получить данные по ключу."""
        if key in self.storage:
            data = self.storage[key]
            # Очистка устаревших записей
            if data['reset_time'] < datetime.utcnow():
                del self.storage[key]
                return None
            return data
        return None
    
    def set(self, key: str, count: int, reset_time: datetime):
        """Установить данные."""
        self.storage[key] = {
            'count': count,
            'reset_time': reset_time
        }
    
    def increment(self, key: str) -> int:
        """Увеличить счётчик."""
        data = self.get(key)
        if data:
            data['count'] += 1
            self.storage[key] = data
            return data['count']
        return 0
    
    def clear_expired(self):
        """Очистить устаревшие записи."""
        now = datetime.utcnow()
        expired = [k for k, v in self.storage.items() if v['reset_time'] < now]
        for key in expired:
            del self.storage[key]


class RateLimit:
    """Rate limiting для API endpoints."""
    
    def __init__(self, app=None):
        self.storage = RateLimitStorage()
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Инициализация с Flask app."""
        app.config.setdefault('RATELIMIT_ENABLED', True)
        app.config.setdefault('RATELIMIT_STORAGE', self.storage)
        
        @app.before_request
        def check_rate_limit():
            """Проверка rate limit перед каждым запросом."""
            if not app.config['RATELIMIT_ENABLED']:
                return
            
            # Пропускаем статические файлы
            if request.endpoint and request.endpoint.startswith('static'):
                return
    
    def limit(
        self,
        max_requests: int = 100,
        window: int = 60,
        per: str = 'ip',
        message: str = None
    ):
        """
        Декоратор для ограничения запросов.
        
        Args:
            max_requests: максимальное количество запросов
            window: временное окно в секундах
            per: по чему ограничивать ('ip', 'user', 'endpoint')
            message: кастомное сообщение об ошибке
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Определяем ключ для rate limiting
                if per == 'ip':
                    identifier = request.remote_addr
                elif per == 'user':
                    from flask_login import current_user
                    identifier = str(current_user.id) if current_user.is_authenticated else request.remote_addr
                elif per == 'endpoint':
                    identifier = f"{request.endpoint}:{request.remote_addr}"
                else:
                    identifier = request.remote_addr
                
                key = f"ratelimit:{identifier}:{f.__name__}"
                
                # Получаем или создаём запись
                data = self.storage.get(key)
                now = datetime.utcnow()
                
                if data is None:
                    # Первый запрос в окне
                    reset_time = now + timedelta(seconds=window)
                    self.storage.set(key, 1, reset_time)
                    remaining = max_requests - 1
                    reset_timestamp = int(reset_time.timestamp())
                else:
                    # Проверяем лимит
                    if data['count'] >= max_requests:
                        # Лимит превышен
                        reset_timestamp = int(data['reset_time'].timestamp())
                        retry_after = (data['reset_time'] - now).total_seconds()
                        
                        logger.warning(
                            f"Rate limit exceeded for {identifier} on {f.__name__}: "
                            f"{data['count']}/{max_requests} requests"
                        )
                        
                        error_message = message or "Rate limit exceeded. Please try again later."
                        
                        response = jsonify({
                            'error': 'rate_limit_exceeded',
                            'message': error_message,
                            'retry_after': int(retry_after),
                            'reset_at': reset_timestamp
                        })
                        response.status_code = 429
                        response.headers['X-RateLimit-Limit'] = str(max_requests)
                        response.headers['X-RateLimit-Remaining'] = '0'
                        response.headers['X-RateLimit-Reset'] = str(reset_timestamp)
                        response.headers['Retry-After'] = str(int(retry_after))
                        
                        return response
                    
                    # Увеличиваем счётчик
                    count = self.storage.increment(key)
                    remaining = max_requests - count
                    reset_timestamp = int(data['reset_time'].timestamp())
                
                # Выполняем функцию
                result = f(*args, **kwargs)
                
                # Добавляем заголовки rate limit
                if hasattr(result, 'headers'):
                    result.headers['X-RateLimit-Limit'] = str(max_requests)
                    result.headers['X-RateLimit-Remaining'] = str(remaining)
                    result.headers['X-RateLimit-Reset'] = str(reset_timestamp)
                
                return result
            
            return decorated_function
        return decorator


# Глобальный экземпляр
rate_limit = RateLimit()


# Предустановленные лимиты
def limit_strict(f):
    """Строгий лимит: 10 запросов в минуту."""
    return rate_limit.limit(max_requests=10, window=60)(f)


def limit_moderate(f):
    """Умеренный лимит: 30 запросов в минуту."""
    return rate_limit.limit(max_requests=30, window=60)(f)


def limit_relaxed(f):
    """Мягкий лимит: 100 запросов в минуту."""
    return rate_limit.limit(max_requests=100, window=60)(f)


def limit_auth(f):
    """Лимит для аутентификации: 5 попыток в 5 минут."""
    return rate_limit.limit(
        max_requests=5,
        window=300,
        message="Too many authentication attempts. Please try again in 5 minutes."
    )(f)
