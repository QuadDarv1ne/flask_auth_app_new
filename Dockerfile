# Multi-stage build для Flask Auth App

# Stage 1: Builder - установка зависимостей
FROM python:3.11-slim as builder

# Установка рабочей директории
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование файла зависимостей
COPY requirements.txt .

# Установка Python зависимостей в локальную директорию
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime - создание финального образа
FROM python:3.11-slim

# Создание непривилегированного пользователя
RUN groupadd -r flaskgroup && useradd -r -g flaskgroup flaskuser

# Установка рабочей директории
WORKDIR /app

# Установка curl для healthcheck
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование установленных зависимостей из builder stage
COPY --from=builder /root/.local /home/flaskuser/.local

# Установка правильных прав доступа
RUN chown -R flaskuser:flaskgroup /home/flaskuser/.local

# Копирование всех файлов проекта
COPY --chown=flaskuser:flaskgroup . .

# Создание директории для базы данных
RUN mkdir -p instance && chown -R flaskuser:flaskgroup instance

# Переменные окружения
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PATH=/home/flaskuser/.local/bin:$PATH

# Открытие порта
EXPOSE 5000

# Переключение на непривилегированного пользователя
USER flaskuser

# Инициализация БД и запуск приложения
CMD ["sh", "-c", "python init_db.py && python app.py"]