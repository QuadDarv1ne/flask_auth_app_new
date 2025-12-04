"""
Утилиты общего назначения
"""

# Импортируем все утилиты для удобного использования
from . import logging, email, decorators, performance, metrics, security
from .logging import setup_logging, log_user_action, log_security_event
from .email import send_email, send_confirmation_email
from .decorators import admin_required, check_confirmed, anonymous_required
from .performance import cache_response, clear_cache, rate_limit, QueryCounter, optimize_images, cache_data
from .metrics import record_request_metrics, increment_failed_logins, increment_successful_registrations, set_active_users, increment_user_sessions, decrement_user_sessions, record_api_call, record_db_query, increment_request_in_progress, metrics_endpoint
from .security import generate_secure_token, hash_sensitive_data, rate_limit_sensitive_operations, require_password_confirmation, sanitize_input, validate_password_strength, detect_suspicious_activity, is_safe_redirect_url
