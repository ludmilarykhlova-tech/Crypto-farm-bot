import asyncio
import time
import random
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8998631035:AAGj3IiYS0cqqNeKB4BTIO3DWDDpr-zXEuYXROCKET_API_TOKEN = "9a9e823f2bb0d99a7b3c8c4e6"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
users = {}

IMG_MINE = "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=500&auto=format&fit=crop&q=60"
IMG_PROFILE = "https://i.ibb.co/3ynvchrm/square-gwi-bear.jpg"

def get_user(user_id, name="Игрок"):
    if user_id not in users:
        users[user_id] = {"name": name, "balance": 10.0, "farm_level": 1, "last_bonus": 0}
    else:
        users[user_id]["name"] = name
    return users[user_id]

# Состояния для ввода собственной ставки
class UnicornGame(StatesGroup):
    waiting_for_bet = State()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⛏ Майнить"), KeyboardButton(text="💼 Профиль")],
        [KeyboardButton(text="🦄 Полет Единорога"), KeyboardButton(text="🎁 Ежедневный бонус")],
        [KeyboardButton(text="🚀 Улучшить ферму"), KeyboardButton(text="🛒 Магазин (Купить монеты)")],
        [KeyboardButton(text="🏆 Топ игроков")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    get_user(message.from_user.id, message.from_user.first_name)
    await message.answer(
        "👋 **Добро пожаловать в My Pet Farm!**\n\nМайните монеты, запускайте единорога в полёт и развивайте питомца!", 
        reply_markup=main_keyboard
    )

@dp.message(F.text == "⛏ Майнить")
@dp.message(Command("mine"))
async def process_mine(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.first_name)
    mined = 0.5 * user["farm_level"]
    user["balance"] += mined
    await message.answer_photo(
        photo=IMG_MINE,
        caption=f"⛏ **{user['name']}**, твой питомец поработал!\n\nСмайнено: **+{mined}** монет!\nБаланс: **{user['balance']:.2f}**"
    )

@dp.message(F.text == "💼 Профиль")
@dp.message(Command("balance"))
async def process_profile(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.first_name)
    await message.answer_photo(
        photo=IMG_PROFILE,
        caption=f"💼 **Профиль {user['name']}:**\n\n💰 Баланс: **{user['balance']:.2f}** монет\n⚡ Уровень фермы: **{user['farm_level']} lvl**"
    )

# ================= ИГРА: ПОЛЕТ ЕДИНОРОГА =================

@dp.message(F.text == "🦄 Полет Единорога")
async def start_unicorn_game(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id, message.from_user.first_name)
    if user["balance"] <= 0:
        await message.answer("❌ У вас 0 монет! Смайните немного монет, чтобы играть.")
        return
        
    await message.answer(
        f"🦄 **Полет Единорога!**\n\n💰 Ваш баланс: **{user['balance']:.2f}** монет.\n\nНапишите в чат **сумму ставки**, которую хотите поставить:"
    )
    await state.set_state(UnicornGame.waiting_for_bet)

@dp.message(UnicornGame.waiting_for_bet)
async def process_bet_input(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id, message.from_user.first_name)
    
    try:
        bet = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите корректное число (например: 2 или 5.5):")
        return

    if bet <= 0:
        await message.answer("⚠️ Ставка должна быть больше 0! Введите сумму заново:")
        return

    if bet > user["balance"]:
        await message.answer(f"❌ У вас нет столько монет! У вас на балансе: **{user['balance']:.2f}**. Введите сумму меньше:")
        return

    # Сохраняем ставку в память
    await state.update_data(bet=bet)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌈 До Радуги (x1.5)", callback_data="uni_rainbow")],
        [InlineKeyboardButton(text="☁️ До Облаков (x2.0)", callback_data="uni_clouds")],
        [InlineKeyboardButton(text="⭐️ До Космоса (x5.0)", callback_data="uni_space")]
    ])
    
    await message.answer(
        f"Ставка принята: **{bet}** монет!\n\n✨ **Угадай, до куда долетит единорог?**", 
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("uni_"))
async def process_unicorn_flight(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    bet = user_data.get("bet")

    if not bet:
        await callback.answer("⚠️ Время ожидания истекло. Нажмите кнопку '🦄 Полет Единорога' заново.", show_alert=True)
        return

    user = get_user(callback.from_user.id, callback.from_user.first_name)
    
    if user["balance"] < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        await state.clear()
        return

    target = callback.data.split("_")[1]
    
    # Шансы: rainbow (70%), clouds (50%), space (20%)
    chances = {"rainbow": 70, "clouds": 50, "space": 20}
    multipliers = {"rainbow": 1.5, "clouds": 2.0, "space": 5.0}
    names = {"rainbow": "🌈 Радуги", "clouds": "☁️ Облаков", "space": "⭐️ Космоса"}

    roll = random.randint(1, 100)
    is_win = roll <= chances[target]

    if is_win:
        win_amount = bet * multipliers[target]
        profit = win_amount - bet
        user["balance"] += profit
        await callback.message.edit_text(
            f"🦄✨ **Единорог успешно долетел до {names[target]}!**\n\n🎉 Вы угадали и выиграли **+{win_amount:.2f}** монет!\n💰 Ваш баланс: **{user['balance']:.2f}**"
        )
    else:
        user["balance"] -= bet
        await callback.message.edit_text(
            f"🦄💨 **Единорог устал и приземлился раньше...**\n\n💥 Вы не долетели до {names[target]} и потеряли **-{bet:.2f}** монет.\n💰 Ваш баланс: **{user['balance']:.2f}**"
        )

    await state.clear()
    await callback.answer()

# ================= МАГАЗИН И ПРОЧЕЕ =================

@dp.message(F.text == "🛒 Магазин (Купить монеты)")
@dp.message(Command("shop"))
async def process_shop(message: types.Message):
    shop_inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 100 монет — 1 TON", callback_data="buy_100")],
        [InlineKeyboardButton(text="🚀 500 монет — 4.5 TON", callback_data="buy_500")],
        [InlineKeyboardButton(text="👑 1500 монет — 10 TON", callback_data="buy_1500")]
    ])
    await message.answer("🚀 **Магазин xRocket Pay**", reply_markup=shop_inline_kb)

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy_callback(callback: types.CallbackQuery):
    amount_str = callback.data.split("_")[1]
    prices = {"100": 1.0, "500": 4.5, "1500": 10.0}
    price = prices.get(amount_str, 1.0)
    
    async with aiohttp.ClientSession() as session:
        headers = {"Rocket-Pay-Key": XROCKET_API_TOKEN, "Content-Type": "application/json"}
        payload = {"amount": price, "currency": "TON", "description": f"Покупка {amount_str} монет", "customData": f"{callback.from_user.id}_{amount_str}"}
        try:
            async with session.post("https://pay.tigo.la/api/tg-invoices", json=payload, headers=headers) as resp:
                data = await resp.json()
                if data.get("success") and "data" in data:
                    pay_url = data["data"]["link"]
                    invoice_id = data["data"]["id"]
                    pay_kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🚀 Оплатить", url=pay_url)],
                        [InlineKeyboardButton(text="✅ Проверить", callback_data=f"check_{invoice_id}_{amount_str}")]
                    ])
                    await callback.message.answer(f"🧾 **Счет на {amount_str} монет ({price} TON):**", reply_markup=pay_kb)
                else:
                    await callback.message.answer("⚠️ Ошибка счета в xRocket.")
        except Exception:
            await callback.message.answer("⚠️ Ошибка сети.")
    await callback.answer()

