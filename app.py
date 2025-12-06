from flask import Flask, render_template, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config_env import get_config
from flask_minify import Minify
import os
import time
import logging

# Импорт новых утилит
from utils.logger import setup_logging
from utils.redis_cache import cache
from utils.monitoring import metrics_collector, performance_monitor, SystemMonitor
from utils.error_handler import setup_error_handlers, ErrorLogger
from utils.email_service import email_service
from utils.websocket import socketio, ws_manager
from utils.rate_limit import rate_limit
from utils.security_utils import SecureHeaders
from utils.cache_strategies import CacheWarmer, SmartCache
from utils.cdn_optimization import CDNOptimizer, ContentCompression
from utils.query_optimization import QueryOptimizer
from utils.advanced_monitoring import PerformanceMetricsCollector, AlertSystem, DashboardData
from utils.background_tasks import TaskQueue, TaskScheduler, CommonTasks, ScheduledTask

# Инициализация расширений
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Минификатор для оптимизации статических файлов
minify = Minify()

# Error logger будет инициализирован в create_app
error_logger = None

def create_app(config_name=None):
    """Фабрика приложения Flask"""
    app = Flask(__name__)
    
    # Загрузка конфигурации из config_env.py
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Создание директории для загрузок
    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    # Инициализация расширений с приложением
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    minify.init_app(app)
    limiter.init_app(app)
    
    # Инициализация новых компонентов
    try:
        cache.init_app(app)
    except Exception as e:
        app_logger = logging.getLogger('flask_auth_app')
        app_logger.warning(f"⚠ Cache initialization warning: {e}")
    
    try:
        email_service.init_app(app)
    except Exception as e:
        app_logger = logging.getLogger('flask_auth_app')
        app_logger.warning(f"⚠ Email service initialization warning: {e}")
    
    try:
        rate_limit.init_app(app)
    except Exception as e:
        app_logger = logging.getLogger('flask_auth_app')
        app_logger.warning(f"⚠ Rate limit initialization warning: {e}")
    
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    
    # Инициализация продвинутых оптимизаций
    smart_cache = SmartCache(cache)
    cdn_optimizer = CDNOptimizer(app.config.get('CDN_URL', None))
    advanced_metrics = PerformanceMetricsCollector()
    alert_system = AlertSystem()
    dashboard_data = DashboardData(advanced_metrics, alert_system)
    
    # Инициализация фоновых задач
    task_queue = TaskQueue(db)
    task_scheduler = TaskScheduler()
    
    # Инициализация Query Optimizer
    query_optimizer = QueryOptimizer(db)
    
    # Инициализация Cache Warmer
    cache_warmer = CacheWarmer(app, cache)
    
    # Регистрация планировщика задач
    task_scheduler.register_scheduled_task(
        ScheduledTask('cleanup_sessions', CommonTasks.cleanup_old_sessions, 'daily')
    )
    task_scheduler.register_scheduled_task(
        ScheduledTask('backup_database', lambda: CommonTasks.backup_database(app.config['DATABASE_URL']), 'daily')
    )
    
    # Настройка логирования
    setup_logging(app)
    
    # Инициализация Error Logger
    app_logger = logging.getLogger('flask_auth_app')
    error_logger = ErrorLogger(app_logger)
    
    # Сохраняем в расширении для использования в обработчиках
    app.extensions['error_logger'] = error_logger
    
    # Настройка обработчиков ошибок
    setup_error_handlers(app, app_logger)
    
    # Регистрация расширений в app.extensions
    app.extensions['cache'] = cache
    app.extensions['smart_cache'] = smart_cache
    app.extensions['metrics_collector'] = metrics_collector
    app.extensions['advanced_metrics'] = advanced_metrics
    app.extensions['ws_manager'] = ws_manager
    app.extensions['task_queue'] = task_queue
    app.extensions['query_optimizer'] = query_optimizer
    app.extensions['cdn_optimizer'] = cdn_optimizer
    app.extensions['alert_system'] = alert_system
    app.extensions['dashboard_data'] = dashboard_data
    
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
        
        # Проверка rate limit (если не отключен для эндпоинта)
        if not getattr(request.endpoint, '_rate_limit_exempt', False):
            # Rate limit уже обрабатывается декораторами
            pass
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            # Запись метрик
            duration = time.time() - g.start_time
            endpoint = request.endpoint or 'unknown'
            status_code = response.status_code
            
            metrics_collector.record_request(
                endpoint=endpoint,
                method=request.method,
                duration=duration,
                status_code=status_code
            )
            
            # Проверка порогов производительности
            performance_monitor.check_thresholds()
        
        # Добавляем security headers
        security_headers = SecureHeaders.get_security_headers()
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Force HTTPS if configured
        if app.config.get('FORCE_HTTPS', False):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    # Регистрация blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    # API blueprint (если существует)
    try:
        from routes.api import api_bp
        app.register_blueprint(api_bp)
    except ImportError:
        pass
    
    # Endpoint для метрик
    @app.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint"""
        stats = metrics_collector.get_stats()
        system_metrics = SystemMonitor.get_all_metrics()
        
        return {
            'application': stats,
            'system': system_metrics,
            'timestamp': time.time()
        }, 200
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check для мониторинга"""
        try:
            # Проверка БД
            db.session.execute('SELECT 1')
            db_status = 'healthy'
        except:
            db_status = 'unhealthy'
        
        # Проверка Redis
        redis_status = 'healthy' if cache.is_available() else 'unhealthy'
        
        overall_status = 'healthy' if all([
            db_status == 'healthy',
            redis_status == 'healthy'
        ]) else 'degraded'
        
        return {
            'status': overall_status,
            'database': db_status,
            'redis': redis_status,
            'websocket_connections': ws_manager.get_stats(),
            'timestamp': time.time()
        }, 200 if overall_status == 'healthy' else 503
    
    # API Status endpoint
    @app.route('/api/status')
    def api_status():
        """Детальный статус API"""
        return {
            'api_version': '1.0',
            'status': 'operational',
            'metrics': metrics_collector.get_stats(),
            'system': SystemMonitor.get_all_metrics(),
            'timestamp': time.time()
        }, 200
    
    # Dashboard endpoint с продвинутыми метриками
    @app.route('/dashboard')
    def dashboard():
        """Dashboard с продвинутыми метриками"""
        from flask_login import login_required
        
        @login_required
        def _dashboard():
            dashboard_info = dashboard_data.get_dashboard_data()
            return {
                'success': True,
                'data': dashboard_info
            }, 200
        
        return _dashboard()
    
    # Advanced alerts endpoint
    @app.route('/api/alerts')
    def get_alerts():
        """Получить активные алерты"""
        return {
            'alerts': alert_system.get_active_alerts(),
            'count': len(alert_system.get_active_alerts()),
            'timestamp': time.time()
        }, 200
    
    # Query statistics endpoint
    @app.route('/api/query-stats')
    def query_stats():
        """Получить статистику запросов к БД"""
        from flask_login import login_required
        
        @login_required
        def _stats():
            stats = query_optimizer.stats.get_summary()
            slow_queries = query_optimizer.stats.get_slow_queries(limit=10)
            
            return {
                'summary': stats,
                'slow_queries': slow_queries,
                'timestamp': time.time()
            }, 200
        
        return _stats()
    
    # Обработчики ошибок (управляются error_handler.py)
    # Дополнительные обработчики для специфичных случаев
    
    @app.errorhandler(413)
    def too_large(e):
        """Обработчик ошибки большого файла"""
        try:
            err_logger = app.extensions.get('error_logger')
            if err_logger:
                err_logger.log_error(e, request)
        except:
            pass
        return render_template('errors/413.html', title='Файл слишком большой'), 413
    
    # Создание таблиц базы данных
    with app.app_context():
        try:
            # Ensure the instance directory exists
            instance_dir = os.path.join(app.root_path, 'instance')
            os.makedirs(instance_dir, exist_ok=True)
            
            db.create_all()
            app_logger.info("✓ Database tables created")
        except Exception as e:
            app_logger.warning(f"Database initialization warning: {e}")
            # Try to create database with a fallback approach
            try:
                # Fallback to in-memory database for development
                if app.config.get('TESTING', False):
                    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
                    db.create_all()
                    app_logger.info("✓ Fallback database created in memory")
            except Exception as fallback_e:
                app_logger.error(f"Critical database initialization error: {fallback_e}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("\n" + "="*60)
    print("🚀 Flask Auth App запущен")
    print("="*60)
    print("📍 Откройте браузер: http://localhost:5000")
    print("🔐 Зарегистрируйтесь или войдите в систему")
    print("📊 Метрики Prometheus: http://localhost:5000/metrics")
    print("🏥 Health check: http://localhost:5000/health")
    print("📚 API документация: http://localhost:5000/api/docs/")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)