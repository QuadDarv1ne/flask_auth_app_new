"""
Утилиты для повышения производительности приложения
"""
from functools import wraps
from flask import request, jsonify, current_app
import hashlib
import time
import json
import pickle


# Простой in-memory кэш (для продакшена использовать Redis)
_cache = {}
_cache_timestamps = {}

# Попытка импортировать Redis для продакшена
try:
    import redis
    _redis_client = None
    _redis_available = True
except ImportError:
    _redis_client = None
    _redis_available = False


def get_redis_client():
    """Получение клиента Redis"""
    global _redis_client
    if _redis_client is None and _redis_available:
        try:
            _redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
            # Проверяем соединение
            _redis_client.ping()
        except:
            _redis_client = None
    return _redis_client

def cache_response(timeout=300, use_redis=True):
    """
    Декоратор для кэширования ответов
    
    Args:
        timeout: Время жизни кэша в секундах (по умолчанию 5 минут)
        use_redis: Использовать Redis для кэширования (если доступен)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Создаем ключ кэша на основе URL и аргументов
            cache_key = hashlib.md5(
                f"{request.url}{str(args)}{str(kwargs)}".encode()
            ).hexdigest()
            
            # Проверяем Redis кэш если доступен
            if use_redis and _redis_available:
                redis_client = get_redis_client()
                if redis_client:
                    try:
                        cached_data = redis_client.get(cache_key)
                        if cached_data:
                            # Десериализуем данные
                            return pickle.loads(cached_data)
                    except Exception as e:
                        # В случае ошибки Redis, используем in-memory кэш
                        current_app.logger.warning(f"Redis cache error: {e}")
            
            # Проверяем in-memory кэш
            if cache_key in _cache:
                timestamp = _cache_timestamps.get(cache_key, 0)
                if time.time() - timestamp < timeout:
                    return _cache[cache_key]
            
            # Выполняем функцию и кэшируем результат
            response = f(*args, **kwargs)
            
            # Сохраняем в Redis если доступен
            if use_redis and _redis_available:
                redis_client = get_redis_client()
                if redis_client:
                    try:
                        # Сериализуем данные
                        serialized_data = pickle.dumps(response)
                        redis_client.setex(cache_key, timeout, serialized_data)
                    except Exception as e:
                        current_app.logger.warning(f"Redis cache set error: {e}")
            
            # Сохраняем в in-memory кэш
            _cache[cache_key] = response
            _cache_timestamps[cache_key] = time.time()
            
            return response
        return decorated_function
    return decorator


def clear_cache(pattern=None):
    """
    Очистка кэша
    
    Args:
        pattern: Шаблон для выборочной очистки (опционально)
    """
    global _cache, _cache_timestamps
    
    # Очистка Redis кэша если доступен
    if _redis_available:
        redis_client = get_redis_client()
        if redis_client:
            try:
                if pattern is None:
                    redis_client.flushdb()
                else:
                    # Получаем все ключи по паттерну
                    keys = redis_client.keys(f"*{pattern}*")
                    if keys:
                        redis_client.delete(*keys)
            except Exception as e:
                current_app.logger.warning(f"Redis cache clear error: {e}")
    
    # Очистка in-memory кэша
    if pattern is None:
        _cache.clear()
        _cache_timestamps.clear()
    else:
        keys_to_delete = [k for k in _cache.keys() if pattern in k]
        for key in keys_to_delete:
            del _cache[key]
            if key in _cache_timestamps:
                del _cache_timestamps[key]


def rate_limit(max_requests=10, window=60):
    """
    Простой rate limiting декоратор
    
    Args:
        max_requests: Максимальное количество запросов
        window: Временное окно в секундах
    """
    requests_dict = {}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Получаем IP адрес клиента
            client_ip = request.remote_addr
            current_time = time.time()
            
            # Инициализируем запись для нового IP
            if client_ip not in requests_dict:
                requests_dict[client_ip] = []
            
            # Удаляем старые запросы
            requests_dict[client_ip] = [
                req_time for req_time in requests_dict[client_ip]
                if current_time - req_time < window
            ]
            
            # Проверяем лимит
            if len(requests_dict[client_ip]) >= max_requests:
                return jsonify({
                    'error': 'Too many requests',
                    'message': f'Максимум {max_requests} запросов за {window} секунд'
                }), 429
            
            # Добавляем текущий запрос
            requests_dict[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


class QueryCounter:
    """
    Утилита для подсчета количества SQL запросов
    Полезна для оптимизации производительности
    """
    def __init__(self, app=None):
        self.queries = []
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Инициализация с приложением Flask"""
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            self.queries.append({
                'statement': statement,
                'parameters': parameters,
                'time': time.time()
            })
        
        @app.before_request
        def before_request():
            self.queries = []
        
        @app.after_request
        def after_request(response):
            if app.debug:
                query_count = len(self.queries)
                if query_count > 10:
                    app.logger.warning(
                        f'High number of queries: {query_count} for {request.path}'
                    )
            return response
    
    def get_query_count(self):
        """Получить количество выполненных запросов"""
        return len(self.queries)
    
    def get_queries(self):
        """Получить список всех запросов"""
        return self.queries


