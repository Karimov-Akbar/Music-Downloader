# Базовый образ Python
FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Устанавливаем зависимости системы (чтобы ytdlp, ffmpeg работали)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы проекта
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Переменная окружения для запуска в Docker
ENV PYTHONUNBUFFERED=1

# Запуск бота
CMD ["python", "spotify_downloader_bot.py"]
