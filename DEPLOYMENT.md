# 🚀 Руководство по развёртыванию Flask Auth App

## 📋 Содержание
- [Требования](#требования)
- [Локальная разработка](#локальная-разработка)
- [Docker](#docker)
- [Production (Ubuntu/Debian)](#production-ubuntudebian)
- [Переменные окружения](#переменные-окружения)
- [Мониторинг](#мониторинг)
- [Резервное копирование](#резервное-копирование)

## 🔧 Требования

### Минимальные требования:
- Python 3.9+
- PostgreSQL 12+ (или SQLite для разработки)
- Redis 6.0+
- 512 MB RAM
- 1 GB свободного места на диске

### Рекомендуемые требования:
- Python 3.11+
- PostgreSQL 15+
- Redis 7.0+
- 2 GB RAM
- 10 GB свободного места на диске

## 💻 Локальная разработка

### 1. Клонирование репозитория
```bash
git clone https://github.com/QuadDarv1ne/flask_auth_app_new.git
cd flask_auth_app_new
```

### 2. Создание виртуального окружения
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения
Создайте файл `.env`:
```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/app.db
REDIS_URL=redis://localhost:6379/0
```

### 5. Инициализация базы данных
```bash
python init_db.py
```

### 6. Запуск приложения
```bash
# Режим разработки
flask run

# Или с горячей перезагрузкой
flask run --reload
```

Приложение будет доступно по адресу: http://localhost:5000

## 🐳 Docker

### Быстрый старт с Docker Compose

```bash
# Сборка и запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка сервисов
docker-compose down
```

### Сервисы Docker Compose:
- **web**: Flask приложение (порт 5000)
- **db**: PostgreSQL база данных (порт 5432)
- **redis**: Redis кэш (порт 6379)

### Доступ к контейнерам:

```bash
# Войти в контейнер приложения
docker-compose exec web bash

# Войти в PostgreSQL
docker-compose exec db psql -U postgres -d flask_auth_app

# Проверить логи Redis
docker-compose logs redis
```

### Сборка собственного образа:

```bash
# Сборка образа
docker build -t flask-auth-app:latest .

# Запуск контейнера
docker run -d \
  -p 5000:5000 \
  -e SECRET_KEY="your-secret-key" \
  -e DATABASE_URL="postgresql://user:pass@db:5432/flask_auth_app" \
  --name flask-app \
  flask-auth-app:latest
```

## 🌐 Production (Ubuntu/Debian)

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3.11 python3.11-venv python3-pip \
  postgresql postgresql-contrib redis-server nginx supervisor git
```

### 2. Настройка PostgreSQL

```bash
# Вход в PostgreSQL
sudo -u postgres psql

# Создание базы данных и пользователя
CREATE DATABASE flask_auth_app;
CREATE USER flask_user WITH PASSWORD 'strong-password-here';
GRANT ALL PRIVILEGES ON DATABASE flask_auth_app TO flask_user;
\q
```

### 3. Настройка приложения

```bash
# Создание пользователя для приложения
sudo useradd -m -s /bin/bash flaskapp
sudo su - flaskapp

# Клонирование репозитория
git clone https://github.com/QuadDarv1ne/flask_auth_app_new.git
cd flask_auth_app_new

# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
pip install gunicorn
```

### 4. Конфигурация переменных окружения

Создайте `.env` файл:
```bash
nano .env
```

```env
FLASK_ENV=production
SECRET_KEY=generate-strong-random-key-here
DATABASE_URL=postgresql://flask_user:strong-password-here@localhost/flask_auth_app
REDIS_URL=redis://localhost:6379/0

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com
```

### 5. Инициализация базы данных

```bash
# Применение миграций
python migrations.py migrate

# Или создание начальных таблиц
python init_db.py
```

### 6. Настройка Gunicorn

Создайте `gunicorn_config.py`:
```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "eventlet"
worker_connections = 1000
timeout = 30
keepalive = 2

# Логирование
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
loglevel = "info"

# Процесс
daemon = False
pidfile = "gunicorn.pid"
```

### 7. Настройка Supervisor

Создайте `/etc/supervisor/conf.d/flaskapp.conf`:
```ini
[program:flaskapp]
command=/home/flaskapp/flask_auth_app_new/venv/bin/gunicorn -c gunicorn_config.py app:app
directory=/home/flaskapp/flask_auth_app_new
user=flaskapp
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/flaskapp/error.log
stdout_logfile=/var/log/flaskapp/access.log
```

```bash
# Создание директории для логов
sudo mkdir -p /var/log/flaskapp
sudo chown flaskapp:flaskapp /var/log/flaskapp

# Перезагрузка Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start flaskapp
```

### 8. Настройка Nginx

Создайте `/etc/nginx/sites-available/flaskapp`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Редирект на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL сертификаты (используйте Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Логирование
    access_log /var/log/nginx/flaskapp-access.log;
    error_log /var/log/nginx/flaskapp-error.log;

    # Статические файлы
    location /static {
        alias /home/flaskapp/flask_auth_app_new/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Проксирование на Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket поддержка
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Безопасность
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

```bash
# Активация сайта
sudo ln -s /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 9. Настройка SSL с Let's Encrypt

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление (проверка)
sudo certbot renew --dry-run
```

## 🔐 Переменные окружения

### Обязательные переменные:

| Переменная | Описание | Пример |
|-----------|----------|--------|
| `SECRET_KEY` | Секретный ключ Flask | `your-secret-key-here` |
| `DATABASE_URL` | URL базы данных | `postgresql://user:pass@localhost/db` |
| `REDIS_URL` | URL Redis сервера | `redis://localhost:6379/0` |

### Опциональные переменные:

| Переменная | Описание | По умолчанию |
|-----------|----------|--------------|
| `FLASK_ENV` | Окружение | `development` |
| `MAIL_SERVER` | SMTP сервер | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP порт | `587` |
| `MAIL_USERNAME` | Email пользователь | - |
| `MAIL_PASSWORD` | Email пароль | - |

## 📊 Мониторинг

### Проверка статуса приложения:

```bash
# Supervisor
sudo supervisorctl status flaskapp

# Логи приложения
tail -f /var/log/flaskapp/error.log

# Логи Nginx
tail -f /var/log/nginx/flaskapp-error.log

# Системные ресурсы
htop
```

### Эндпоинты для мониторинга:

- **Health Check**: `GET /health` - Проверка работоспособности
- **Metrics**: `GET /metrics` - Метрики Prometheus
- **Status**: `GET /api/status` - Детальный статус системы

### Настройка Prometheus (опционально):

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'flask_app'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
```

## 💾 Резервное копирование

### Автоматическое резервное копирование БД:

```bash
# Создание скрипта бэкапа
nano /home/flaskapp/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/flaskapp/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL бэкап
pg_dump -U flask_user flask_auth_app | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

```bash
# Настройка cron для ежедневных бэкапов
crontab -e
```

Добавьте строку:
```
0 2 * * * /home/flaskapp/backup.sh
```

### Использование встроенной утилиты бэкапа:

```bash
# Создание бэкапа
python -m utils.backup backup --output backups/

# Восстановление из бэкапа
python -m utils.backup restore --file backups/backup_20231206.tar.gz

# Список бэкапов
python -m utils.backup list

# Очистка старых бэкапов
python -m utils.backup cleanup --days 30
```

## 🔄 Обновление приложения

```bash
# Переход в директорию приложения
cd /home/flaskapp/flask_auth_app_new

# Получение обновлений
git pull origin main

# Активация виртуального окружения
source venv/bin/activate

# Обновление зависимостей
pip install -r requirements.txt --upgrade

# Применение миграций
python migrations.py migrate

# Перезапуск приложения
sudo supervisorctl restart flaskapp
```

## 🛡️ Безопасность

### Чек-лист безопасности:

- [ ] Использован сильный SECRET_KEY
- [ ] HTTPS включен (SSL сертификат)
- [ ] Firewall настроен (ufw/iptables)
- [ ] Пароли БД сложные и уникальные
- [ ] Redis защищён паролем
- [ ] Регулярные обновления системы
- [ ] Логирование настроено
- [ ] Бэкапы выполняются автоматически
- [ ] Rate limiting включен
- [ ] CSRF защита активна

### Настройка Firewall (UFW):

```bash
# Установка UFW
sudo apt install ufw

# Разрешение SSH
sudo ufw allow 22/tcp

# Разрешение HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включение firewall
sudo ufw enable
```

## 📝 Логи

### Расположение логов:

- **Приложение**: `/var/log/flaskapp/`
- **Nginx**: `/var/log/nginx/`
- **PostgreSQL**: `/var/log/postgresql/`
- **Supervisor**: `/var/log/supervisor/`

### Ротация логов:

Создайте `/etc/logrotate.d/flaskapp`:
```
/var/log/flaskapp/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 flaskapp flaskapp
    sharedscripts
    postrotate
        supervisorctl restart flaskapp
    endscript
}
```

## 🆘 Устранение неполадок

### Приложение не запускается:

```bash
# Проверка логов
sudo supervisorctl tail -f flaskapp stderr

# Проверка зависимостей
source venv/bin/activate
pip check
```

### Ошибки базы данных:

```bash
# Проверка подключения
psql -U flask_user -d flask_auth_app -h localhost

# Проверка статуса PostgreSQL
sudo systemctl status postgresql
```

### Проблемы с Redis:

```bash
# Проверка Redis
redis-cli ping

# Проверка статуса
sudo systemctl status redis
```

## 📞 Поддержка

Если у вас возникли проблемы:
1. Проверьте логи приложения
2. Создайте Issue на GitHub
3. Обратитесь к документации Flask

---

**Автор**: QuadDarv1ne  
**Лицензия**: MIT  
**Версия документации**: 1.0
