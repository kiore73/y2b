import asyncio
import logging
from scheduler import upload_job

async def force_test():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("🚀 Запуск принудительной загрузки видео...")
    await upload_job()
    logging.info("🏁 Тест завершен.")

if __name__ == "__main__":
    asyncio.run(force_test())
