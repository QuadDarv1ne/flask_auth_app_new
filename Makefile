# Makefile для управления Flask Auth App проектом

.PHONY: help install dev prod test clean lint format migrate backup docker

# Цвета для вывода
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m # No Color

help: ## Показать это сообщение помощи
	@echo "$(GREEN)Flask Auth App - Команды управления проектом$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Установить все зависимости
	@echo "$(GREEN)Установка зависимостей...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✓ Зависимости установлены$(NC)"

dev: ## Запустить в режиме разработки
	@echo "$(GREEN)Запуск в режиме разработки...$(NC)"
	export FLASK_ENV=development && python run.py

prod: ## Запустить в продакшн режиме с Gunicorn
	@echo "$(GREEN)Запуск в продакшн режиме...$(NC)"
	gunicorn -c gunicorn_config.py run:app

test: ## Запустить тесты
	@echo "$(GREEN)Запуск тестов...$(NC)"
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

test-quick: ## Быстрые тесты (без coverage)
	@echo "$(GREEN)Быстрые тесты...$(NC)"
	pytest tests/ -v

coverage: ## Показать coverage отчёт
	@echo "$(GREEN)Генерация coverage отчёта...$(NC)"
	pytest tests/ --cov=. --cov-report=html
	@echo "$(GREEN)Отчёт создан в htmlcov/index.html$(NC)"

lint: ## Проверить код линтерами
	@echo "$(GREEN)Проверка кода...$(NC)"
	@echo "$(YELLOW)Flake8...$(NC)"
	-flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@echo "$(YELLOW)Bandit (security)...$(NC)"
	-bandit -r . -ll
	@echo "$(YELLOW)Safety (dependencies)...$(NC)"
	-safety check

format: ## Форматировать код
	@echo "$(GREEN)Форматирование кода...$(NC)"
	black . --line-length 100
	isort .
	@echo "$(GREEN)✓ Код отформатирован$(NC)"

init-db: ## Инициализировать базу данных
	@echo "$(GREEN)Инициализация базы данных...$(NC)"
	python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✓ Database initialized')"

migrate: ## Применить миграции
	@echo "$(GREEN)Применение миграций...$(NC)"
	python migrations.py migrate

migrate-status: ## Статус миграций
	@echo "$(GREEN)Статус миграций:$(NC)"
	python migrations.py status

rollback: ## Откатить последнюю миграцию
	@echo "$(YELLOW)Откат миграции...$(NC)"
	python migrations.py rollback

backup: ## Создать бэкап базы данных
	@echo "$(GREEN)Создание бэкапа...$(NC)"
	python -m utils.backup backup --output backups/
	@echo "$(GREEN)✓ Бэкап создан$(NC)"

restore: ## Восстановить из бэкапа (использовать: make restore FILE=backup.tar.gz)
	@echo "$(YELLOW)Восстановление из бэкапа...$(NC)"
	python -m utils.backup restore --file $(FILE)

clean: ## Очистить временные файлы
	@echo "$(GREEN)Очистка...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	@echo "$(GREEN)✓ Очистка завершена$(NC)"

clean-cache: ## Очистить Redis кэш
	@echo "$(GREEN)Очистка кэша...$(NC)"
	python -c "from utils.redis_cache import cache; cache.clear(); print('✓ Cache cleared')"

docker-build: ## Собрать Docker образ
	@echo "$(GREEN)Сборка Docker образа...$(NC)"
	docker build -t flask-auth-app:latest .
	@echo "$(GREEN)✓ Образ собран$(NC)"

docker-up: ## Запустить Docker Compose
	@echo "$(GREEN)Запуск Docker Compose...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Контейнеры запущены$(NC)"

docker-down: ## Остановить Docker Compose
	@echo "$(YELLOW)Остановка Docker Compose...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Контейнеры остановлены$(NC)"

docker-logs: ## Показать логи Docker
	docker-compose logs -f

docker-shell: ## Войти в контейнер приложения
	docker-compose exec web bash

metrics: ## Показать метрики приложения
	@echo "$(GREEN)Текущие метрики:$(NC)"
	python -c "from app import create_app; from utils.monitoring import metrics_collector, SystemMonitor; app = create_app(); app.app_context().push(); stats = metrics_collector.get_stats(); system = SystemMonitor.get_all_metrics(); print('Requests:', stats['requests']['total']); print('Errors:', stats['errors']['total']); print('CPU:', system['cpu'], '%'); print('Memory:', system['memory']['percent'], '%')"

routes: ## Показать все маршруты
	@echo "$(GREEN)Маршруты приложения:$(NC)"
	python -c "from app import create_app; app = create_app(); app.app_context().push(); [print(f'{rule.endpoint:50s} {str(rule)}') for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r))]"

shell: ## Запустить Flask shell
	@echo "$(GREEN)Flask shell$(NC)"
	flask shell

create-admin: ## Создать администратора
	@echo "$(GREEN)Создание администратора:$(NC)"
	python run.py create-admin

venv: ## Создать виртуальное окружение
	@echo "$(GREEN)Создание виртуального окружения...$(NC)"
	python -m venv venv
	@echo "$(GREEN)✓ Виртуальное окружение создано$(NC)"
	@echo "$(YELLOW)Активируйте его:$(NC)"
	@echo "  Windows: venv\\Scripts\\activate"
	@echo "  Linux/Mac: source venv/bin/activate"

requirements: ## Обновить requirements.txt
	@echo "$(GREEN)Обновление requirements.txt...$(NC)"
	pip freeze > requirements.txt
	@echo "$(GREEN)✓ Requirements обновлены$(NC)"

security: ## Проверка безопасности
	@echo "$(GREEN)Проверка безопасности...$(NC)"
	@echo "$(YELLOW)Bandit...$(NC)"
	bandit -r . -ll
	@echo "$(YELLOW)Safety...$(NC)"
	safety check
	@echo "$(GREEN)✓ Проверка завершена$(NC)"

quality: ## Анализ качества кода
	@echo "$(GREEN)Анализ качества кода...$(NC)"
	@echo "$(YELLOW)Radon - Cyclomatic Complexity:$(NC)"
	radon cc . -a
	@echo "$(YELLOW)Radon - Maintainability Index:$(NC)"
	radon mi . -s
	@echo "$(GREEN)✓ Анализ завершён$(NC)"

all-checks: lint security quality test ## Запустить все проверки
	@echo "$(GREEN)✓ Все проверки пройдены$(NC)"

.DEFAULT_GOAL := help
