import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.config import BOT_TOKEN, ADMIN_ID, DEFAULT_TITLE, DEFAULT_DESCRIPTION
from core.db_manager import DBManager
from core.video_handler import VideoProcessor

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = DBManager()

class UploadStates(StatesGroup):
    waiting_for_metadata = State()
    choosing_channel = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Отправь мне ссылку на TikTok или видеофайл, и я подготовлю его для YouTube Shorts.")

@dp.message(F.text.startswith("http"))
@dp.message(F.video)
async def handle_video_input(message: types.Message, state: FSMContext):
    msg = await message.answer("🎬 Начинаю обработку видео...")
    
    try:
        if message.text:
            raw_path = await VideoProcessor.download_tiktok(message.text, str(message.message_id))
        else:
            video = message.video
            raw_path = f"data/videos/raw_{message.message_id}.mp4"
            await bot.download(video, destination=raw_path)

        final_path = await VideoProcessor.apply_overlay(raw_path, f"final_{message.message_id}")
        
        await state.update_data(file_path=final_path)
        
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Использовать стандартные", callback_data="use_default")
        ]])
        
        await msg.edit_text("✅ Видео обработано. Введи название и описание через '|' (например: Заголовок | Описание) или нажми кнопку ниже:", reply_markup=kb)
        await state.set_state(UploadStates.waiting_for_metadata)
        
    except Exception as e:
        logging.error(f"Error: {e}")
        await msg.edit_text(f"❌ Произошла ошибка: {e}")

@dp.callback_query(F.data == "use_default")
async def use_default_metadata(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(title=DEFAULT_TITLE, description=DEFAULT_DESCRIPTION)
    await show_channel_selection(callback.message, state)
    await callback.answer()

@dp.message(UploadStates.waiting_for_metadata)
async def process_metadata(message: types.Message, state: FSMContext):
    if "|" in message.text:
        title, desc = message.text.split("|", 1)
        await state.update_data(title=title.strip(), description=desc.strip())
    else:
        await state.update_data(title=message.text.strip(), description=DEFAULT_DESCRIPTION)
    
    await show_channel_selection(message, state)

async def show_channel_selection(message: types.Message, state: FSMContext):
    # Тут можно загружать каналы из конфига, для примера сделаем 3
    channels = ["Channel_1", "Channel_2", "Channel_3"]
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
    
    await callback.message.edit_text(f"✅ Видео добавлено в очередь для канала **{channel_name}**! Оно будет загружено при следующей проверке планировщика.")
    await state.clear()
    await callback.answer()

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
