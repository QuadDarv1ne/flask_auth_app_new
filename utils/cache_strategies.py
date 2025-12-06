"""
Advanced caching strategies and cache warming
"""
import hashlib
import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Optional, Callable
import logging

logger = logging.getLogger('flask_auth_app.cache_strategies')


class CacheKey:
    """Генератор ключей кэша с поддержкой версионирования"""
    
    VERSION = 1
    
    @staticmethod
    def user(user_id: int) -> str:
        """Ключ для пользователя"""
        return f"v{CacheKey.VERSION}:user:{user_id}"
    
    @staticmethod
    def user_profile(user_id: int) -> str:
        """Ключ для профиля пользователя"""
        return f"v{CacheKey.VERSION}:profile:{user_id}"
    
    @staticmethod
    def user_sessions(user_id: int) -> str:
        """Ключ для сессий пользователя"""
        return f"v{CacheKey.VERSION}:sessions:{user_id}"
    
    @staticmethod
    def route_content(route: str) -> str:
        """Ключ для контента маршрута"""
        return f"v{CacheKey.VERSION}:route:{route}"
    
    @staticmethod
    def api_response(endpoint: str, params_hash: str) -> str:
        """Ключ для API ответа"""
        return f"v{CacheKey.VERSION}:api:{endpoint}:{params_hash}"
    
    @staticmethod
    def query_result(query_hash: str) -> str:
        """Ключ для результата запроса"""
        return f"v{CacheKey.VERSION}:query:{query_hash}"
    
    @staticmethod
    def stats(stat_type: str, period: str) -> str:
        """Ключ для статистики"""
        return f"v{CacheKey.VERSION}:stats:{stat_type}:{period}"
    
    @staticmethod
    def invalidation_tag(tag: str) -> str:
        """Тег для инвалидации групп кэша"""
        return f"v{CacheKey.VERSION}:tag:{tag}"


class CacheInvalidator:
    """Управление инвалидацией кэша с использованием тегов"""
    
    def __init__(self, cache):
        self.cache = cache
        self.tags = {}
    
    def register_key(self, key: str, *tags):
        """Зарегистрировать ключ с тегами для инвалидации"""
        for tag in tags:
            if tag not in self.tags:
                self.tags[tag] = []
            if key not in self.tags[tag]:
                self.tags[tag].append(key)
    
    def invalidate_by_tag(self, tag: str):
        """Инвалидировать все ключи по тегу"""
        if tag in self.tags:
            keys_to_delete = self.tags[tag]
            self.cache.delete(*keys_to_delete)
            del self.tags[tag]
            logger.info(f"Invalidated {len(keys_to_delete)} keys with tag '{tag}'")
    
    def invalidate_user(self, user_id: int):
        """Инвалидировать данные пользователя"""
        self.invalidate_by_tag(f"user:{user_id}")
    
    def invalidate_all_users(self):
        """Инвалидировать данные всех пользователей"""
        self.invalidate_by_tag("users")
    
    def invalidate_stats(self):
        """Инвалидировать кэш статистики"""
        self.invalidate_by_tag("stats")


class CacheWarmer:
    """Предварительное заполнение кэша при запуске приложения"""
    
    def __init__(self, app, cache):
        self.app = app
        self.cache = cache
    
    def warm_cache(self):
        """Заполнить кэш часто используемыми данными"""
        logger.info("Starting cache warming...")
        
        try:
            with self.app.app_context():
                # Кэширование статических данных
                self._warm_static_data()
                
                # Кэширование популярных пользователей
                self._warm_popular_users()
                
                # Кэширование конфигурации
                self._warm_config()
                
            logger.info("Cache warming completed successfully")
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
    
    def _warm_static_data(self):
        """Кэширование статических данных"""
        static_data = {
            'app_version': '2.1.0',
            'api_version': '1.0',
            'features': [
                'authentication',
                '2fa',
                'email',
                'websocket',
                'monitoring'
            ]
        }
        self.cache.set('app:static:data', static_data, timeout=86400)
        logger.debug("Static data cached")
    
    def _warm_popular_users(self):
        """Кэширование популярных пользователей"""
        from models import User
        
        # Получаем топ пользователей
        top_users = User.query.order_by(User.id).limit(10).all()
        
        for user in top_users:
            user_key = CacheKey.user(user.id)
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin
            }
            self.cache.set(user_key, user_data, timeout=3600)
        
        logger.debug(f"Warmed cache for {len(top_users)} users")
    
    def _warm_config(self):
        """Кэширование конфигурации"""
        config = {
            'max_upload_size': 16 * 1024 * 1024,
            'session_timeout': 3600,
            'password_min_length': 8,
            'cache_timeout': 300
        }
        self.cache.set('app:config', config, timeout=86400)
        logger.debug("Config cached")


class SmartCache:
    """Умное кэширование с автоматической инвалидацией и сжатием"""
    
    def __init__(self, cache):
        self.cache = cache
        self.invalidator = CacheInvalidator(cache)
    
    def set_with_tags(
        self,
        key: str,
        value: Any,
        timeout: int = 300,
        tags: list = None
    ):
        """Установить значение с тегами для инвалидации"""
        self.cache.set(key, value, timeout)
        
        if tags:
            for tag in tags:
                self.invalidator.register_key(key, tag)
        
        return True
    
    def get_or_compute(
        self,
        key: str,
        compute_func: Callable,
        timeout: int = 300,
        tags: list = None
    ):
        """Получить из кэша или вычислить"""
        # Попытка получить из кэша
        value = self.cache.get(key)
        
        if value is not None:
            logger.debug(f"Cache hit: {key}")
            return value
        
        # Вычисление значения
        logger.debug(f"Cache miss: {key}, computing...")
        value = compute_func()
        
        # Кэширование
        self.set_with_tags(key, value, timeout, tags)
        
        return value
    
    def mget_or_compute(
        self,
        keys: list,
        compute_func: Callable,
        timeout: int = 300
    ) -> dict:
        """Массовое получение с вычислением недостающих"""
        result = {}
        missing_keys = []
        
        # Получаем что есть в кэше
        for key in keys:
            value = self.cache.get(key)
            if value is not None:
                result[key] = value
            else:
                missing_keys.append(key)
        
        # Вычисляем недостающие
        if missing_keys:
            logger.debug(f"Computing {len(missing_keys)} missing keys")
            computed = compute_func(missing_keys)
            
            # Кэшируем результаты
            for key, value in computed.items():
                self.cache.set(key, value, timeout)
                result[key] = value
        
        return result


def cached_route(timeout: int = 300, key_prefix: str = 'route'):
    """Декоратор для кэширования маршрутов"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request, current_app
            
            # Пропускаем кэширование для POST/PUT/DELETE
            if request.method != 'GET':
                return f(*args, **kwargs)
            
            # Генерируем ключ кэша
            cache_key = f"{key_prefix}:{request.endpoint}:{request.query_string.decode()}"
            
            cache = current_app.extensions.get('cache')
            if not cache or not cache.is_available():
                return f(*args, **kwargs)
            
            # Пытаемся получить из кэша
            response = cache.get(cache_key)
            if response is not None:
                logger.debug(f"Route cache hit: {cache_key}")
                return response
            
            # Выполняем функцию
            response = f(*args, **kwargs)
            
            # Кэшируем результат
            cache.set(cache_key, response, timeout)
            
            return response
        
        return decorated_function
    return decorator


def cache_warming_decorator(cache_warmer):
    """Декоратор для запуска cache warming"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = f(*args, **kwargs)
            # Запускаем cache warming после создания app
            cache_warmer.warm_cache()
            return result
        return decorated_function
    return decorator
