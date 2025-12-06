"""
Точка входа в приложение
Запускает Flask приложение с SocketIO поддержкой
"""
import os
from app import create_app, db, socketio
from models import User

# Создание приложения
app = create_app(os.getenv('FLASK_ENV', 'development'))

# Shell context для flask shell
@app.shell_context_processor
def make_shell_context():
    """Добавляет переменные в flask shell"""
    return {
        'db': db,
        'User': User,
        'app': app
    }

# CLI команды
@app.cli.command()
def init_db():
    """Инициализация базы данных"""
    db.create_all()
    print('✓ Database initialized')

@app.cli.command()
def create_admin():
    """Создание администратора"""
    from werkzeug.security import generate_password_hash
    
    username = input('Admin username: ')
    email = input('Admin email: ')
    password = input('Admin password: ')
    
    # Проверка существования пользователя
    if User.query.filter_by(username=username).first():
        print('✗ User already exists')
        return
    
    # Создание администратора
    admin = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        is_admin=True,
        is_active=True
    )
    
    db.session.add(admin)
    db.session.commit()
    
    print(f'✓ Admin user created: {username}')

@app.cli.command()
def clear_cache():
    """Очистка Redis кэша"""
    from utils.redis_cache import cache
    
    if cache.is_available():
        count = cache.clear()
        print(f'✓ Cache cleared: {count} keys deleted')
    else:
        print('✗ Redis not available')

@app.cli.command()
def show_routes():
    """Показать все маршруты приложения"""
    from flask import url_for
    import urllib
    
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = f"{rule.endpoint:50s} {methods:20s} {rule}"
        output.append(line)
    
    for line in sorted(output):
        print(line)

@app.cli.command()
def show_metrics():
    """Показать текущие метрики"""
    from utils.monitoring import metrics_collector, SystemMonitor
    
    stats = metrics_collector.get_stats()
    system = SystemMonitor.get_all_metrics()
    
    print('\n=== Application Metrics ===')
    print(f"Total Requests: {stats['requests']['total']}")
    print(f"Total Errors: {stats['errors']['total']}")
    print(f"Error Rate: {stats['errors']['error_rate']:.2f}%")
    print(f"Cache Hit Rate: {stats['cache']['hit_rate']:.2f}%")
    
    print('\n=== System Metrics ===')
    print(f"CPU Usage: {system['cpu']:.1f}%")
    print(f"Memory Usage: {system['memory']['percent']:.1f}%")
    print(f"Disk Usage: {system['disk'].get('percent', 0):.1f}%")

if __name__ == '__main__':
    # Запуск с SocketIO
    # В продакшене использовать gunicorn с eventlet worker
    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )
