import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F

TOKEN = "8818091251:AAHLxobo0WNLkJ-RjjuMXuquA6xf5mrMA-g"

bot = Bot(token=TOKEN)
dp = Dispatcher()

users = {}

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "balance": 0,
            "last_bonus": 0
        }
    return users[user_id]

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    get_user(message.from_user.id)
    await message.answer("Привет! Бот успешно запущен!")

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
    print("Запускаем веб-сервер и бота...")
    await start_web_server()
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
