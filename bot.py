import os
import logging
import aiosqlite
from aiohttp import web
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН")
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL", "https://mama-ritm.onrender.com")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
DB_NAME = "mama_ritm.db"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- БАЗА ДАННЫХ ---
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY,
                baby_name TEXT,
                text TEXT,
                date TEXT
            )
        """)
        await db.commit()

# --- ОТДАЕМ HTML ---
async def handle_index(request):
    return web.FileResponse('./index.html')

# --- API ДЛЯ АНКЕТЫ ---
async def handle_save_profile(request):
    data = await request.json()
    logging.info(f"Новый профиль: {data.get('name')}, Дата: {data.get('date')}")
    return web.json_response({"status": "ok"})

# --- API ДЛЯ ДОСТИЖЕНИЙ ---
async def handle_add_achievement(request):
    data = await request.json()
    baby_name = data.get('baby_name')
    text = data.get('text')
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO achievements (baby_name, text, date) VALUES (?, ?, ?)", (baby_name, text, date_str))
        await db.commit()
    return web.json_response({"status": "ok"})

async def handle_get_achievements(request):
    baby_name = request.query.get('baby_name')
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT text, date FROM achievements WHERE baby_name = ? ORDER BY id DESC", (baby_name,)) as cursor:
            rows = await cursor.fetchall()
    
    result = [{"text": row[0], "date": row[1]} for row in rows]
    return web.json_response(result)

# --- КОМАНДА START ---
@dp.message(Command("start"))
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="👶 Открыть Мамин Ритм", 
        web_app=WebAppInfo(url=f"{WEBHOOK_HOST}/index.html")
    ))
    await message.answer(
        "Привет! 👋 Добро пожаловать в «Мамин Ритм».\n"
        "Нажмите кнопку ниже, чтобы начать знакомство.",
        reply_markup=builder.as_markup()
    )

# --- ЗАПУСК ---
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)

def main():
    app = web.Application()
    app.router.add_get("/index.html", handle_index)
    
    # Подключаем наши API
    app.router.add_post("/api/save", handle_save_profile)
    app.router.add_post("/api/add_achievement", handle_add_achievement)
    app.router.add_get("/api/get_achievements", handle_get_achievements)
    
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()
