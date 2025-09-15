import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import spotdl

# Берем токен из Railway Variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не найден в переменных окружения!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Привет! 🎶 Пришли ссылку на трек из Spotify, и я его скачаю.")

# Обработка ссылки на Spotify
@dp.message()
async def download_track(message: types.Message):
    url = message.text.strip()

    if not url.startswith("https://open.spotify.com/"):
        await message.answer("⚠️ Это не похоже на ссылку Spotify.")
        return

    await message.answer("Скачиваю трек, подожди... ⏳")

    try:
        # Указываем временный путь для файла
        output_file = "song.mp3"

        # Скачивание через spotdl
        os.system(f"spotdl download {url} --output {output_file}")

        # Проверяем, появился ли файл
        if os.path.exists(output_file):
            await message.answer_document(types.FSInputFile(output_file))
            os.remove(output_file)
        else:
            await message.answer("❌ Ошибка: Файл не найден после скачивания.")

    except Exception as e:
        await message.answer(f"⚠️ Ошибка при скачивании: {e}")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
