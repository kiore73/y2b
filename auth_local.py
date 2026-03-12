from core.youtube_client import YouTubeClient
import os

# Укажите названия ваших каналов здесь
channels = ["Колибри VPN", "marvel-shorts-ru", "classic-movies-ru"] 

for name in channels:
    print(f"Авторизация для: {name}")
    client = YouTubeClient(name)
    print(f"✅ Успешно! Файл создан в data/tokens/{name}_token.pickle")
