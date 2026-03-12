import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncioScheduler
from core.db_manager import DBManager
from core.youtube_client import YouTubeClient
from utils.config import UPLOAD_INTERVAL_HOURS, ADMIN_ID
from aiogram import Bot

# Инициализация для уведомлений
from utils.config import BOT_TOKEN, ADMIN_ID, UPLOAD_INTERVAL_HOURS, ARCHIVE_DIR
bot = Bot(token=BOT_TOKEN)
db = DBManager()

import os
import shutil

async def upload_job():
    logging.info("--- Запуск фоновой проверки очереди YouTube ---")
    
    stats = db.get_queue_stats()
    if not stats:
        logging.info("Очередь пуста.")
        return

    for channel_name in stats.keys():
        next_video = db.get_next_for_channel(channel_name)
        if next_video:
            logging.info(f"Загрузка для {channel_name}: {next_video['title']}")
            file_path = next_video['file_path']
            
            if not os.path.exists(file_path):
                logging.error(f"Файл не найден: {file_path}")
                db.update_status(next_video['id'], 'error', 'File not found')
                continue

            try:
                client = YouTubeClient(channel_name)
                video_id = await client.upload(
                    file_path=file_path,
                    title=next_video['title'],
                    description=next_video['description']
                )
                
                db.update_status(next_video['id'], 'uploaded')
                
                # Перемещаем в архив
                try:
                    dest = os.path.join(ARCHIVE_DIR, f"{channel_name}_{os.path.basename(file_path)}")
                    shutil.move(file_path, dest)
                except Exception as e:
                    logging.warning(f"Не удалось переместить файл в архив: {e}")

                await bot.send_message(ADMIN_ID, f"✅ Видео '{next_video['title']}' успешно загружено на {channel_name}!\nID: {video_id}")
                
            except Exception as e:
                logging.error(f"Ошибка при загрузке на {channel_name}: {e}")
                db.update_status(next_video['id'], 'error', str(e))
                await bot.send_message(ADMIN_ID, f"❌ Ошибка загрузки на {channel_name}: {e}")
        
        # Проверка остатка в очереди
        if stats[channel_name] <= 1:
            await bot.send_message(ADMIN_ID, f"⚠️ Предупреждение: Очередь для {channel_name} почти пуста!")

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
    )
    scheduler = AsyncioScheduler()
    # Запуск раз в 3 часа. Можно изменить для теста на раз в минуту (minutes=1)
    scheduler.add_job(upload_job, 'interval', hours=UPLOAD_INTERVAL_HOURS)
    scheduler.start()
    
    logging.info(f"Планировщик запущен. Интервал: {UPLOAD_INTERVAL_HOURS} ч.")
    
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
