import asyncio
import time
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8818091251:AAHLxobo0WNLkJ-RrjuMXuquA6xf5mrMA-g"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временная база данных в памяти
users = {}

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "balance": 0.0,
            "farm_level": 1,
            "last_bonus": 0
        }
    return users[user_id]

# Главное меню с кнопками
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⛏ Майнить"), KeyboardButton(text="💼 Профиль")],
        [KeyboardButton(text="🎁 Ежедневный бонус"), KeyboardButton(text="🚀 Улучшить ферму")]
    ],
    resize_keyboard=True
)

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    get_user(message.from_user.id)
    await message.answer(
        "👋 Добро пожаловать в My Pet Farm!\n\n"
        "Здесь ты можешь майнить крипту, прокачивать ферму и получать ежедневные бонусы.\n"
        "Выбирай действие на клавиатуре ниже:",
        reply_markup=main_keyboard
    )

@dp.message(F.text == "⛏ Майнить")
async def process_mine(message: types.Message):
    user = get_user(message.from_user.id)
    mined = 0.5 * user["farm_level"]
    user["balance"] += mined
    await message.answer(f"⛏ Вы смайнили +{mined} монет!\nТекущий баланс: {user['balance']:.2f}")

@dp.message(F.text == "💼 Профиль")
async def process_profile(message: types.Message):
    user = get_user(message.from_user.id)
    await message.answer(
        f"💼 Ваш профиль:\n\n"
        f"👤 ID: {message.from_user.id}\n"
        f"💰 Баланс: {user['balance']:.2f} монет\n"
        f"⚡ Уровень фермы: {user['farm_level']} lvl\n"
        f"📈 Доход за клик: {0.5 * user['farm_level']} монет"
    )

@dp.message(F.text == "🎁 Ежедневный бонус")
async def process_bonus(message: types.Message):
    user = get_user(message.from_user.id)
    now = time.time()
    
    # Кулдаун 24 часа (86400 сек)
    if now - user["last_bonus"] < 86400:
        left = int((86400 - (now - user["last_bonus"])) / 3600)
        await message.answer(f"⏳ Бонус уже получен! Приходите через ~{left} ч.")
        return

    user["last_bonus"] = now
    bonus_amount = 10.0
    user["balance"] += bonus_amount
    await message.answer(f"🎁 Вы получили ежедневный бонус +{bonus_amount} монет!")

@dp.message(F.text == "🚀 Улучшить ферму")
async def process_upgrade(message: types.Message):
    user = get_user(message.from_user.id)
    cost = user["farm_level"] * 20
    
    if user["balance"] < cost:
        await message.answer(f"❌ Недостаточно монет! Улучшение стоит {cost} монет.")
        return

    user["balance"] -= cost
    user["farm_level"] += 1
    await message.answer(f"🚀 Ферма улучшена до {user['farm_level']} уровня!")

# Фейковый веб-сервер для поддержания работы на Render
async def handle_health_check(request):
    return web.Response(text="OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

async def main():
    await start_web_server()
    print("Бот запущен!")
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())