def cache_data(key, timeout=300, use_redis=True):
    """
    Декоратор для кэширования результатов функции
    
    Args:
        key: Ключ кэша
        timeout: Время жизни кэша в секундах
        use_redis: Использовать Redis для кэширования (если доступен)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Генерируем ключ кэша
            cache_key = f"data:{key}"
            
            # Проверяем Redis кэш если доступен
            if use_redis and _redis_available:
                redis_client = get_redis_client()
                if redis_client:
                    try:
                        cached_data = redis_client.get(cache_key)
                        if cached_data:
                            # Десериализуем данные
                            return pickle.loads(cached_data)
                    except Exception as e:
                        current_app.logger.warning(f"Redis cache error: {e}")
            
            # Проверяем in-memory кэш
            if cache_key in _cache:
                timestamp = _cache_timestamps.get(cache_key, 0)
                if time.time() - timestamp < timeout:
                    return _cache[cache_key]
            
            # Выполняем функцию и кэшируем результат
            result = f(*args, **kwargs)
            
            # Сохраняем в Redis если доступен
            if use_redis and _redis_available:
                redis_client = get_redis_client()
                if redis_client:
                    try:
                        # Сериализуем данные
                        serialized_data = pickle.dumps(result)
                        redis_client.setex(cache_key, timeout, serialized_data)
                    except Exception as e:
                        current_app.logger.warning(f"Redis cache set error: {e}")
            
            # Сохраняем в in-memory кэш
            _cache[cache_key] = result
            _cache_timestamps[cache_key] = time.time()
            
            return result
        return decorated_function
    return decorator

def optimize_images(max_width=1920, max_height=1080, quality=85):
    """
    Декоратор для оптимизации загружаемых изображений
    
    Args:
        max_width: Максимальная ширина
        max_height: Максимальная высота
        quality: Качество сжатия (1-100)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from PIL import Image
            from io import BytesIO
            
            if 'file' in request.files:
                file = request.files['file']
                if file and file.filename:
                    try:
                        # Открываем изображение
                        img = Image.open(file)
                        
                        # Изменяем размер если нужно
                        if img.width > max_width or img.height > max_height:
                            img.thumbnail((max_width, max_height), Image.LANCZOS)
                        
                        # Сохраняем оптимизированное изображение
                        output = BytesIO()
                        img.save(output, format=img.format, quality=quality, optimize=True)
                        output.seek(0)
                        
                        # Заменяем файл на оптимизированный
                        request.files['file'] = output
                    except Exception as e:
                        # Если не удалось обработать, продолжаем с оригиналом
                        pass
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
