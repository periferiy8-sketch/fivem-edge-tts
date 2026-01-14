FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей + проверка git
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libsndfile1 \
    && echo "✅ Пакеты установлены" \
    && git --version \
    && echo "✅ Git доступен" \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем основной скрипт
COPY app.py .

# Запуск сервера
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]