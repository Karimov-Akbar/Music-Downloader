import os
import logging
import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from spotdl import Spotdl

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not all([TELEGRAM_TOKEN, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET]):
    raise ValueError(
        "ОШИБКА: Не заданы обязательные переменные окружения: "
        "TELEGRAM_TOKEN, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET"
    )

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_message = (
        f"Привет, {user.first_name}!\n\n"
        "Я бот для скачивания музыки из Spotify.\n"
        "Просто отправь мне ссылку на трек, и я пришлю тебе аудиофайл."
    )
    await update.message.reply_html(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Чтобы скачать трек, просто отправьте мне ссылку на него из Spotify.\n"
        "Я найду его, скачаю и пришлю вам в виде аудиофайла."
    )
    await update.message.reply_text(help_text)


async def download_track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    url = message.text

    if "spotify.com/track/" not in url:
        await message.reply_text("Пожалуйста, отправьте корректную ссылку на трек Spotify.")
        return

    status_message = await message.reply_text("⏳ Обрабатываю ссылку...")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            temp_path = Path(temp_dir)
            await status_message.edit_text("🔍 Ищу и скачиваю трек... Это может занять до минуты.")

            spotdl_client = Spotdl(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                output_format="mp3",
                output=str(temp_path),
            )

            songs = spotdl_client.download([url])

            if not songs or not songs[0].downloaded_at:
                await status_message.edit_text("😕 Не удалось скачать этот трек. Возможно, он недоступен. Попробуйте другую ссылку.")
                return

            song = songs[0]
            downloaded_files = list(temp_path.glob("*.mp3"))
            if not downloaded_files:
                raise FileNotFoundError("Скачанный mp3 файл не найден во временной директории.")
            
            output_file = downloaded_files[0]

            await status_message.edit_text("✅ Трек скачан! Отправляю аудиофайл...")

            with open(output_file, 'rb') as audio_file:
                await context.bot.send_audio(
                    chat_id=message.chat_id,
                    audio=audio_file,
                    title=song.title,
                    performer=song.artist,
                    duration=int(song.duration or 0),
                    thumbnail=song.cover_url
                )

        except Exception as e:
            logger.error(f"Произошла ошибка при обработке ссылки {url}: {e}", exc_info=True)
            await status_message.edit_text("❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.")
        
        finally:
             await status_message.delete()
    



def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_track))

    logger.info("Бот запущен и готов к работе...")
    application.run_polling()


if __name__ == "__main__":
    main()