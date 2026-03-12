import os
import time
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from auth import get_authenticated_service
from uploader import upload_video
from utils import load_config, setup_logging, Database, move_to_archive

def process_channel(channel_config, config, db):
    channel_name = channel_config['name']
    video_dir = channel_config['video_dir']
    archive_dir = channel_config['archive_dir']
    
    logging.info(f"--- Проверка канала: {channel_name} ---")
    
    if not os.path.exists(video_dir):
        logging.warning(f"Папка {video_dir} не найдена. Пропускаем.")
        return

    # Получаем список .mp4 файлов
    videos = [f for f in os.listdir(video_dir) if f.lower().endswith('.mp4')]
    
    if not videos:
        logging.info(f"Нет новых видео в {video_dir}")
        return

    # Берем первый файл (очередь)
    video_file = videos[0]
    file_path = os.path.join(video_dir, video_file)

    # Проверка на дубликат по имени файла (можно заменить на хеш)
    if db.is_uploaded(video_file):
        logging.info(f"Файл {video_file} уже был загружен ранее. Перемещаем в архив.")
        move_to_archive(file_path, archive_dir)
        return

    # Авторизация
    try:
        youtube = get_authenticated_service(
            channel_name, 
            config['client_secrets_file'], 
            config['token_dir']
        )
    except Exception as e:
        logging.error(f"Ошибка авторизации для {channel_name}: {e}")
        return

    # Подготовка метаданных
    title = os.path.splitext(video_file)[0]
    # YouTube автоматически распознает вертикальное видео до 60с как Shorts,
    # но добавим хештег для уверенности.
    if "#shorts" not in title.lower():
        title += " #shorts"
    
    description = channel_config.get('default_description', "")
    tags = channel_config.get('default_tags', [])

    # Загрузка
    video_id = upload_video(youtube, file_path, title, description, tags)
    
    if video_id:
        db.mark_as_uploaded(video_file, channel_name)
        move_to_archive(file_path, archive_dir)
        logging.info(f"Успешно обработан файл: {video_file}")

def main():
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print(f"Ошибка: {config_path} не найден!")
        return

    config = load_config(config_path)
    setup_logging(config['log_file'])
    db = Database(config['database_file'])

    logging.info("Запуск планировщика YouTube Shorts Automation...")

    scheduler = BlockingScheduler()

    for channel in config['channels']:
        interval = channel.get('upload_interval_hours', 3)
        logging.info(f"Добавлена задача для канала {channel['name']} (каждые {interval} ч.)")
        
        # Запускаем сразу при старте и далее по интервалу
        scheduler.add_job(
            process_channel, 
            'interval', 
            hours=interval, 
            args=[channel, config, db],
            next_run_time=time.strftime('%Y-%m-%d %H:%M:%S') # Запуск прямо сейчас
        )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Завершение работы.")

if __name__ == "__main__":
    main()
