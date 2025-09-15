from aiogram import Bot, Dispatcher, executor, types
from spotdl import Spotdl
import os

# токен телеграм-бота
TOKEN = os.getenv("BOT_TOKEN")  # В Railway через переменные окружения

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# создаём объект spotdl
spotdl = Spotdl()

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("Отправь ссылку на трек Spotify 🎵")

@dp.message_handler()
async def download_track(message: types.Message):
    url = message.text.strip()

    await message.answer("Скачиваю трек, подожди... ⏳")
    try:
        # ищем трек
        search_results = spotdl.search([url])
        if not search_results:
            await message.answer("Не удалось найти трек по ссылке ❌")
            return

        song = search_results[0]
        # качаем трек
        file_path = spotdl.download(song)

        if file_path and os.path.exists(file_path):
            await message.answer_document(open(file_path, "rb"))
            os.remove(file_path)  # очищаем после отправки
        else:
            await message.answer("Ошибка: Файл не найден после скачивания.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
