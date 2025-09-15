import os
import asyncio
import logging
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# 📥 Функция для скачивания трека через spotdl (CLI)
async def download_track(url: str, output_dir: str = "downloads") -> str:
    os.makedirs(output_dir, exist_ok=True)
    # Формируем команду spotdl
    cmd = ["spotdl", "download", url, "--output", output_dir]

    # Запускаем процесс
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        logging.error(f"Ошибка spotdl: {stderr.decode()}")
        raise Exception(f"Ошибка при скачивании: {stderr.decode()}")

    # Находим скачанный файл в папке
    files = os.listdir(output_dir)
    if not files:
        raise Exception("Файл не найден после скачивания.")

    # Возвращаем путь к первому скачанному файлу
    return os.path.join(output_dir, files[0])


# 📲 Хэндлер на получение ссылки
@dp.message()
async def handle_message(message: types.Message):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("Отправь ссылку на трек Spotify 🎵")
        return

    await message.answer("Скачиваю трек, подожди... ⏳")

    try:
        file_path = await download_track(url)
        audio = FSInputFile(file_path)
        await message.answer_audio(audio)
        os.remove(file_path)  # удаляем после отправки
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())