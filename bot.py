import asyncio
from time import time
from aiogram import Bot, Dispatcher, types, F

# Вставь сюда свой токен от BotFather (в кавычках)
TOKEN = "8818091251:AAHLxobo0WNLkJ-RrjuMXuquA6xf5mrMA-g"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Простейшее хранилище пользователей в памяти
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
    await message.answer("Привет! Добро пожаловать в Crypto Farm Bot!\nИспользуй команды или меню.")

@dp.message(F.text == "Бонус")
async def daily_bonus(message: types.Message):
    user = get_user(message.from_user.id)
    now = time()
    if now - user["last_bonus"] < 86400:
        remaining = int((86400 - (now - user["last_bonus"])) / 3600)
        await message.answer(f"Следующий бонус можно получить через {remaining} ч.")
        return
    
    bonus = 5000
    user["balance"] += bonus
    user["last_bonus"] = now
    await message.answer(f"Вы получили ежедневный бонус: +{bonus} монет!")

@dp.message(F.text == "Вывод (100€)")
async def withdraw(message: types.Message):
    user = get_user(message.from_user.id)
    target = 1000000
    if user["balance"] >= target:
        await message.answer("Заявка на вывод 100€ принята!\nОна находится на проверке модератором.")
    else:
        left = target - user["balance"]
        progress = round((user["balance"] / target) * 100, 2)
        await message.answer(f"Вывод средств\n\nМинимальная сумма: 1 000 000 монет (100€)\nВаш баланс: {user['balance']} монет\nПрогресс: {progress}%")

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

    if __name__ == "__main__":
        asyncio.run(main())
