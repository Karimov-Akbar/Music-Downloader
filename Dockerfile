# Используем официальный образ Python в качестве основы
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Обновляем список пакетов и устанавливаем системные зависимости, включая ffmpeg
# --no-install-recommends не устанавливает необязательные пакеты для экономии места
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл с зависимостями Python в контейнер
COPY requirements.txt .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы проекта (наш .py скрипт)
COPY . .

# Команда для запуска приложения при старте контейнера
CMD ["python", "spotify_downloader_bot.py"]
