import os
import subprocess
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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
            process = subprocess.run(['spotdl', message_text], capture_output=True, text=True, check=True)
            
            output_lines = process.stdout.splitlines()
            downloaded_file_path = ""
            for line in output_lines:
                if "Downloaded" in line:
                    parts = line.split('"')
                    if len(parts) > 1:
                        downloaded_file_path = parts[1]
                        break
            
            if downloaded_file_path and os.path.exists(downloaded_file_path):
                with open(downloaded_file_path, 'rb') as audio_file:
                    await update.message.reply_audio(audio=audio_file, title=os.path.basename(downloaded_file_path))
                os.remove(downloaded_file_path)
            else:
                await update.message.reply_text('Не удалось найти скачанный файл.')

        except subprocess.CalledProcessError as e:
            await update.message.reply_text(f"Ошибка при скачивании: {e.stderr}")
        except Exception as e:
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