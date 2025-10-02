import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from spotdl import Spotdl
import tempfile
import asyncio

# Инициализация Spotdl
spotdl = Spotdl(client_id=os.getenv('SPOTIFY_CLIENT_ID'), 
                client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'))

# Telegram Bot Token
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветственное сообщение"""
    await update.message.reply_text(
        '🎵 Привет! Я бот для скачивания музыки.\n\n'
        'Отправь мне:\n'
        '• Название песни\n'
        '• Ссылку на Spotify трек\n'
        '• Ссылку на YouTube\n\n'
        'Я найду и отправлю тебе музыку!'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет справку"""
    await update.message.reply_text(
        '📖 Как использовать:\n\n'
        '1. Отправь название песни или исполнителя\n'
        '2. Или отправь ссылку на Spotify/YouTube\n'
        '3. Получи музыку!\n\n'
        'Примеры:\n'
        '• "Imagine Dragons Believer"\n'
        '• https://open.spotify.com/track/...'
    )

async def download_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает запрос на скачивание музыки"""
    user_input = update.message.text
    chat_id = update.message.chat_id
    
    # Отправляем сообщение о начале поиска
    status_msg = await update.message.reply_text('🔍 Ищу музыку...')
    
    try:
        # Создаем временную директорию
        with tempfile.TemporaryDirectory() as temp_dir:
            # Поиск и скачивание
            songs = spotdl.search([user_input])
            
            if not songs:
                await status_msg.edit_text('❌ Ничего не найдено. Попробуй другой запрос.')
                return
            
            song = songs[0]
            await status_msg.edit_text(f'⬇️ Скачиваю: {song.name} - {song.artist}...')
            
            # Скачиваем трек
            downloaded, errors = spotdl.download(song)
            
            if errors:
                await status_msg.edit_text(f'❌ Ошибка скачивания: {errors[0]}')
                return
            
            # Отправляем файл
            file_path = downloaded[0] if downloaded else None
            
            if file_path and os.path.exists(file_path):
                await status_msg.edit_text('📤 Отправляю файл...')
                
                with open(file_path, 'rb') as audio:
                    await context.bot.send_audio(
                        chat_id=chat_id,
                        audio=audio,
                        title=song.name,
                        performer=song.artist,
                        duration=song.duration
                    )
                
                await status_msg.delete()
            else:
                await status_msg.edit_text('❌ Не удалось скачать файл.')
                
    except Exception as e:
        await status_msg.edit_text(f'❌ Произошла ошибка: {str(e)}')

# Для Vercel webhook
async def webhook_handler(request):
    """Обработчик webhook для Vercel"""
    application = Application.builder().token(TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_music))
    
    # Инициализация приложения
    await application.initialize()
    await application.start()
    
    # Обработка запроса
    body = await request.json()
    update = Update.de_json(body, application.bot)
    await application.process_update(update)
    
    return {"statusCode": 200}

# Для локального запуска
def main():
    """Запуск бота в режиме polling (для локальной разработки)"""
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_music))
    
    print('🤖 Бот запущен!')
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()