@dp.callback_query(F.data.startswith("check_"))
async def check_payment(callback: types.CallbackQuery):
    _, invoice_id, amount_str = callback.data.split("_")
    async with aiohttp.ClientSession() as session:
        headers = {"Rocket-Pay-Key": XROCKET_API_TOKEN}
        try:
            async with session.get(f"https://pay.tigo.la/api/tg-invoices/{invoice_id}", headers=headers) as resp:
                data = await resp.json()
                if data.get("success") and "data" in data and data["data"]["status"] == "PAID":
                    user = get_user(callback.from_user.id, callback.from_user.first_name)
                    user["balance"] += float(amount_str)
                    await callback.message.edit_text(f"🎉 **Оплачено!** Зачислено **+{amount_str}** монет!")
                else:
                    await callback.answer("⏳ Еще не оплачено!", show_alert=True)
        except Exception:
            await callback.answer("⚠️ Ошибка проверки.", show_alert=True)

@dp.message(F.text == "🎁 Ежедневный бонус")
@dp.message(Command("bonus"))
async def process_bonus(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.first_name)
    now = time.time()
    if now - user["last_bonus"] < 86400:
        await message.answer("⏳ Бонус уже получен! Приходите завтра.")
        return
    user["last_bonus"] = now
    user["balance"] += 10.0
    await message.answer("🎁 Вы получили **+10** монет!")

@dp.message(F.text == "🚀 Улучшить ферму")
@dp.message(Command("upgrade"))
async def process_upgrade(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.first_name)
    cost = user["farm_level"] * 20
    if user["balance"] < cost:
        await message.answer(f"❌ Нужно **{cost}** монет!")
        return
    user["balance"] -= cost
    user["farm_level"] += 1
    await message.answer(f"🚀 Уровень повышен до **{user['farm_level']}**!")

@dp.message(F.text == "🏆 Топ игроков")
@dp.message(Command("top"))
async def process_top(message: types.Message):
    if not users:
        await message.answer("🏆 Топ пуст!")
        return
    sorted_users = sorted(users.values(), key=lambda x: x["balance"], reverse=True)[:10]
    top_text = "🏆 **ТОП ИГРОКОВ:**\n\n" + "\n".join([f"{i}. {u['name']} — {u['balance']:.2f}" for i, u in enumerate(sorted_users, 1)])
    await message.answer(top_text)

async def handle_health_check(request):
    return web.Response(text="OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", 10000).start()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
