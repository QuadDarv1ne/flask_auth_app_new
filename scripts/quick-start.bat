@echo off
REM Скрипт быстрого старта для Windows

echo.
echo ========================================
echo   Flask Auth App - Quick Start
echo ========================================
echo.

REM Проверка Python
echo Проверка Python версии...
python --version
if errorlevel 1 (
    echo Ошибка: Python не установлен!
    echo Установите Python с https://python.org
    pause
    exit /b 1
)
echo OK Python установлен
echo.

REM Создание виртуального окружения
if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
    echo OK Виртуальное окружение создано
    echo.
)

REM Активация виртуального окружения
echo Активация виртуального окружения...
call venv\Scripts\activate.bat
echo OK Виртуальное окружение активировано
echo.

REM Обновление pip
echo Обновление pip...
python -m pip install --upgrade pip setuptools wheel -q
echo OK pip обновлён
echo.

REM Установка зависимостей
echo Установка зависимостей...
pip install -r requirements.txt -q
echo OK Зависимости установлены
echo.

REM Создание .env файла
if not exist ".env" (
    echo Создание .env файла...
    (
        echo FLASK_APP=run.py
        echo FLASK_ENV=development
        echo SECRET_KEY=dev-secret-key-change-in-production
        echo DATABASE_URL=sqlite:///instance/app.db
        echo REDIS_URL=redis://localhost:6379/0
        echo MAIL_SERVER=smtp.gmail.com
        echo MAIL_PORT=587
        echo MAIL_USE_TLS=true
    ) > .env
    echo OK .env файл создан
    echo.
)

REM Создание директорий
echo Создание директорий...
if not exist "instance" mkdir instance
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups
if not exist "static\uploads" mkdir static\uploads
echo OK Директории созданы
echo.

REM Инициализация базы данных
echo Инициализация базы данных...
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('OK База данных инициализирована')"
echo.

echo ========================================
echo   Установка завершена!
echo ========================================
echo.
echo Следующие шаги:
echo.
echo   1. Запустите приложение:
echo      python run.py
echo.
echo   2. Откройте браузер:
echo      http://localhost:5000
echo.
echo   3. Дополнительные команды:
echo      python run.py create-admin  - Создать администратора
echo      pytest tests/               - Запустить тесты
echo.
echo Нажмите любую клавишу для выхода...
pause > nul
