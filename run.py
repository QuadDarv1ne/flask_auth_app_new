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

@app.cli.command()
def warm_cache():
    """Предварительное заполнение кэша"""
    from utils.cache_strategies import CacheWarmer
    from utils.redis_cache import cache
    
    warmer = CacheWarmer(app, cache)
    warmer.warm_cache()
    print('✓ Cache warmed successfully')

@app.cli.command()
def analyze_queries():
    """Анализировать медленные запросы"""
    from utils.query_optimization import QueryOptimizer
    
    optimizer = app.extensions.get('query_optimizer')
    if optimizer:
        stats = optimizer.stats.get_summary()
        slow_queries = optimizer.stats.get_slow_queries(limit=5)
        
        print('\n=== Query Statistics ===')
        print(f"Total Queries: {stats.get('total_queries', 0)}")
        print(f"Total Time: {stats.get('total_time', 0):.3f}s")
        print(f"Average Time: {stats.get('avg_time', 0):.3f}s")
        print(f"Slow Queries: {stats.get('slow_queries_count', 0)}")
        
        if slow_queries:
            print('\n=== Top Slow Queries ===')
            for i, query in enumerate(slow_queries, 1):
                print(f"{i}. {query['duration']:.3f}s - {query['query'][:80]}")

@app.cli.command()
def setup_indexes():
    """Создать индексы для оптимизации БД"""
    from utils.query_optimization import QueryOptimizer
    
    optimizer = QueryOptimizer(db)
    
    # Создание индексов для таблицы users
    optimizer.create_index('users', 'email', 'idx_users_email')
    optimizer.create_index('users', 'username', 'idx_users_username')
    optimizer.create_composite_index('users', ['is_admin', 'is_active'])
    
    # Анализ таблиц
    optimizer.analyze_table('users')
    
    print('✓ Database indexes created and analyzed')

@app.cli.command()
def test_performance():
    """Тестировать производительность"""
    from utils.advanced_monitoring import LoadTesting
    
    print('Starting load test...')
    
    results = LoadTesting.simulate_traffic(
        'http://localhost:5000/',
        requests_count=50,
        concurrent=5
    )
    
    print('\n=== Load Test Results ===')
    print(f"Total Requests: {results['total_requests']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {results.get('success_rate', 0):.2%}")
    print(f"Average Time: {results.get('avg_time', 0):.3f}s")
    print(f"Min Time: {results.get('min_time', 0):.3f}s")
    print(f"Max Time: {results.get('max_time', 0):.3f}s")

@app.cli.command()
def capacity_planning():
    """Планирование емкости на год"""
    from utils.advanced_monitoring import CapacityPlanning
    
    predictions = CapacityPlanning.predict_resource_needs(
        current_users=100,
        growth_rate=0.10,  # 10% месячный рост
        months=12
    )
    
    print('\n=== Capacity Planning (12 months) ===')
    print(f"Current Users: {predictions['current_users']}")
    print(f"Growth Rate: {predictions['growth_rate']}")
    print()
    
    for pred in predictions[::3]:  # Показываем каждый 3-й месяц
        print(f"Month {pred['month']}: {pred['projected_users']} users")
        print(f"  CPU Cores: {pred['cpu_cores']}, Memory: {pred['memory_mb']}MB, Storage: {pred['storage_gb']}GB")


if __name__ == '__main__':
    # Запуск с SocketIO
    # В продакшене использовать gunicorn с eventlet worker
    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )
