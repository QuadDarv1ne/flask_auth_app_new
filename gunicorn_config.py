# Production WSGI configuration for Gunicorn
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'eventlet'  # Для WebSocket поддержки
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Debugging
reload = os.getenv('FLASK_ENV', 'production') == 'development'
reload_engine = 'auto'

# Logging
accesslog = os.getenv('GUNICORN_ACCESS_LOG', 'logs/gunicorn-access.log')
errorlog = os.getenv('GUNICORN_ERROR_LOG', 'logs/gunicorn-error.log')
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'flask_auth_app'

# Server mechanics
daemon = False
pidfile = os.getenv('GUNICORN_PID_FILE', 'gunicorn.pid')
user = None
group = None
tmp_upload_dir = None

# SSL (если используется)
keyfile = os.getenv('SSL_KEY_FILE')
certfile = os.getenv('SSL_CERT_FILE')

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

def when_ready(server):
    """Callback при старте сервера"""
    server.log.info("Server is ready. Spawning workers")

def on_starting(server):
    """Callback перед стартом"""
    server.log.info("Starting Gunicorn server")

def on_reload(server):
    """Callback при перезагрузке"""
    server.log.info("Reloading Gunicorn server")

def worker_int(worker):
    """Callback при получении SIGINT"""
    worker.log.info("Worker received INT signal")

def worker_abort(worker):
    """Callback при abort воркера"""
    worker.log.info("Worker received ABRT signal")

def pre_fork(server, worker):
    """Callback перед fork воркера"""
    pass

def post_fork(server, worker):
    """Callback после fork воркера"""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def post_worker_init(worker):
    """Callback после инициализации воркера"""
    worker.log.info("Worker initialized")

def worker_exit(server, worker):
    """Callback при выходе воркера"""
    server.log.info(f"Worker exited (pid: {worker.pid})")

def nworkers_changed(server, new_value, old_value):
    """Callback при изменении количества воркеров"""
    server.log.info(f"Workers changed from {old_value} to {new_value}")

def on_exit(server):
    """Callback при выходе сервера"""
    server.log.info("Shutting down Gunicorn")
