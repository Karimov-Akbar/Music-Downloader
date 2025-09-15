import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from spotdl import Spotdl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Загружаем токены и ключи из Railway переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not TELEGRAM_TOKEN or not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise ValueError("Не заданы TELEGRAM_TOKEN, SPOTIFY_CLIENT_ID или SPOTIFY_CLIENT_SECRET!")

# Инициализируем SpotDL клиент
spotdl_client = Spotdl(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
)

# Телеграм бот
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# /start
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! 🎵 Отправь ссылку на Spotify трек, и я скачаю его для тебя.")


# Обработка ссылок
@dp.message()
async def download_handler(message: types.Message):
    url = message.text.strip()

    if not url.startswith("https://open.spotify.com/track/"):
        await message.answer("⚠️ Отправь корректную ссылку на трек Spotify.")
        return

    try:
        await message.answer("⏳ Скачиваю трек, подожди немного...")

        # Скачиваем трек
        results = spotdl_client.search([url])
        song = results[0]
        file_path = spotdl_client.download(song)

        # Отправляем пользователю
        audio_file = FSInputFile(file_path)
        await message.answer_audio(audio_file)

        # Удаляем после отправки, чтобы не забивать Railway
        os.remove(file_path)

    except Exception as e:
        logging.error(f"Ошибка при скачивании {url}: {e}")
        await message.answer("❌ Произошла ошибка при загрузке трека. Попробуй позже.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
