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
import time

# Инициализация расширений
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app(config_class=Config):
    """Фабрика приложения Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Инициализация расширений с приложением
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
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
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            endpoint = request.endpoint or 'unknown'
            record_request_metrics(g.start_time, endpoint, request.method, response.status_code)
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
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f'404 error: {error}')
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'500 error: {error}')
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f'403 error: {error}')
        return render_template('errors/403.html'), 403
    
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