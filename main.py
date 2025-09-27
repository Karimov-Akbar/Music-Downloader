import os
import subprocess
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в .env файле!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Отправь мне ссылку на трек из Spotify.')

async def download_song(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    if "open.spotify.com/track/" in message_text:
        await update.message.reply_text('Скачиваю трек, пожалуйста, подождите...')

        try:
            command = ['spotdl', message_text]
            logger.info(f"Запускаю команду: {' '.join(command)}")

            process = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=True
            )

            logger.info(f"Вывод spotdl (stdout): {process.stdout}")

            output_lines = process.stdout.splitlines()
            downloaded_file_path = ""
            for line in output_lines:
                if "Downloaded" in line:
                    parts = line.split('"')
                    if len(parts) > 1:
                        downloaded_file_path = parts[1].strip()
                        break
            
            if downloaded_file_path and os.path.exists(downloaded_file_path):
                logger.info(f"Отправляю файл: {downloaded_file_path}")
                with open(downloaded_file_path, 'rb') as audio_file:
                    await update.message.reply_audio(audio=audio_file, title=os.path.basename(downloaded_file_path))
                os.remove(downloaded_file_path)
            else:
                logger.warning(f"Файл не найден после скачивания. Вывод spotdl: {process.stdout}")
                await update.message.reply_text('Не удалось найти скачанный файл после завершения процесса.')

        except subprocess.CalledProcessError as e:
            error_message = f"Процесс spotdl завершился с ошибкой.\n"
            error_message += f"Код возврата: {e.returncode}\n"
            error_message += f"Stdout: {e.stdout}\n"
            error_message += f"Stderr: {e.stderr}"
            
            logger.error(error_message)
            await update.message.reply_text(f"Ошибка при скачивании. Stderr: {e.stderr}")
            
        except Exception as e:
            logger.error(f"Произошла непредвиденная ошибка: {e}", exc_info=True)
            await update.message.reply_text(f"Произошла непредвиденная ошибка: {e}")
    else:
        await update.message.reply_text('Пожалуйста, отправьте корректную ссылку на трек Spotify.')

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_song))
    application.run_polling()

if __name__ == '__main__':
    main()