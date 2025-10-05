import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
from dotenv import load_dotenv
import yt_dlp
import tempfile
import glob

# Загружаем переменные окружения
load_dotenv()

# Telegram Bot Token
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветственное сообщение"""
    await update.message.reply_text(
        '🎵 Привет! Я бот для скачивания музыки.\n\n'
        'Отправь мне:\n'
        '• Название песни\n'
        '• Ссылку на YouTube\n'
        '• Ссылку на Spotify (найду на YouTube)\n\n'
        'Я найду и отправлю тебе музыку!'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет справку"""
    await update.message.reply_text(
        '📖 Как использовать:\n\n'
        '1. Отправь название песни или исполнителя\n'
        '2. Или отправь ссылку на YouTube/Spotify\n'
        '3. Получи музыку!\n\n'
        'Примеры:\n'
        '• "Imagine Dragons Believer"\n'
        '• https://www.youtube.com/watch?v=...\n'
        '• https://open.spotify.com/track/...'
    )

def download_track(query):
    """Синхронная функция для скачивания трека через yt-dlp"""
    try:
        # Создаём временную директорию
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')
        
        # Если это Spotify ссылка, извлекаем информацию и ищем на YouTube
        if 'spotify.com' in query:
            try:
                import re
                from spotipy import Spotify
                from spotipy.oauth2 import SpotifyClientCredentials
                
                # Получаем track ID из ссылки
                track_id = re.search(r'track/([a-zA-Z0-9]+)', query)
                if track_id:
                    # Инициализируем Spotify API
                    sp = Spotify(auth_manager=SpotifyClientCredentials(
                        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
                    ))
                    
                    # Получаем информацию о треке
                    track = sp.track(track_id.group(1))
                    artist = track['artists'][0]['name']
                    title = track['name']
                    
                    # Формируем поисковый запрос для YouTube
                    query = f"{artist} - {title}"
                    print(f"Spotify трек: {query}")
            except Exception as e:
                print(f"Не удалось получить инфо из Spotify: {e}")
                return None, None, None, None, "Не удалось обработать Spotify ссылку. Отправьте название песни."
        
        # Проверяем наличие FFmpeg (для локального запуска)
        import shutil
        has_ffmpeg = shutil.which('ffmpeg') is not None
        
        # Настройки yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'default_search': 'ytsearch1',
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_retries': 3,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate'
            },
            # Используем альтернативные методы извлечения
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'skip': ['hls', 'dash']
                }
            },
            # Попробуем использовать cookies из браузера (если доступны)
            'cookiesfrombrowser': ('chrome',) if has_ffmpeg else None,
        }
        
        # Добавляем конвертацию в MP3 только если есть FFmpeg
        if has_ffmpeg:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        print(f"Скачиваю: {query}")
        print(f"FFmpeg доступен: {has_ffmpeg}")
        
        # Пробуем разные источники
        search_queries = [
            query,  # Оригинальный запрос
            f"ytsearch:{query}",  # YouTube поиск
            f"ytsearch1:{query} audio",  # YouTube с уточнением "audio"
        ]
        
        last_error = None
        
        for search_query in search_queries:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Скачиваем
                    info = ydl.extract_info(search_query, download=True)
                    
                    # Получаем информацию о треке
                    if 'entries' in info:
                        # Это результат поиска
                        info = info['entries'][0]
                    
                    title = info.get('title', 'Unknown')
                    artist = info.get('artist', info.get('uploader', 'Unknown'))
                    duration = info.get('duration', 0)
                    
                    # Ищем скачанный файл (mp3, m4a, webm, opus)
                    audio_files = []
                    for ext in ['*.mp3', '*.m4a', '*.webm', '*.opus']:
                        audio_files.extend(glob.glob(os.path.join(temp_dir, ext)))
                    
                    if audio_files:
                        return audio_files[0], title, artist, duration, None
                    
            except Exception as e:
                last_error = str(e)
                print(f"Ошибка с запросом '{search_query}': {e}")
                continue
        
        # Если все попытки провалились
        if last_error:
            if 'Sign in to confirm' in last_error or 'bot' in last_error.lower():
                return None, None, None, None, "YouTube временно недоступен. Попробуйте другую песню или позже."
            return None, None, None, None, f"Не удалось скачать: {last_error[:200]}"
        
        return None, None, None, None, "Файл не был создан"
            
    except Exception as e:
        print(f"Ошибка: {e}")
        return None, None, None, None, str(e)

async def download_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает запрос на скачивание музыки"""
    user_input = update.message.text
    chat_id = update.message.chat_id
    
    # Отправляем сообщение о начале поиска
    status_msg = await update.message.reply_text('🔍 Ищу музыку...')
    
    try:
        await status_msg.edit_text('⬇️ Скачиваю...')
        
        # Запускаем скачивание в отдельном потоке
        file_path, title, artist, duration, error = await asyncio.to_thread(
            download_track, user_input
        )
        
        if error:
            await status_msg.edit_text(f'❌ Ошибка: {error[:150]}')
            return
        
        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text('❌ Не удалось скачать трек.')
            return
        
        # Получаем размер файла
        file_size = os.path.getsize(file_path)
        
        # Telegram ограничение: 50 МБ для ботов
        if file_size > 50 * 1024 * 1024:
            await status_msg.edit_text('❌ Файл слишком большой (>50 МБ)')
            try:
                os.remove(file_path)
            except:
                pass
            return
        
        await status_msg.edit_text('📤 Отправляю файл...')
        
        # Отправляем с увеличенным таймаутом
        with open(file_path, 'rb') as audio:
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=audio,
                title=title,
                performer=artist,
                duration=duration,
                read_timeout=120,
                write_timeout=120,
                connect_timeout=120
            )
        
        # Удаляем файл после отправки
        try:
            os.remove(file_path)
            # Удаляем временную директорию
            import shutil
            temp_dir = os.path.dirname(file_path)
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass
        
        await status_msg.delete()
            
    except Exception as e:
        error_msg = str(e)
        await status_msg.edit_text(f'❌ Ошибка: {error_msg[:150]}')

# Для Vercel webhook - синхронная версия
def webhook_handler_sync(body):
    """Синхронный обработчик webhook для Vercel"""
    import asyncio
    
    async def process():
        application = Application.builder().token(TOKEN).build()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_music))
        
        # Инициализация приложения
        await application.initialize()
        await application.start()
        
        # Обработка запроса
        update = Update.de_json(body, application.bot)
        await application.process_update(update)
        
        await application.stop()
        
        return {"statusCode": 200}
    
    # Запускаем в новом event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(process())
    finally:
        loop.close()

# Старый async webhook handler (оставляем для совместимости)
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

# Для локального запуска и Render.com
def main():
    """Запуск бота в режиме polling"""
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_music))
    
    print('🤖 Бот запущен!')
    print(f'🌐 Режим: Polling (для Render.com)')
    
    # Для Render Web Service - запускаем простой HTTP сервер в отдельном потоке
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Bot is running!')
        
        def log_message(self, format, *args):
            pass  # Отключаем логи HTTP сервера
    
    def run_http_server():
        port = int(os.getenv('PORT', 10000))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        print(f'🌐 HTTP сервер запущен на порту {port}')
        server.serve_forever()
    
    # Запускаем HTTP сервер в отдельном потоке
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Запускаем бота в основном потоке
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()