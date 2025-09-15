import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from yt_dlp import YoutubeDL
import spotdl

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не найден в переменных окружения!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Привет! 🎶 Пришли ссылку на трек из Spotify, и я попробую скачать его.")

@dp.message()
async def download_track(message: types.Message):
    url = message.text.strip()

    if not url.startswith("https://open.spotify.com/"):
        await message.answer("⚠️ Это не похоже на ссылку Spotify.")
        return

    await message.answer("Скачиваю трек, подожди... ⏳")

    try:
        # spotdl: получаем название + youtube-источник
        song = spotdl.Song.from_url(url)

        output_file = f"{song.display_name}.mp3"

        # качаем через yt-dlp
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_file,
            "quiet": True,
            "noplaylist": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([song.youtube_url])

        # отправляем если файл есть
        if os.path.exists(output_file):
            await message.answer_document(types.FSInputFile(output_file))
            os.remove(output_file)
        else:
            await message.answer("❌ Ошибка: файл не найден после скачивания.")

    except Exception as e:
        await message.answer(f"⚠️ Ошибка при скачивании: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())