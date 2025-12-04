from flask import Flask, render_template, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from utils.logging import setup_logging
from utils.email import mail
from utils.metrics import metrics_endpoint, record_request_metrics
from flask_minify import Minify
import os
import time

# Инициализация расширений
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Минификатор для оптимизации статических файлов
minify = Minify()

def create_app(config_class=Config):
    """Фабрика приложения Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Установка максимального размера загружаемых файлов (5MB)
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
    
    # Создание директории для загрузок
    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    # Инициализация расширений с приложением
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    minify.init_app(app)
    
    # Configure rate limiter storage
    if hasattr(config_class, 'RATELIMIT_STORAGE_URL'):
        app.config.setdefault('RATELIMIT_STORAGE_URL', config_class.RATELIMIT_STORAGE_URL)
    limiter.init_app(app)
    
    # Настройка логирования
    setup_logging(app)
    
    # Настройка Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
    login_manager.login_message_category = 'info'
    
    # Загрузчик пользователя для Flask-Login
    from models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Middleware для сбора метрик
    @app.before_request
    def before_request():
        g.start_time = time.time()
        endpoint = request.endpoint or 'unknown'
        from utils.metrics import increment_request_in_progress
        increment_request_in_progress(request.method, endpoint)
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            endpoint = request.endpoint or 'unknown'
            record_request_metrics(g.start_time, endpoint, request.method, response.status_code)
        
        # Добавляем заголовки безопасности
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://kit.fontawesome.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://kit.fontawesome.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # Force HTTPS if configured
        if app.config.get('FORCE_HTTPS', False):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    # Регистрация blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    # Endpoint для метрик Prometheus
    @app.route('/metrics')
    def metrics():
        return metrics_endpoint()
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'timestamp': time.time()}, 200
    
    # Обработчики ошибок
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(f'400 error: {error}')
        return render_template('errors/400.html', title='Некорректный запрос'), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        app.logger.warning(f'401 error: {error}')
        flash('Пожалуйста, войдите в систему для доступа к этой странице.', 'warning')
        return redirect(url_for('auth.login')), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f'403 error: {error}')
        return render_template('errors/403.html', title='Доступ запрещен'), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f'404 error: {error}')
        return render_template('errors/404.html', title='Страница не найдена'), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        app.logger.warning(f'405 error: {error}')
        return render_template('errors/405.html', title='Метод не разрешен'), 405
    
    @app.errorhandler(429)
    def too_many_requests(error):
        app.logger.warning(f'429 error: {error}')
        return render_template('errors/429.html', title='Слишком много запросов'), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'500 error: {error}')
        return render_template('errors/500.html', title='Внутренняя ошибка сервера'), 500
    
    # Обработчик ошибок загрузки файлов
    @app.errorhandler(413)
    def too_large(e):
        app.logger.warning(f'File too large error: {e}')
        flash('Файл слишком большой. Максимальный размер файла 16MB.', 'error')
        return render_template('errors/413.html', title='Файл слишком большой'), 413
    
    # Создание таблиц базы данных
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("\n" + "="*60)
    print("🚀 Flask Auth App запущен!")
    print("="*60)
    print("📍 Откройте браузер: http://localhost:5000")
    print("🔐 Зарегистрируйтесь или войдите в систему")
    print("📊 Метрики Prometheus: http://localhost:5000/metrics")
    print("🏥 Health check: http://localhost:5000/health")
    print("📚 API документация: http://localhost:5000/api/docs/")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)