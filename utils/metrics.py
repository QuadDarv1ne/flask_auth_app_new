"""Модуль для мониторинга метрик Prometheus"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from flask import request, Response
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

def record_request_metrics(start_time, endpoint, method, status_code):
    """Запись метрик для HTTP запроса"""
    duration = time.time() - start_time
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

def increment_failed_logins():
    """Увеличение счетчика неудачных попыток входа"""
    FAILED_LOGIN_ATTEMPTS.inc()

def increment_successful_registrations():
    """Увеличение счетчика успешных регистраций"""
    SUCCESSFUL_REGISTRATIONS.inc()

def set_active_users(count):
    """Установка количества активных пользователей"""
    ACTIVE_USERS.set(count)

def metrics_endpoint():
    """Endpoint для получения метрик Prometheus"""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)