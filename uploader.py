import os
import logging
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

def upload_video(youtube, file_path, title, description, tags):
    """
    Загрузка видео через YouTube Data API v3.
    """
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '22'  # Категория "Люди и блоги"
        },
        'status': {
            'privacyStatus': 'public',  # Публичный доступ
            'selfDeclaredMadeForKids': False
        }
    }

    # Использование MediaFileUpload для возобновляемой загрузки
    insert_request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
    )

    logging.info(f"Начало загрузки: {file_path}")
    
    response = None
    try:
        while response is None:
            status, response = insert_request.next_chunk()
            if status:
                logging.info(f"Загружено {int(status.progress() * 100)}%")
        
        logging.info(f"Видео успешно загружено! ID: {response['id']}")
        return response['id']
    except HttpError as e:
        logging.error(f"Произошла ошибка API: {e}")
        return None
    except Exception as e:
        logging.error(f"Произошла ошибка при загрузке: {e}")
        return None
