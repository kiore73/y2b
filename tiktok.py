import os
import subprocess
import sys

# ---------------- Настройки ----------------
BASE_DIR = r"E:\tiktok_auto"
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OVERLAY = os.path.join(BASE_DIR, "assets", "overlay.mov")
LINKS_FILE = os.path.join(BASE_DIR, "links.txt")
FFMPEG_PATH = r"C:\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe"
FFPROBE_PATH = FFMPEG_PATH.replace("ffmpeg.exe", "ffprobe.exe")
POSITION = "top"  # "top" или "bottom"
# -------------------------------------------

# Создание папок
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Проверка overlay
if not os.path.exists(OVERLAY):
    print(f"❌ Оверлей не найден: {OVERLAY}")
    sys.exit(1)

# Чтение ссылок
if not os.path.exists(LINKS_FILE):
    print(f"❌ Файл ссылок не найден: {LINKS_FILE}")
    sys.exit(1)

with open(LINKS_FILE, "r", encoding="utf-8") as f:
    links = [l.strip() for l in f if l.strip()]

if not links:
    print("❌ Нет ссылок для скачивания!")
    sys.exit(1)

# ---------------- Функция для получения разрешения видео ----------------
def get_resolution(video):
    cmd = [
        FFPROBE_PATH,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0:s=x",
        video
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    width, height = map(int, result.stdout.strip().split("x"))
    return width, height

# ---------------- 1️⃣ Скачивание видео ----------------
for i, link in enumerate(links, 1):
    out_file = os.path.join(INPUT_DIR, f"video_{i}.mp4")
    print(f"⬇ Скачиваем {link} -> {out_file}")
    try:
        subprocess.run([
            "yt-dlp",
            "-f", "bv*+ba/b",
            "--merge-output-format", "mp4",
            "-o", out_file,
            link
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при скачивании {link}: {e}")
        continue

print("✔ Все видео скачаны.")

# ---------------- 2️⃣ Наложение overlay ----------------
for filename in sorted(os.listdir(INPUT_DIR)):
    if not filename.lower().endswith(".mp4"):
        continue

    input_path = os.path.join(INPUT_DIR, filename)
    output_path = os.path.join(OUTPUT_DIR, f"final_{filename}")

    # Получаем разрешение видео
    width, height = get_resolution(input_path)

    # Масштабируем overlay пропорционально видео
    overlay_width = int(width * 1.75)       # 50% ширины видео
    overlay_height = int(overlay_width * 0.50)  # 75% ширины видео
    x_offset = int((width - overlay_width) / 1.7)  # по центру горизонтально
    y_offset = -100 if POSITION == "top" else height - overlay_height - -100

    # FFmpeg фильтр: масштабируем overlay и повторяем на всю длину
    overlay_filter = (
        f"[1:v]scale={overlay_width}:{overlay_height},"
        f"loop=-1:size=250:start=0,setpts=N/FRAME_RATE/TB[ol];"
        f"[0:v][ol]overlay={x_offset}:{y_offset}:shortest=1"
    )

    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", input_path,
        "-i", OVERLAY,
        "-filter_complex", overlay_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ]

    print(f"🎬 Обрабатываем {filename} ({width}x{height}) -> {output_path}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при обработке {filename}: {e}")
        continue

print("✔ Все видео обработаны и overlay точно наложен.")
