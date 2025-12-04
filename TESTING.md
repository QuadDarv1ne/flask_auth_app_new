# Руководство по запуску тестов

## Установка зависимостей для тестирования

Убедитесь, что все зависимости установлены:

```bash
pip install -r requirements.txt
```

## Запуск всех тестов

```bash
# Простой запуск всех тестов
python -m pytest tests/

# С подробным выводом
python -m pytest tests/ -v

# С отображением покрытия кода
python -m pytest tests/ --cov=. --cov-report=html

# Только определенный файл
python -m pytest tests/test_models.py -v

# Только определенный тест
python -m pytest tests/test_auth.py::TestAuthRoutes::test_successful_login -v
```

## Структура тестов

```
tests/
├── __init__.py           # Пустой файл для инициализации пакета
├── conftest.py           # Конфигурация pytest и fixtures
├── test_models.py        # Тесты для моделей базы данных
├── test_auth.py          # Тесты для маршрутов аутентификации
└── test_routes.py        # Тесты для основных маршрутов
```

## Описание тестов

### test_models.py (6 тестов)
- `test_user_creation` - Создание пользователя
- `test_password_hashing` - Хеширование пароля
- `test_unique_username` - Уникальность имени пользователя
- `test_unique_email` - Уникальность email
- `test_update_last_login` - Обновление времени входа
- `test_user_representation` - Строковое представление

### test_auth.py (9 тестов)
- `test_login_page_loads` - Загрузка страницы входа
- `test_register_page_loads` - Загрузка страницы регистрации
- `test_successful_registration` - Успешная регистрация
- `test_registration_with_existing_username` - Регистрация с существующим именем
- `test_registration_password_mismatch` - Несовпадение паролей
- `test_successful_login` - Успешный вход
- `test_login_with_wrong_password` - Вход с неправильным паролем
- `test_login_with_nonexistent_user` - Вход несуществующего пользователя
- `test_logout` - Выход из системы

### test_routes.py (9 тестов)
- `test_index_page_loads` - Загрузка главной страницы
- `test_dashboard_requires_login` - Dashboard требует авторизации
- `test_dashboard_with_authenticated_user` - Dashboard для авторизованных
- `test_profile_requires_login` - Profile требует авторизации
- `test_profile_with_authenticated_user` - Profile для авторизованных
- `test_update_profile` - Обновление профиля
- `test_change_password` - Смена пароля
- `test_change_password_wrong_current` - Смена с неправильным текущим паролем
- `test_404_error` - Обработка ошибки 404

## Fixtures (conftest.py)

- `app` - Тестовое приложение Flask
- `client` - Тестовый клиент Flask
- `runner` - CLI runner
- `test_user` - Тестовый пользователь в БД
- `authenticated_client` - Аутентифицированный клиент

## Конфигурация тестов (TestConfig)

```python
TESTING = True
SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory БД
WTF_CSRF_ENABLED = False  # Отключаем CSRF для тестов
SECRET_KEY = 'test-secret-key'
```

## Проверка покрытия кода

```bash
# Генерация HTML отчета о покрытии
python -m pytest tests/ --cov=. --cov-report=html

# Открыть отчет в браузере
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
xdg-open htmlcov/index.html  # Linux
```

## Результаты тестирования

Все 24 теста успешно пройдены:
- ✓ 6 тестов моделей
- ✓ 9 тестов аутентификации  
- ✓ 9 тестов маршрутов

```
======================== 24 passed in 4.31s ========================
```

## Continuous Integration

Для настройки CI/CD можно использовать GitHub Actions:

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python -m pytest tests/ -v
```

## Отладка тестов

```bash
# Запуск с отладочным выводом
python -m pytest tests/ -v -s

# Остановка на первой ошибке
python -m pytest tests/ -x

# Повторный запуск только упавших тестов
python -m pytest tests/ --lf
```

## Дополнительные команды

```bash
# Список всех тестов без запуска
python -m pytest tests/ --collect-only

# Запуск с таймингом
python -m pytest tests/ --durations=10

# Параллельный запуск (требует pytest-xdist)
pip install pytest-xdist
python -m pytest tests/ -n auto
```

---

**Все тесты готовы к использованию и работают корректно!** ✅
