#!/bin/bash
# Скрипт быстрого старта для локальной разработки

set -e

echo "🚀 Flask Auth App - Quick Start"
echo "================================"
echo ""

# Проверка Python версии
echo "📋 Проверка Python версии..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version"

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
    echo "✓ Виртуальное окружение создано"
fi

# Активация виртуального окружения
echo ""
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate || . venv/Scripts/activate
echo "✓ Виртуальное окружение активировано"

# Обновление pip
echo ""
echo "⬆️  Обновление pip..."
pip install --upgrade pip setuptools wheel -q
echo "✓ pip обновлён"

# Установка зависимостей
echo ""
echo "📦 Установка зависимостей..."
pip install -r requirements.txt -q
echo "✓ Зависимости установлены"

# Создание .env файла
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Создание .env файла..."
    cat > .env << EOF
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=sqlite:///instance/app.db
REDIS_URL=redis://localhost:6379/0
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
EOF
    echo "✓ .env файл создан"
fi

# Создание необходимых директорий
echo ""
echo "📁 Создание директорий..."
mkdir -p instance logs backups static/uploads
echo "✓ Директории созданы"

# Инициализация базы данных
echo ""
echo "🗄️  Инициализация базы данных..."
python3 << EOF
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print("✓ База данных инициализирована")
EOF

# Проверка Redis (опционально)
echo ""
echo "🔍 Проверка Redis..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✓ Redis доступен"
    else
        echo "⚠️  Redis не запущен (запустите: redis-server)"
    fi
else
    echo "⚠️  Redis не установлен (опционально, но рекомендуется)"
fi

echo ""
echo "✅ Установка завершена!"
echo ""
echo "🎯 Следующие шаги:"
echo "   1. Активируйте виртуальное окружение:"
echo "      Linux/Mac: source venv/bin/activate"
echo "      Windows: venv\\Scripts\\activate"
echo ""
echo "   2. Запустите приложение:"
echo "      python run.py"
echo ""
echo "   3. Откройте браузер:"
echo "      http://localhost:5000"
echo ""
echo "📚 Дополнительные команды:"
echo "   make help        - Показать все команды"
echo "   make test        - Запустить тесты"
echo "   make create-admin - Создать администратора"
echo ""
