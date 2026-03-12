import os
import pickle
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from utils.config import CLIENT_SECRETS, TOKENS_DIR

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

class YouTubeClient:
    def __init__(self, channel_name):
        self.channel_name = channel_name
        self.token_file = os.path.join(TOKENS_DIR, f"{channel_name}_token.pickle")
        self.service = self._authenticate()

    def _authenticate(self):
        credentials = None
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                credentials = pickle.load(token)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                if not os.path.exists(CLIENT_SECRETS):
                    raise FileNotFoundError(f"Файл {CLIENT_SECRETS} не найден!")
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
                credentials = flow.run_local_server(port=0)
            with open(self.token_file, 'wb') as token:
                pickle.dump(credentials, token)
        return build('youtube', 'v3', credentials=credentials)

    async def upload(self, file_path, title, description, tags=None):
        if tags is None: tags = ["shorts"]
        body = {'snippet': {'title': title, 'description': description, 'tags': tags, 'categoryId': '22'}, 'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}}
        insert_request = self.service.videos().insert(part=','.join(body.keys()), body=body, media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True))
        response = None
        while response is None:
            status, response = insert_request.next_chunk()
        return response.get('id')
