"""
Система мониторинга и метрик приложения
"""
import time
import psutil
import os
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
from flask import request, g
import logging

logger = logging.getLogger('flask_auth_app.monitoring')


class MetricsCollector:
    """Сборщик метрик приложения."""
    
    def __init__(self):
        self.request_count = defaultdict(int)
        self.request_duration = defaultdict(list)
        self.error_count = defaultdict(int)
        self.status_codes = defaultdict(int)
        self.endpoint_calls = defaultdict(int)
        self.user_activity = defaultdict(int)
        self.cache_stats = {'hits': 0, 'misses': 0}
        self.db_query_stats = {'count': 0, 'total_time': 0, 'slow_queries': []}
    
    def record_request(self, endpoint: str, method: str, duration: float, status_code: int):
        """Записать метрики запроса."""
        key = f"{method}:{endpoint}"
        self.request_count[key] += 1
        self.request_duration[key].append(duration)
        self.status_codes[status_code] += 1
        self.endpoint_calls[endpoint] += 1
        
        if status_code >= 400:
            self.error_count[key] += 1
    
    def record_user_activity(self, user_id: int):
        """Записать активность пользователя."""
        self.user_activity[user_id] += 1
    
    def record_cache_hit(self):
        """Записать cache hit."""
        self.cache_stats['hits'] += 1
    
    def record_cache_miss(self):
        """Записать cache miss."""
        self.cache_stats['misses'] += 1
    
    def record_db_query(self, duration: float):
        """Записать метрики DB запроса."""
        self.db_query_stats['count'] += 1
        self.db_query_stats['total_time'] += duration
        
        # Записываем медленные запросы (> 100ms)
        if duration > 0.1:
            self.db_query_stats['slow_queries'].append({
                'duration': duration,
                'timestamp': datetime.utcnow()
            })
            
            # Храним только последние 100 медленных запросов
            if len(self.db_query_stats['slow_queries']) > 100:
                self.db_query_stats['slow_queries'].pop(0)
    
    def get_stats(self) -> dict:
        """Получить статистику."""
        total_requests = sum(self.request_count.values())
        total_errors = sum(self.error_count.values())
        
        # Средняя длительность запросов
        avg_duration = {}
        for key, durations in self.request_duration.items():
            if durations:
                avg_duration[key] = sum(durations) / len(durations)
        
        # Cache hit rate
        cache_total = self.cache_stats['hits'] + self.cache_stats['misses']
        cache_hit_rate = (self.cache_stats['hits'] / cache_total * 100) if cache_total > 0 else 0
        
        # DB query stats
        avg_query_time = (self.db_query_stats['total_time'] / self.db_query_stats['count']
                         if self.db_query_stats['count'] > 0 else 0)
        
        return {
            'requests': {
                'total': total_requests,
                'by_endpoint': dict(self.endpoint_calls),
                'by_method_endpoint': dict(self.request_count),
            },
            'errors': {
                'total': total_errors,
                'by_endpoint': dict(self.error_count),
                'error_rate': (total_errors / total_requests * 100) if total_requests > 0 else 0,
            },
            'performance': {
                'avg_duration': avg_duration,
                'status_codes': dict(self.status_codes),
            },
            'cache': {
                'hits': self.cache_stats['hits'],
                'misses': self.cache_stats['misses'],
                'hit_rate': cache_hit_rate,
            },
            'database': {
                'query_count': self.db_query_stats['count'],
                'avg_query_time': avg_query_time,
                'slow_queries_count': len(self.db_query_stats['slow_queries']),
            },
            'users': {
                'active_count': len(self.user_activity),
                'top_active': sorted(
                    self.user_activity.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
            }
        }
    
    def reset(self):
        """Сбросить все метрики."""
        self.__init__()


class SystemMonitor:
    """Мониторинг системных ресурсов."""
    
    @staticmethod
    def get_cpu_usage() -> float:
        """Получить использование CPU."""
        return psutil.cpu_percent(interval=1)
    
    @staticmethod
    def get_memory_usage() -> dict:
        """Получить использование памяти."""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent,
        }
    
    @staticmethod
    def get_disk_usage(path: str = '/') -> dict:
        """Получить использование диска."""
        try:
            disk = psutil.disk_usage(path)
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent,
            }
        except:
            return {}
    
    @staticmethod
    def get_process_info() -> dict:
        """Получить информацию о текущем процессе."""
        process = psutil.Process(os.getpid())
        
        return {
            'pid': process.pid,
            'cpu_percent': process.cpu_percent(interval=0.1),
            'memory_info': process.memory_info()._asdict(),
            'num_threads': process.num_threads(),
            'create_time': datetime.fromtimestamp(process.create_time()),
        }
    
    @staticmethod
    def get_all_metrics() -> dict:
        """Получить все системные метрики."""
        return {
            'cpu': SystemMonitor.get_cpu_usage(),
            'memory': SystemMonitor.get_memory_usage(),
            'disk': SystemMonitor.get_disk_usage(),
            'process': SystemMonitor.get_process_info(),
            'timestamp': datetime.utcnow().isoformat(),
        }


