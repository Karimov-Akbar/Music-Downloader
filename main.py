import os
import logging
from uuid import uuid4
from pathlib import Path
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from spotdl import Spotdl

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Необходимо указать TELEGRAM_TOKEN в файле .env")

DOWNLOAD_PATH = Path("./downloads")
DOWNLOAD_PATH.mkdir(exist_ok=True)

spotdl_client = Spotdl(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    ffmpeg="/usr/bin/ffmpeg",
    output=f"{DOWNLOAD_PATH}/{{title}} - {{artist}}.mp3"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! 👋\n\nОтправь мне ссылку на трек, альбом или плейлист из Spotify, и я скачаю музыку для тебя.",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    if "open.spotify.com" not in message_text:
        await update.message.reply_text("Пожалуйста, отправьте корректную ссылку на Spotify.")
        return

    status_message = await update.message.reply_text("Получил ссылку. Начинаю загрузку... ⏳")

    try:
        songs = spotdl_client.download([message_text])

        if not songs:
            await status_message.edit_text("Не удалось найти или скачать треки по этой ссылке. 😔")
            return

        await status_message.edit_text(f"Скачано {len(songs)} трек(ов). Отправляю файлы... 🚀")

        for song in songs:
            if song and song.path and os.path.exists(song.path):
                logger.info(f"Отправка файла: {song.path}")
                try:
                    await context.bot.send_audio(
                        chat_id=update.effective_chat.id,
                        audio=open(song.path, "rb"),
                        title=song.title,
                        performer=song.artist,
                        duration=int(song.duration),
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке файла {song.path}: {e}")
                    await update.message.reply_text(f"Не смог отправить файл: {song.display_name}. Возможно, он слишком большой.")
                finally:
                    os.remove(song.path)
            else:
                logger.warning(f"Файл для песни {song.display_name} не найден.")

        await status_message.edit_text("Все готово! ✅")

    except Exception as e:
        logger.error(f"Произошла ошибка при обработке ссылки: {e}")
        await status_message.edit_text("Ой, что-то пошло не так. Попробуйте другую ссылку. 🛠️")


def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()