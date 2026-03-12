import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.config import BOT_TOKEN, ADMIN_IDS, DEFAULT_TITLE, DEFAULT_DESCRIPTION, get_channels, OVERLAY_POSITION
from core.db_manager import DBManager
from core.video_handler import VideoProcessor

# Инициализация (перенесено в main для стабильности)
dp = Dispatcher()
db = DBManager()

# Middleware для проверки ADMIN_IDS
async def admin_check_middleware(handler, event, data):
    if event.from_user.id not in ADMIN_IDS:
        await event.answer("⛔️ У вас нет доступа к этому боту.")
        return
    return await handler(event, data)

class UploadStates(StatesGroup):
    waiting_for_metadata = State()
    choosing_channel = State()

# Мы будем передавать bot через контекст или использовать глобальную переменную осторожно
# Но лучше инициализировать в main
bot_instance: Bot = None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🚀 **YouTube Shorts Automation Bot**\n\n"
        "Отправь мне ссылку на TikTok или видеофайл.\n"
        "Команды:\n"
        "/queue — Посмотреть очередь\n"
        "/clear — Очистить очередь"
    )

@dp.message(Command("queue"))
async def cmd_queue(message: types.Message):
    queue = db.get_full_queue()
    if not queue:
        return await message.answer("📭 Очередь пуста.")
    
    text = "📂 **Текущая очередь:**\n\n"
    for item in queue:
        text += f"🔹 {item['id']}: {item['title']} ({item['channel_name']})\n"
    await message.answer(text)

@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    count = db.clear_queue()
    await message.answer(f"🗑 Очередь очищена. Удалено задач: {count}")

@dp.message(F.text.startswith("http"))
@dp.message(F.video)
async def handle_video_input(message: types.Message, state: FSMContext, bot: Bot):
    msg = await message.answer("🎬 Начинаю обработку видео...")
    
    try:
        if message.text:
            raw_path = await VideoProcessor.download_tiktok(message.text, str(message.message_id))
        else:
            video = message.video
            raw_path = f"data/videos/raw_{message.message_id}.mp4"
            await bot.download(video, destination=raw_path)

        final_path = await VideoProcessor.apply_overlay(raw_path, f"final_{message.message_id}", position=OVERLAY_POSITION)
        await state.update_data(file_path=final_path)
        
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Использовать стандартные", callback_data="use_default")
        ]])
        
        await msg.edit_text("✅ Видео обработано. Введи название и описание через '|' (например: Заголовок | Описание) или нажми кнопку ниже:", reply_markup=kb)
        await state.set_state(UploadStates.waiting_for_metadata)
        
    except Exception as e:
        error_msg = str(e)[:1000]
        logging.error(f"Error handling video: {e}", exc_info=True)
        await msg.edit_text(f"❌ Произошла ошибка: {error_msg}")

@dp.callback_query(F.data == "use_default")
async def use_default_metadata(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(title=DEFAULT_TITLE, description=DEFAULT_DESCRIPTION)
    await show_channel_selection(callback.message, state)
    await callback.answer()

@dp.message(UploadStates.waiting_for_metadata)
async def process_metadata(message: types.Message, state: FSMContext):
    if message.text and "|" in message.text:
        title, desc = message.text.split("|", 1)
        await state.update_data(title=title.strip(), description=desc.strip())
    else:
        text = message.text.strip() if message.text else DEFAULT_TITLE
        await state.update_data(title=text, description=DEFAULT_DESCRIPTION)
    
    await show_channel_selection(message, state)

async def show_channel_selection(message: types.Message, state: FSMContext):
    channels = get_channels()
    buttons = [[InlineKeyboardButton(text=c, callback_data=f"channel_{c}")] for c in channels]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer("Выбери канал для загрузки:", reply_markup=kb)
    await state.set_state(UploadStates.choosing_channel)

@dp.callback_query(F.data.startswith("channel_"))
async def finalize_upload(callback: types.CallbackQuery, state: FSMContext):
    channel_name = callback.data.replace("channel_", "")
    data = await state.get_data()
    
    db.add_to_queue(
        file_path=data['file_path'],
        title=data['title'],
        description=data['description'],
        channel_name=channel_name
    )
    
    await callback.message.edit_text(f"✅ Видео добавлено в очередь для канала **{channel_name}**!")
    await state.clear()
    await callback.answer()

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
    )
    
    bot = Bot(token=BOT_TOKEN)
    dp.message.outer_middleware(admin_check_middleware)
    
    logging.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
