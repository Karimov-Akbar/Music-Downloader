import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from spotdl import Spotdl
import os

# токен телеграм-бота
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# создаём объект spotdl
spotdl = Spotdl()

@dp.message(commands=["start"])
async def start_cmd(message: Message):
    await message.answer("Отправь ссылку на трек Spotify 🎵")

@dp.message()
async def download_track(message: Message):
    url = message.text.strip()

    await message.answer("Скачиваю трек, подожди... ⏳")
    try:
        # ищем трек
        search_results = spotdl.search([url])
        if not search_results:
            await message.answer("Не удалось найти трек по ссылке ❌")
            return

        song = search_results[0]
        file_path = spotdl.download(song)

        if file_path and os.path.exists(file_path):
            await message.answer_document(open(file_path, "rb"))
            os.remove(file_path)
        else:
            await message.answer("Ошибка: Файл не найден после скачивания.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
