import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
FFPROBE_PATH = os.getenv("FFPROBE_PATH", "ffprobe")
OVERLAY_PATH = os.getenv("OVERLAY_PATH")

DEFAULT_TITLE = os.getenv("DEFAULT_TITLE", "Shorts #shorts")
DEFAULT_DESCRIPTION = os.getenv("DEFAULT_DESCRIPTION", "")
PROXY = os.getenv("PROXY") # socks5://user:pass@ip:port or http://...

UPLOAD_INTERVAL_HOURS = int(os.getenv("UPLOAD_INTERVAL_HOURS", 3))

DATA_DIR = "data"
VIDEOS_DIR = os.path.join(DATA_DIR, "videos")
TOKENS_DIR = os.path.join(DATA_DIR, "tokens")
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")
CLIENT_SECRETS = "client_secrets.json"

OVERLAY_POSITION = os.getenv("OVERLAY_POSITION", "top") # top or bottom

for d in [VIDEOS_DIR, TOKENS_DIR, ARCHIVE_DIR]:
    os.makedirs(d, exist_ok=True)

def get_channels():
    """Возвращает список доступных каналов на основе токенов в data/tokens/"""
    channels = []
    if os.path.exists(TOKENS_DIR):
        for f in os.listdir(TOKENS_DIR):
            if f.endswith("_token.pickle"):
                channels.append(f.replace("_token.pickle", ""))
    return channels if channels else ["Default_Channel"]
