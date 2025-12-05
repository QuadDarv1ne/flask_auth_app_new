"""
Оптимизация запросов и кэширование для базы данных
"""
from functools import wraps
import hashlib
import json
from datetime import timedelta


def generate_cache_key(*args, **kwargs):
    """Генерирует уникальный ключ для кэша."""
    key_data = {
        'args': str(args),
        'kwargs': str(sorted(kwargs.items()))
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached_query(cache, timeout=300):
    """Декоратор для кэширования результатов запроса."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"query:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # Попытка получить из кэша
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполнение функции
            result = func(*args, **kwargs)
            
            # Сохранение в кэш
            cache.set(cache_key, result, timeout=timeout)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(cache, *patterns):
    """Инвалидирует кэш по паттернам."""
    for pattern in patterns:
        # Получить все ключи, соответствующие паттерну
        keys = cache.keys(f"{pattern}*")
        if keys:
            cache.delete(*keys)


# Паттерны кэширования
CACHE_KEYS = {
    'user': 'user:{user_id}',
    'user_profile': 'user:profile:{user_id}',
    'user_2fa': 'user:2fa:{user_id}',
    'user_sessions': 'user:sessions:{user_id}',
    'all_users': 'users:all',
    'app_config': 'config:*',
}


class QueryOptimizer:
    """Оптимизирует запросы к БД с помощью кэширования и批处理."""
    
    def __init__(self, db, cache, logger):
        self.db = db
        self.cache = cache
        self.logger = logger
    
    def get_user_by_id(self, user_id, use_cache=True):
        """Получить пользователя по ID с кэшированием."""
        cache_key = CACHE_KEYS['user'].format(user_id=user_id)
        
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                self.logger.debug(f"Cache hit for user {user_id}")
                return cached
        
        user = self.db.session.query(User).filter_by(id=user_id).first()
        
        if user and use_cache:
            self.cache.set(cache_key, user, timeout=3600)
        
        return user
    
    def get_user_by_email(self, email, use_cache=True):
        """Получить пользователя по email с кэшированием."""
        cache_key = f"user:email:{hashlib.md5(email.encode()).hexdigest()}"
        
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                self.logger.debug(f"Cache hit for email {email}")
                return cached
        
        user = self.db.session.query(User).filter_by(email=email).first()
        
        if user and use_cache:
            self.cache.set(cache_key, user, timeout=3600)
        
        return user
    
    def invalidate_user_cache(self, user_id):
        """Инвалидирует кэш пользователя."""
        patterns = [
            CACHE_KEYS['user'].format(user_id=user_id),
            CACHE_KEYS['user_profile'].format(user_id=user_id),
            CACHE_KEYS['user_2fa'].format(user_id=user_id),
            CACHE_KEYS['user_sessions'].format(user_id=user_id),
        ]
        invalidate_cache(self.cache, *patterns)
    
    def batch_get_users(self, user_ids, use_cache=True):
        """Получить нескольких пользователей одним запросом."""
        if not user_ids:
            return []
        
        cached_users = {}
        uncached_ids = []
        
        if use_cache:
            for uid in user_ids:
                cache_key = CACHE_KEYS['user'].format(user_id=uid)
                cached = self.cache.get(cache_key)
                if cached:
                    cached_users[uid] = cached
                else:
                    uncached_ids.append(uid)
        else:
            uncached_ids = user_ids
        
        # Получить некэшированные пользователей
        if uncached_ids:
            users = self.db.session.query(User).filter(User.id.in_(uncached_ids)).all()
            for user in users:
                cached_users[user.id] = user
                if use_cache:
                    cache_key = CACHE_KEYS['user'].format(user_id=user.id)
                    self.cache.set(cache_key, user, timeout=3600)
        
        return [cached_users.get(uid) for uid in user_ids if uid in cached_users]
    
    def get_user_sessions(self, user_id):
        """Получить сессии пользователя с кэшированием."""
        cache_key = CACHE_KEYS['user_sessions'].format(user_id=user_id)
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        sessions = self.db.session.query(UserSession).filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        
        self.cache.set(cache_key, sessions, timeout=1800)
        return sessions
    
    def count_users(self):
        """Получить количество пользователей с кэшированием."""
        cache_key = "stats:total_users"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        count = self.db.session.query(User).count()
        self.cache.set(cache_key, count, timeout=3600)
        return count
    
    def get_active_sessions_count(self):
        """Получить количество активных сессий."""
        cache_key = "stats:active_sessions"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        count = self.db.session.query(UserSession).filter_by(is_active=True).count()
        self.cache.set(cache_key, count, timeout=300)
        return count


# Индексы БД для оптимизации
DATABASE_INDEXES = {
    'user': [
        'CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email)',
        'CREATE INDEX IF NOT EXISTS idx_user_username ON "user"(username)',
        'CREATE INDEX IF NOT EXISTS idx_user_created_at ON "user"(created_at)',
    ],
    'user_session': [
        'CREATE INDEX IF NOT EXISTS idx_session_user_id ON user_session(user_id)',
        'CREATE INDEX IF NOT EXISTS idx_session_is_active ON user_session(is_active)',
        'CREATE INDEX IF NOT EXISTS idx_session_created_at ON user_session(created_at)',
    ],
    'login_history': [
        'CREATE INDEX IF NOT EXISTS idx_login_user_id ON login_history(user_id)',
        'CREATE INDEX IF NOT EXISTS idx_login_created_at ON login_history(created_at)',
        'CREATE INDEX IF NOT EXISTS idx_login_ip_address ON login_history(ip_address)',
    ],
}


def create_database_indexes(db):
    """Создает индексы БД для оптимизации."""
    with db.engine.connect() as connection:
        for table, indexes in DATABASE_INDEXES.items():
            for index_sql in indexes:
                try:
                    connection.execute(index_sql)
                    connection.commit()
                except Exception as e:
                    print(f"Index creation warning: {e}")


# Аналитика запросов
class QueryAnalytics:
    """Анализирует и отслеживает производительность запросов."""
    
    def __init__(self, logger):
        self.logger = logger
        self.query_times = []
        self.slow_queries = []
    
    def track_query(self, query_name, duration, threshold=1000):
        """Отслеживает время выполнения запроса."""
        self.query_times.append({
            'name': query_name,
            'duration': duration
        })
        
        if duration > threshold:
            self.slow_queries.append({
                'name': query_name,
                'duration': duration,
                'timestamp': __import__('datetime').datetime.now()
            })
            self.logger.warning(f"Slow query detected: {query_name} ({duration}ms)")
    
    def get_stats(self):
        """Получить статистику запросов."""
        if not self.query_times:
            return {}
        
        durations = [q['duration'] for q in self.query_times]
        return {
            'total_queries': len(self.query_times),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'slow_queries_count': len(self.slow_queries)
        }
