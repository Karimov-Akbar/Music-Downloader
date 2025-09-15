from aiogram import Bot, Dispatcher, executor, types
from spotdl import Spotdl
import os

TOKEN = "ТВОЙ_ТОКЕН"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# создаем объект spotdl
spotdl = Spotdl()

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("Отправь ссылку на трек Spotify 🎵")

@dp.message_handler()
async def download_track(message: types.Message):
    url = message.text.strip()

    await message.answer("Скачиваю трек, подожди... ⏳")
    try:
        # качаем
        song, = spotdl.search([url])
        file_path = spotdl.download(song)

        if file_path and os.path.exists(file_path):
            await message.answer_document(open(file_path, "rb"))
            os.remove(file_path)  # очищаем
        else:
            await message.answer("Ошибка: Файл не найден после скачивания.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)