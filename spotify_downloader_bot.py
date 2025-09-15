import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from spotdl import Spotdl
from spotdl.types.song import Song

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Берем токен из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Не найден TELEGRAM_TOKEN в переменных окружения")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# создаём клиента spotdl
spotdl_client = Spotdl()


async def download_track(url: str) -> str | None:
    try:
        song: Song = await spotdl_client.song.from_url(url)
        path = await spotdl_client.downloader.download_song(song)
        return path
    except Exception as e:
        logger.error(f"Ошибка при загрузке трека: {e}")
        return None


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Отправь мне ссылку на трек Spotify, и я скачаю его для тебя 🎵")


@dp.message()
async def handle_message(message: types.Message):
    url = message.text.strip()
    if "open.spotify.com/track" not in url:
        await message.answer("Пожалуйста, пришли корректную ссылку на трек Spotify 🎧")
        return

    await message.answer("⏳ Загружаю трек, подожди немного...")

    file_path = await download_track(url)
    if file_path and os.path.exists(file_path):
        audio = FSInputFile(file_path)
        await message.answer_audio(audio)
        os.remove(file_path)  # удаляем после отправки
    else:
        await message.answer("❌ Не удалось скачать трек. Попробуй позже.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())