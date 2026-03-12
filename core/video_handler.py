import os
import asyncio
import subprocess
import logging
from utils.config import FFMPEG_PATH, FFPROBE_PATH, OVERLAY_PATH, VIDEOS_DIR

class VideoProcessor:
    @staticmethod
    async def download_tiktok(url: str, output_name: str):
        file_path = os.path.join(VIDEOS_DIR, f"raw_{output_name}.mp4")
        cmd = ["yt-dlp", "-f", "bv*+ba/b", "--merge-output-format", "mp4", "-o", file_path, url]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise Exception(f"Ошибка загрузки TikTok: {stderr.decode()}")
        return file_path

    @staticmethod
    def _get_resolution(video_path):
        cmd = [FFPROBE_PATH, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", video_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Ошибка ffprobe: {result.stderr}")
        width, height = map(int, result.stdout.strip().split("x"))
        return width, height

    @staticmethod
    async def apply_overlay(input_path: str, output_name: str, position: str = "top"):
        output_path = os.path.join(VIDEOS_DIR, f"{output_name}.mp4")
        
        try:
            if not os.path.exists(OVERLAY_PATH):
                logging.warning(f"Оверлей не найден по пути {OVERLAY_PATH}, пропускаем наложение")
                # Если оверлея нет, просто переименовываем/перемещаем входной файл как "финальный"
                os.rename(input_path, output_path)
                return output_path

            loop = asyncio.get_event_loop()
            width, height = await loop.run_in_executor(None, VideoProcessor._get_resolution, input_path)
            
            # Настройки оверлея (можно вынести в .env)
            overlay_width = int(width * 1.75)
            overlay_height = int(overlay_width * 0.50)
            x_offset = int((width - overlay_width) / 1.7)
            y_offset = -100 if position == "top" else height - overlay_height + 100

            overlay_filter = (f"[1:v]scale={overlay_width}:{overlay_height},loop=-1:size=250:start=0,setpts=N/FRAME_RATE/TB[ol];"
                              f"[0:v][ol]overlay={x_offset}:{y_offset}:shortest=1")

            cmd = [
                FFMPEG_PATH, "-y", "-i", input_path, "-i", OVERLAY_PATH,
                "-filter_complex", overlay_filter,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k", output_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"Ошибка FFmpeg: {stderr.decode()}")

            return output_path

        finally:
            # Всегда удаляем исходный файл, если он еще существует и не является выходным
            if os.path.exists(input_path) and input_path != output_path:
                try:
                    os.remove(input_path)
                except Exception as e:
                    logging.error(f"Не удалось удалить временный файл {input_path}: {e}")
