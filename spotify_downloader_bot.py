import asyncio
import os
from spotdl import Spotdl
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# токен Telegram бота
TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# создаём объект SpotDL (он сам подтянет нужные провайдеры)
spotdl = Spotdl()

async def download_song(url: str) -> str:
    """Скачать песню по ссылке и вернуть путь к файлу"""
    songs = await spotdl.search([url])
    if not songs:
        return None
    file = await spotdl.download(songs[0])
    return file

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("Привет! Отправь мне ссылку на песню в Spotify 🎵")

@dp.message_handler()
async def handle_message(message: types.Message):
    url = message.text.strip()

    if "spotify.com" not in url:
        await message.reply("Отправь ссылку на трек Spotify 🙂")
        return

    await message.reply("Скачиваю... ⏳")

    try:
        file_path = await download_song(url)
        if file_path:
            await message.reply_document(open(file_path, "rb"))
        else:
            await message.reply("Не удалось найти трек 😢")
    except Exception as e:
        await message.reply(f"Ошибка при скачивании: {e}")

if __name__ == "__main__":
    # aiogram работает в asyncio, так что всё ок
    executor.start_polling(dp, skip_updates=True)