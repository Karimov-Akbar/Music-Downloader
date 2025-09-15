FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
 && pip uninstall -y spotdl \
 && pip install -r requirements.txt

COPY . .

CMD ["python", "spotify_downloader_bot.py"]