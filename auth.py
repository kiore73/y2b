import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Скоупы для работы с YouTube API (загрузка видео)
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service(channel_name, client_secrets_file, token_dir):
    """
    Авторизация конкретного канала и получение сервиса YouTube Data API.
    """
    if not os.path.exists(token_dir):
        os.makedirs(token_dir)

    token_file = os.path.join(token_dir, f"{channel_name}_token.pickle")
    credentials = None

    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            credentials = pickle.load(token)

    # Если токена нет или он истек
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print(f"Обновление токена для канала: {channel_name}")
            credentials.refresh(Request())
        else:
            print(f"Требуется новая авторизация для канала: {channel_name}")
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            credentials = flow.run_local_server(port=0)

        # Сохраняем токен
        with open(token_file, 'wb') as token:
            pickle.dump(credentials, token)

    return build('youtube', 'v3', credentials=credentials)
