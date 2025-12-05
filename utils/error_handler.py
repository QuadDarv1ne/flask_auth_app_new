"""
Улучшенная обработка ошибок и исключений
"""
from flask import render_template, jsonify, request
import traceback
import logging


class APIException(Exception):
    """Базовый класс для исключений API."""
    
    def __init__(self, message, status_code=400, error_code=None, details=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        """Преобразование в словарь для JSON ответа."""
        return {
            'error': self.error_code,
            'message': self.message,
            'status_code': self.status_code,
            'details': self.details
        }


class ValidationError(APIException):
    """Ошибка валидации данных."""
    status_code = 400


class AuthenticationError(APIException):
    """Ошибка аутентификации."""
    status_code = 401


class AuthorizationError(APIException):
    """Ошибка авторизации."""
    status_code = 403


class NotFoundError(APIException):
    """Ресурс не найден."""
    status_code = 404


class ConflictError(APIException):
    """Конфликт (например, дубликат)."""
    status_code = 409


class RateLimitError(APIException):
    """Превышен лимит запросов."""
    status_code = 429


class InternalServerError(APIException):
    """Внутренняя ошибка сервера."""
    status_code = 500


class ServiceUnavailableError(APIException):
    """Сервис недоступен."""
    status_code = 503


def setup_error_handlers(app, logger):
    """Регистрация обработчиков ошибок."""
    
    @app.errorhandler(APIException)
    def handle_api_exception(error):
        """Обработка API исключений."""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        
        # Логирование
        if error.status_code >= 500:
            logger.error(f"API Error: {error.to_dict()}", exc_info=True)
        else:
            logger.warning(f"API Error: {error.to_dict()}")
        
        return response
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Обработка 400 ошибки."""
        return render_template('errors/400.html', error=str(error)), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Обработка 401 ошибки."""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Требуется аутентификация'
            }), 401
        return render_template('errors/401.html', error=str(error)), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Обработка 403 ошибки."""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Forbidden',
                'message': 'Доступ запрещен'
            }), 403
        return render_template('errors/403.html', error=str(error)), 403
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Обработка 404 ошибки."""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'NotFound',
                'message': 'Ресурс не найден'
            }), 404
        return render_template('errors/404.html', error=str(error)), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Обработка 405 ошибки."""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'MethodNotAllowed',
                'message': 'Метод не разрешен'
            }), 405
        return render_template('errors/405.html', error=str(error)), 405
    
    @app.errorhandler(429)
    def handle_rate_limit(error):
        """Обработка 429 ошибки (Rate Limit)."""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'TooManyRequests',
                'message': 'Превышен лимит запросов'
            }), 429
        return render_template('errors/429.html', error=str(error)), 429
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Обработка 500 ошибки."""
        logger.error(f"Internal Server Error: {str(error)}", exc_info=True)
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'InternalServerError',
                'message': 'Внутренняя ошибка сервера'
            }), 500
        return render_template('errors/500.html', error=str(error)), 500
    
    @app.errorhandler(503)
    def handle_service_unavailable(error):
        """Обработка 503 ошибки."""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'ServiceUnavailable',
                'message': 'Сервис недоступен'
            }), 503
        return render_template('errors/503.html', error=str(error)), 503
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Обработка неожиданных ошибок."""
        logger.error(f"Unexpected Error: {str(error)}", exc_info=True)
        
        # В production не показываем детали ошибки
        if app.config.get('ENV') == 'production':
            error_message = 'Произошла внутренняя ошибка'
        else:
            error_message = str(error)
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'InternalServerError',
                'message': error_message
            }), 500
        
        return render_template('errors/500.html', error=error_message), 500


class ErrorLogger:
    """Специализированное логирование ошибок."""
    
    def __init__(self, logger):
        self.logger = logger
    
    def log_validation_error(self, errors, user_id=None):
        """Логирование ошибки валидации."""
        message = f"Validation Error | Errors: {errors}"
        if user_id:
            message += f" | User: {user_id}"
        self.logger.warning(message)
    
    def log_authentication_error(self, reason, email=None, ip_address=None):
        """Логирование ошибки аутентификации."""
        message = f"Authentication Error | Reason: {reason}"
        if email:
            message += f" | Email: {email}"
        if ip_address:
            message += f" | IP: {ip_address}"
        self.logger.warning(message)
    
    def log_authorization_error(self, resource, user_id=None, ip_address=None):
        """Логирование ошибки авторизации."""
        message = f"Authorization Error | Resource: {resource}"
        if user_id:
            message += f" | User: {user_id}"
        if ip_address:
            message += f" | IP: {ip_address}"
        self.logger.warning(message)
    
    def log_database_error(self, operation, error, user_id=None):
        """Логирование ошибки БД."""
        message = f"Database Error | Operation: {operation} | Error: {error}"
        if user_id:
            message += f" | User: {user_id}"
        self.logger.error(message)
    
    def log_external_api_error(self, api_name, error, retry_count=0):
        """Логирование ошибки внешнего API."""
        message = f"External API Error | API: {api_name} | Error: {error}"
        if retry_count > 0:
            message += f" | Retry: {retry_count}"
        self.logger.error(message)
    
    def log_security_violation(self, violation_type, details=None):
        """Логирование нарушения безопасности."""
        message = f"Security Violation | Type: {violation_type}"
        if details:
            message += f" | Details: {details}"
        self.logger.critical(message)


# Декоратор для обработки ошибок в функциях
def handle_errors(logger=None):
    """Декоратор для обработки ошибок в функциях."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except APIException:
                raise
            except Exception as e:
                if logger:
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                raise InternalServerError(
                    message="Произошла ошибка при обработке запроса",
                    details={'function': func.__name__}
                )
        return wrapper
    return decorator
