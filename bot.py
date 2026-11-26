import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН")
ADMIN_ID = 8553406744
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL", "https://mama-ritm.onrender.com")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ОТДАЕМ HTML ФАЙЛ ---
async def handle_index(request):
    return web.FileResponse('./index.html')

# --- ПРИНИМАЕМ ДАННЫЕ ОТ МАМЫ ---
async def handle_data(request):
    data = await request.json()
    user_name = data.get('name', 'Неизвестно')
    user_date = data.get('date', 'Неизвестно')
    
    # Просто логируем в консоль Render, что данные пришли
    logging.info(f"Новый пользователь: {user_name}, Дата: {user_date}")
    
    return web.json_response({"status": "ok"})

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
    app.router.add_post("/api/save", handle_data)
    
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()