class HealthCheck:
    """Проверка здоровья приложения."""
    
    def __init__(self, app=None):
        self.app = app
        self.checks = {}
    
    def register_check(self, name: str, check_func: callable):
        """Зарегистрировать проверку."""
        self.checks[name] = check_func
    
    def run_checks(self) -> dict:
        """Запустить все проверки."""
        results = {}
        all_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                result = check_func()
                results[name] = {
                    'status': 'healthy' if result else 'unhealthy',
                    'checked_at': datetime.utcnow().isoformat(),
                }
                if not result:
                    all_healthy = False
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'error': str(e),
                    'checked_at': datetime.utcnow().isoformat(),
                }
                all_healthy = False
        
        return {
            'status': 'healthy' if all_healthy else 'unhealthy',
            'checks': results,
            'timestamp': datetime.utcnow().isoformat(),
        }


def monitor_request(metrics_collector: MetricsCollector):
    """Декоратор для мониторинга запросов."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Начало запроса
            start_time = time.time()
            g.start_time = start_time
            
            # Выполнение функции
            response = f(*args, **kwargs)
            
            # Конец запроса
            duration = time.time() - start_time
            
            # Запись метрик
            endpoint = request.endpoint or 'unknown'
            method = request.method
            status_code = getattr(response, 'status_code', 200)
            
            metrics_collector.record_request(endpoint, method, duration, status_code)
            
            # Добавляем заголовки с метриками
            if hasattr(response, 'headers'):
                response.headers['X-Response-Time'] = f"{duration:.3f}s"
            
            return response
        
        return decorated_function
    return decorator


def track_db_query(metrics_collector: MetricsCollector):
    """Декоратор для отслеживания DB запросов."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            result = f(*args, **kwargs)
            duration = time.time() - start_time
            
            metrics_collector.record_db_query(duration)
            
            if duration > 0.1:
                logger.warning(f"Slow query detected: {f.__name__} took {duration:.3f}s")
            
            return result
        
        return decorated_function
    return decorator


class PerformanceMonitor:
    """Мониторинг производительности с алертами."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.thresholds = {
            'error_rate': 5.0,  # Процент ошибок
            'avg_response_time': 1.0,  # Секунды
            'cpu_usage': 80.0,  # Процент
            'memory_usage': 80.0,  # Процент
        }
        self.alerts = []
    
    def check_thresholds(self) -> list:
        """Проверить пороговые значения."""
        alerts = []
        stats = self.metrics.get_stats()
        system = SystemMonitor.get_all_metrics()
        
        # Проверка error rate
        error_rate = stats['errors']['error_rate']
        if error_rate > self.thresholds['error_rate']:
            alerts.append({
                'type': 'high_error_rate',
                'value': error_rate,
                'threshold': self.thresholds['error_rate'],
                'message': f"Error rate {error_rate:.1f}% exceeds threshold {self.thresholds['error_rate']}%",
            })
        
        # Проверка CPU
        cpu_usage = system['cpu']
        if cpu_usage > self.thresholds['cpu_usage']:
            alerts.append({
                'type': 'high_cpu_usage',
                'value': cpu_usage,
                'threshold': self.thresholds['cpu_usage'],
                'message': f"CPU usage {cpu_usage:.1f}% exceeds threshold {self.thresholds['cpu_usage']}%",
            })
        
        # Проверка памяти
        memory_usage = system['memory']['percent']
        if memory_usage > self.thresholds['memory_usage']:
            alerts.append({
                'type': 'high_memory_usage',
                'value': memory_usage,
                'threshold': self.thresholds['memory_usage'],
                'message': f"Memory usage {memory_usage:.1f}% exceeds threshold {self.thresholds['memory_usage']}%",
            })
        
        self.alerts.extend(alerts)
        
        # Логируем алерты
        for alert in alerts:
            logger.warning(f"ALERT: {alert['message']}")
        
        return alerts
    
    def get_alerts(self, minutes: int = 60) -> list:
        """Получить алерты за последние N минут."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [a for a in self.alerts if a.get('timestamp', datetime.utcnow()) > cutoff]


# Глобальный сборщик метрик
metrics_collector = MetricsCollector()
performance_monitor = PerformanceMonitor(metrics_collector)
