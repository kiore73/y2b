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

UPLOAD_INTERVAL_HOURS = int(os.getenv("UPLOAD_INTERVAL_HOURS", 3))

DATA_DIR = "data"
VIDEOS_DIR = os.path.join(DATA_DIR, "videos")
TOKENS_DIR = os.path.join(DATA_DIR, "tokens")
CLIENT_SECRETS = "client_secrets.json"

for d in [VIDEOS_DIR, TOKENS_DIR]:
    os.makedirs(d, exist_ok=True)
