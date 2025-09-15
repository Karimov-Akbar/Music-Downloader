import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from spotdl.download import Downloader
from spotdl.utils.search import parse_query

# 🔑 Токен берем из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def start(update, context):
    update.message.reply_text("Привет 👋 Отправь ссылку на трек Spotify!")


def download_track(url: str) -> str:
    """Скачивает трек и возвращает путь к файлу"""
    downloader = Downloader()
    search_results = parse_query(url)

    if not search_results:
        return None

    song = search_results[0]
    file_path = downloader.download(song, DOWNLOAD_DIR)
    return file_path


def handle_message(update, context):
    url = update.message.text.strip()

    if "spotify.com" not in url:
        update.message.reply_text("Отправь ссылку на трек Spotify 🎶")
        return

    update.message.reply_text("⏳ Скачиваю...")

    try:
        file_path = download_track(url)
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                update.message.reply_audio(f)
            os.remove(file_path)
        else:
            update.message.reply_text("❌ Ошибка при скачивании.")
    except Exception as e:
        update.message.reply_text(f"⚠️ Ошибка: {str(e)}")


def main():
    if not TELEGRAM_TOKEN:
        print("❌ Укажи TELEGRAM_TOKEN в переменных окружения!")
        return

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    port = int(os.getenv("PORT", 8443))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
