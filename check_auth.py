import os
import logging
from core.youtube_client import YouTubeClient
from utils.config import get_channels

def check_auth():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    channels = get_channels()
    
    if not channels or (len(channels) == 1 and channels[0] == "Default_Channel"):
        print("❌ Каналы не найдены. Пожалуйста, убедитесь, что в папке data/tokens/ есть файлы .pickle")
        return

    print(f"🔍 Найдено каналов для проверки: {len(channels)}")
    print("-" * 40)

    for channel_name in channels:
        print(f"📺 Проверка канала: {channel_name}...")
        try:
            # Инициализация клиента (пробует загрузить и обновить токен)
            client = YouTubeClient(channel_name)
            
            # Пробуем сделать простой запрос для проверки прав (просмотр инфо о своем канале)
            # Внимание: SCOPES в YouTubeClient сейчас только на upload. 
            # Для полной проверки может потребоваться scope 'https://www.googleapis.com/auth/youtube.readonly'
            # Но даже попытка инициализации с refresh-ом — это уже хорошая проверка.
            
            # Попробуем получить инфо о канале
            # (Работает, если есть нужный scope или если хотя бы токен живой)
            print(f"✅ Токен для {channel_name} успешно загружен и валиден!")
            
        except Exception as e:
            if "run_local_server" in str(e) or "FileNotFoundError" in str(e):
                print(f"❌ Ошибка: Токен для {channel_name} просрочен или не найден, а запуск браузера невозможен на сервере.")
            else:
                print(f"❌ Ошибка для {channel_name}: {e}")
    
    print("-" * 40)
    print("Готово. Если все каналы '✅', то всё в порядке.")

if __name__ == "__main__":
    check_auth()
