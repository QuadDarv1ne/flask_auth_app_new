"""Модуль для мониторинга метрик Prometheus"""

from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
from flask import request, Response
global g
from flask import g
import time

# Метрики для отслеживания запросов
REQUEST_COUNT = Counter(
    'flask_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'http_status']
)

REQUEST_DURATION = Histogram(
    'flask_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

REQUEST_IN_PROGRESS = Gauge(
    'flask_requests_in_progress',
    'Number of requests currently being processed',
    ['method', 'endpoint']
)

ACTIVE_USERS = Gauge(
    'flask_active_users',
    'Number of active users'
)

FAILED_LOGIN_ATTEMPTS = Counter(
    'flask_failed_login_attempts_total',
    'Total number of failed login attempts'
)

SUCCESSFUL_REGISTRATIONS = Counter(
    'flask_successful_registrations_total',
    'Total number of successful registrations'
)

USER_SESSIONS = Gauge(
    'flask_user_sessions_total',
    'Total number of active user sessions'
)

API_CALLS = Counter(
    'flask_api_calls_total',
    'Total number of API calls',
    ['endpoint', 'method']
)

DB_QUERIES = Summary(
    'flask_database_queries_duration_seconds',
    'Time spent executing database queries',
    ['query_type']
)

def record_request_metrics(start_time, endpoint, method, status_code):
    """Запись метрик для HTTP запроса"""
    duration = time.time() - start_time
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
    REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()

def increment_failed_logins():
    """Увеличение счетчика неудачных попыток входа"""
    FAILED_LOGIN_ATTEMPTS.inc()

def increment_successful_registrations():
    """Увеличение счетчика успешных регистраций"""
    SUCCESSFUL_REGISTRATIONS.inc()

def set_active_users(count):
    """Установка количества активных пользователей"""
    ACTIVE_USERS.set(count)

def increment_user_sessions():
    """Увеличение счетчика активных сессий"""
    USER_SESSIONS.inc()

def decrement_user_sessions():
    """Уменьшение счетчика активных сессий"""
    USER_SESSIONS.dec()

def record_api_call(endpoint, method):
    """Запись метрик для API вызова"""
    API_CALLS.labels(endpoint=endpoint, method=method).inc()

def record_db_query(query_type, duration):
    """Запись метрик для выполнения запроса к БД"""
    DB_QUERIES.labels(query_type=query_type).observe(duration)

def increment_request_in_progress(method, endpoint):
    """Увеличение счетчика обрабатываемых запросов"""
    REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

def metrics_endpoint():
    """Endpoint для получения метрик Prometheus"""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)