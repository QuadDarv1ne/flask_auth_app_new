# Flask Auth App - Docker

Этот файл объясняет, как запустить приложение с помощью Docker.

## Быстрый старт с Docker

### 1. Запуск с Docker Compose (рекомендуется)

```bash
# Сборка и запуск контейнера
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка контейнера
docker-compose down
```

Приложение будет доступно по адресу: http://localhost:5000

### 2. Запуск с Docker напрямую

```bash
# Сборка образа
docker build -t flask-auth-app .

# Запуск контейнера
docker run -d -p 5000:5000 --name flask_auth flask-auth-app

# Просмотр логов
docker logs -f flask_auth

# Остановка контейнера
docker stop flask_auth
docker rm flask_auth
```

## Переменные окружения

Вы можете настроить приложение через переменные окружения в `docker-compose.yml`:

- `SECRET_KEY` - секретный ключ для Flask (обязательно измените в продакшене!)
- `FLASK_ENV` - окружение (development/production)
- `DATABASE_URL` - путь к базе данных

## Сохранение данных

База данных SQLite сохраняется в volume `./instance`, поэтому данные сохранятся после перезапуска контейнера.

## Тестовые пользователи

При первом запуске автоматически создаются тестовые пользователи:

1. **admin** / admin123
2. **testuser** / test123
3. **demo** / demo123
