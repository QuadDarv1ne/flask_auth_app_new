# ⚡ Quick Start Guide - Flask Auth App

Быстрое руководство для начала работы с проектом за 5 минут.

## 🚀 Мгновенный старт

### Вариант 1: Автоматический скрипт

**Linux/Mac**:
```bash
chmod +x scripts/quick-start.sh
./scripts/quick-start.sh
```

**Windows**:
```batch
scripts\quick-start.bat
```

### Вариант 2: Docker Compose

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

Откройте http://localhost:5000

### Вариант 3: Вручную (5 шагов)

```bash
# 1. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Создать .env файл
cp .env.example .env
# Отредактируйте .env и установите SECRET_KEY

# 4. Инициализировать базу данных
python run.py init-db

# 5. Запустить приложение
python run.py
```

## 📋 Что дальше?

### Создать администратора
```bash
python run.py create-admin
```

### Запустить тесты
```bash
make test
# или
pytest tests/ -v
```

### Проверить безопасность
```bash
make security
```

### Посмотреть метрики
```bash
# Через API
curl http://localhost:5000/metrics

# Через CLI
make metrics
```

## 🛠️ Полезные команды

```bash
make help          # Показать все команды
make dev           # Запуск development
make prod          # Запуск production
make test          # Тесты с coverage
make lint          # Проверка кода
make docker-up     # Docker Compose
make backup        # Создать бэкап
make clean         # Очистка
```

## 📚 Документация

- [README.md](README.md) - Полное описание
- [DEPLOYMENT.md](DEPLOYMENT.md) - Руководство по развёртыванию
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API документация
- [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md) - Отчёт об оптимизации

## 🆘 Проблемы?

### Приложение не запускается
```bash
# Проверить логи
tail -f logs/app.log

# Проверить зависимости
pip check

# Переустановить
pip install -r requirements.txt --force-reinstall
```

### База данных не создаётся
```bash
# Удалить старую БД и создать новую
rm instance/app.db
python run.py init-db
```

### Redis недоступен
```bash
# Установить Redis
# Ubuntu: sudo apt install redis-server
# Mac: brew install redis
# Windows: https://redis.io/download

# Запустить Redis
redis-server
```

## ✅ Checklist первого запуска

- [ ] Python 3.9+ установлен
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] .env файл настроен
- [ ] База данных инициализирована
- [ ] Redis запущен (опционально)
- [ ] Приложение запущено
- [ ] Открыт http://localhost:5000
- [ ] Создан администратор
- [ ] Запущены тесты

## 🎯 Production deployment

См. подробное руководство в [DEPLOYMENT.md](DEPLOYMENT.md)

Краткая версия:
```bash
# 1. Настроить .env для production
# 2. Запустить Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# 3. Проверить статус
curl http://localhost:5000/health
```

---

**Готово!** Приложение запущено и готово к использованию! 🎉

Для получения дополнительной помощи см. [README.md](README.md)
