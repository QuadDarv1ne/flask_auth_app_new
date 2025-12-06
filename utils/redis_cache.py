"""
Redis кэширование для Flask Auth App
"""
import redis
import pickle
import json
from functools import wraps
from typing import Any, Optional, Callable
import logging

logger = logging.getLogger('flask_auth_app.cache')


class RedisCache:
    """Обёртка для Redis с поддержкой кэширования."""
    
    def __init__(self, app=None):
        self.redis_client = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Инициализация Redis из конфига приложения."""
        redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        timeout = app.config.get('REDIS_SOCKET_CONNECT_TIMEOUT', 2)
        
        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=False,
                socket_connect_timeout=timeout,
                socket_timeout=timeout,
                retry_on_timeout=True
            )
            # Проверка соединения
            self.redis_client.ping()
            logger.info(f"✓ Redis connected: {redis_url}")
        except redis.ConnectionError as e:
            logger.warning(f"⚠ Redis connection failed (will use memory cache): {e}")
            self.redis_client = None
        except Exception as e:
            logger.warning(f"⚠ Redis initialization error: {e}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Проверка доступности Redis."""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша."""
        if not self.is_available():
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # Десериализация
            try:
                return json.loads(value)
            except:
                return pickle.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, timeout: int = 300):
        """Установить значение в кэш."""
        if not self.is_available():
            return False
        
        try:
            # Сериализация
            try:
                serialized = json.dumps(value)
            except:
                serialized = pickle.dumps(value)
            
            self.redis_client.setex(key, timeout, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, *keys):
        """Удалить ключи из кэша."""
        if not self.is_available() or not keys:
            return 0
        
        try:
            return self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Проверить существование ключа."""
        if not self.is_available():
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except:
            return False
    
    def keys(self, pattern: str = '*'):
        """Получить ключи по паттерну."""
        if not self.is_available():
            return []
        
        try:
            return [k.decode() if isinstance(k, bytes) else k 
                    for k in self.redis_client.keys(pattern)]
        except Exception as e:
            logger.error(f"Cache keys error: {e}")
            return []
    
    def clear(self, pattern: str = None):
        """Очистить кэш (все или по паттерну)."""
        if not self.is_available():
            return 0
        
        try:
            if pattern:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                return self.redis_client.flushdb()
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    def incr(self, key: str, amount: int = 1) -> int:
        """Увеличить счётчик."""
        if not self.is_available():
            return 0
        
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache incr error: {e}")
            return 0
    
    def expire(self, key: str, timeout: int):
        """Установить TTL для ключа."""
        if not self.is_available():
            return False
        
        try:
            return bool(self.redis_client.expire(key, timeout))
        except:
            return False


def cached(timeout: int = 300, key_prefix: str = 'view'):
    """
    Декоратор для кэширования результатов функций.
    
    Args:
        timeout: время жизни кэша в секундах
        key_prefix: префикс для ключа кэша
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Импортируем cache из текущего приложения
            from flask import current_app
            cache = current_app.extensions.get('cache')
            
            if not cache or not cache.is_available():
                return f(*args, **kwargs)
            
            # Генерация ключа
            cache_key = f"{key_prefix}:{f.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Попытка получить из кэша
            rv = cache.get(cache_key)
            if rv is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return rv
            
            # Выполнение функции
            rv = f(*args, **kwargs)
            
            # Сохранение в кэш
            cache.set(cache_key, rv, timeout)
            logger.debug(f"Cache set: {cache_key}")
            
            return rv
        
        return decorated_function
    return decorator


class SessionStore:
    """Хранилище сессий в Redis."""
    
    def __init__(self, cache: RedisCache, prefix: str = 'session'):
        self.cache = cache
        self.prefix = prefix
    
    def _make_key(self, session_id: str) -> str:
        """Создать ключ для сессии."""
        return f"{self.prefix}:{session_id}"
    
    def get(self, session_id: str) -> Optional[dict]:
        """Получить сессию."""
        return self.cache.get(self._make_key(session_id))
    
    def set(self, session_id: str, data: dict, timeout: int = 3600):
        """Сохранить сессию."""
        return self.cache.set(self._make_key(session_id), data, timeout)
    
    def delete(self, session_id: str):
        """Удалить сессию."""
        return self.cache.delete(self._make_key(session_id))
    
    def exists(self, session_id: str) -> bool:
        """Проверить существование сессии."""
        return self.cache.exists(self._make_key(session_id))
    
    def get_all_sessions(self, user_id: int) -> list:
        """Получить все сессии пользователя."""
        pattern = f"{self.prefix}:*"
        sessions = []
        
        for key in self.cache.keys(pattern):
            session = self.cache.get(key)
            if session and session.get('user_id') == user_id:
                sessions.append(session)
        
        return sessions
    
    def clear_user_sessions(self, user_id: int):
        """Очистить все сессии пользователя."""
        pattern = f"{self.prefix}:*"
        count = 0
        
        for key in self.cache.keys(pattern):
            session = self.cache.get(key)
            if session and session.get('user_id') == user_id:
                self.cache.delete(key)
                count += 1
        
        return count


class RateLimiter:
    """Rate limiting на основе Redis."""
    
    def __init__(self, cache: RedisCache):
        self.cache = cache
    
    def is_allowed(self, identifier: str, limit: int, period: int) -> bool:
        """
        Проверка rate limit.
        
        Args:
            identifier: уникальный идентификатор (IP, user_id и т.д.)
            limit: максимальное количество запросов
            period: период в секундах
        
        Returns:
            True если запрос разрешен, False если превышен лимит
        """
        if not self.cache.is_available():
            return True  # Если Redis недоступен, разрешаем
        
        key = f"ratelimit:{identifier}"
        
        try:
            current = self.cache.incr(key)
            
            if current == 1:
                # Первый запрос - устанавливаем TTL
                self.cache.expire(key, period)
            
            return current <= limit
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True
    
    def get_remaining(self, identifier: str, limit: int) -> int:
        """Получить количество оставшихся запросов."""
        if not self.cache.is_available():
            return limit
        
        key = f"ratelimit:{identifier}"
        current = int(self.cache.get(key) or 0)
        
        return max(0, limit - current)
    
    def reset(self, identifier: str):
        """Сбросить счётчик для идентификатора."""
        key = f"ratelimit:{identifier}"
        self.cache.delete(key)


# Инициализация глобального экземпляра
cache = RedisCache()
