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

TOKEN = "8998631035:AAGj3IiYS0cqqNeKB4BTIO3DWDDpr-zXEuY"
XROCKET_API_TOKEN = "9a9e823f2bb0d99a7b3c8c4e6"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# База данных пользователей в памяти
users = {}
# Пользовательские токены {symbol: {"owner": id, "price": pwi, "change": %}}
custom_tokens = {"$PWI": {"owner": "System", "price": 1.0, "change": "+0%"}}
# Задания на подписку
tasks = []

# Реестр 17 животных
PETS_CATALOG = {
    # Обычные (10)
    "hamster": {"name": "🐹 Хомяк", "cost_pwi": 50, "income": 1, "type": "common"},
    "ferret": {"name": "🦡 Хорёк", "cost_pwi": 100, "income": 2, "type": "common"},
    "rabbit": {"name": "🐰 Кролик", "cost_pwi": 200, "income": 4, "type": "common"},
    "cat": {"name": "🐱 Кот", "cost_pwi": 400, "income": 8, "type": "common"},
    "dog": {"name": "🐶 Собака", "cost_pwi": 800, "income": 15, "type": "common"},
    "parrot": {"name": "🦜 Попугай", "cost_pwi": 1500, "income": 25, "type": "common"},
    "raccoon": {"name": "🦝 Енот", "cost_pwi": 3000, "income": 40, "type": "common"},
    "hedgehog": {"name": "🦔 Еж", "cost_pwi": 5000, "income": 60, "type": "common"},
    "capybara": {"name": "🦫 Капибара", "cost_pwi": 8000, "income": 90, "type": "common"},
    "pig": {"name": "🐷 Свинка", "cost_pwi": 12000, "income": 130, "type": "common"},
    
    # Премиум (4) - за Мешки/Алмазы
    "lion": {"name": "🦁 Лев", "cost_bags": 5, "income": 300, "type": "premium"},
    "phoenix": {"name": "🔥 Феникс", "cost_bags": 15, "income": 800, "type": "premium"},
    "panther": {"name": "🐆 Пантера", "cost_bags": 30, "income": 1500, "type": "premium"},
    "griffin": {"name": "🦅 Грифон", "cost_bags": 50, "income": 3000, "type": "premium"},
    
    # Супер (3) - за TON
    "mecha_dragon": {"name": "🤖 Меха-Дракон", "cost_ton": 0.5, "income": 7000, "type": "super"},
    "space_whale": {"name": "🐋 Космический Кит", "cost_ton": 1.5, "income": 20000, "type": "super"},
    "abyss_lord": {"name": "👑 Владыка Бездны", "cost_ton": 3.0, "income": 50000, "type": "super"},
}

def get_user(user_id, name="Игрок"):
    if user_id not in users:
        users[user_id] = {
            "name": name,
            "pwi": 100.0,
            "diamonds": 0,
            "bags": 0,
            "farm_level": 1,
            "last_bonus": 0,
            "last_mine": 0,
            "pets": {k: 0 for k in PETS_CATALOG.keys()}
        }
    else:
        users[user_id]["name"] = name
    return users[user_id]

class UnicornGame(StatesGroup):
    waiting_for_bet = State()
    waiting_for_height = State()

class CreateToken(StatesGroup):
    waiting_for_name = State()

class CreateTask(StatesGroup):
    waiting_for_link = State()
    waiting_for_count = State()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⛏ Майнить"), KeyboardButton(text="💼 Профиль")],
        [KeyboardButton(text="🐾 Животные"), KeyboardButton(text="🦄 Высота Единорога")],
        [KeyboardButton(text="💎 Задания (Алмазы)"), KeyboardButton(text="📈 Биржа Токенов")],
        [KeyboardButton(text="🎁 Бонус (10 PWI)"), KeyboardButton(text="🛒 P2P Маркет")],
        [KeyboardButton(text="🏆 Топ")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    get_user(message.from_user.id, message.from_user.first_name)
    await message.answer("👋 **Добро пожаловать в PWI Farm World!**", reply_markup=main_keyboard)

# 1. МАЙНИНГ С ТАЙМАУТОМ 3 СЕК
@dp.message(F.text == "⛏ Майнить")
async def process_mine(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.first_name)
    now = time.time()
    if now - user["last_mine"] < 3:
        await message.answer("⏳ Не спамь! Майнить можно раз в 3 секунды.")
        return
    user["last_mine"] = now
    
    pet_income = sum(user["pets"][k] * PETS_CATALOG[k]["income"] for k in PETS_CATALOG)
    mined = (1.0 * user["farm_level"]) + pet_income
    user["pwi"] += mined
    
    await message.answer(f"⛏ Смайнено: **+{mined:.1f} PWI**\n💰 Баланс: **{user['pwi']:.2f} PWI**")

# 2. ПРОФИЛЬ
@dp.message(F.text == "💼 Профиль")
async def process_profile(message: types.Message):
    u = get_user(message.from_user.id, message.from_user.first_name)
    total_pets = sum(u["pets"].values())
    text = (
        f"💼 **Профиль {u['name']}:**\n\n"
        f"🪙 Баланс PWI: **{u['pwi']:.2f}**\n"
        f"💎 Алмазы: **{u['diamonds']}**\n"
        f"🎒 Мешки с деньгами: **{u['bags']}**\n"
        f"⚡ Уровень фермы: **{u['farm_level']} lvl**\n"
        f"🐾 Всего питомцев: **{total_pets} шт.**"
    )
    await message.answer(text)

# 3. ЕЖЕДНЕВНЫЙ БОНУС (10 PWI)
@dp.message(F.text == "🎁 Бонус (10 PWI)")
async def process_bonus(message: types.Message):
    u = get_user(message.from_user.id, message.from_user.first_name)
    now = time.time()
    if now - u["last_bonus"] < 86400:
        await message.answer("⏳ Ежедневный бонус уже получен! Приходи завтра.")
        return
    u["last_bonus"] = now
    u["pwi"] += 10.0
    await message.answer("🎁 Вы получили **+10.0 PWI**!")

# 4. РАЗДЕЛ "ЖИВОТНЫЕ" (17 ВИДОВ)
@dp.message(F.text == "🐾 Животные")
async def process_pets_menu(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Обычные (За PWI)", callback_data="cat_common")],
        [InlineKeyboardButton(text="💼 Премиум (За Мешки)", callback_data="cat_premium")],
        [InlineKeyboardButton(text="👑 Супер (За TON)", callback_data="cat_super")]
    ])
    await message.answer("🐾 **Каталог Животных (17 видов):**\nВыберите категорию:", reply_markup=kb)

@dp.callback_query(F.data.startswith("cat_"))
async def process_category(callback: types.CallbackQuery):
    cat = callback.data.split("_")[1]
    buttons = []
    for k, v in PETS_CATALOG.items():
        if v["type"] == cat:
            if cat == "common":
                txt = f"{v['name']} — {v['cost_pwi']} PWI (+{v['income']}/клик)"
            elif cat == "premium":
                txt = f"{v['name']} — {v['cost_bags']} Мешков (+{v['income']}/клик)"
            else:
                txt = f"{v['name']} — {v['cost_ton']} TON (+{v['income']}/клик)"
            buttons.append([InlineKeyboardButton(text=txt, callback_data=f"buy_pet_{k}")])
    
    await callback.message.edit_text("Выберите питомца для покупки:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("buy_pet_"))
async def buy_pet(callback: types.CallbackQuery):
    pet_key = callback.data.replace("buy_pet_", "")
    pet = PETS_CATALOG[pet_key]
    u = get_user(callback.from_user.id, callback.from_user.first_name)
    
    if pet["type"] == "common":
        if u["pwi"] < pet["cost_pwi"]:
            await callback.answer("❌ Недостаточно PWI!", show_alert=True)
            return
        u["pwi"] -= pet["cost_pwi"]
    elif pet["type"] == "premium":
        if u["bags"] < pet["cost_bags"]:
            await callback.answer("❌ Недостаточно Мешков с деньгами!", show_alert=True)
            return
        u["bags"] -= pet["cost_bags"]
    elif pet["type"] == "super":
        await callback.answer("👑 Супер-питомцы покупаются через счет xRocket!", show_alert=True)
        return

    u["pets"][pet_key] += 1
    await callback.message.answer(f"🎉 Вы купили **{pet['name']}**!")
    await callback.answer()

# 5. ВЫСОТА ЕДИНОРОГА
@dp.message(F.text == "🦄 Высота Единорога")
async def start_unicorn(message: types.Message, state: FSMContext):
    u = get_user(message.from_user.id, message.from_user.first_name)
    if u["pwi"] < 1:
        await message.answer("❌ У вас слишком мало PWI монет!")
        return
    await message.answer(f"🦄 **Высота Единорога**\nБаланс: **{u['pwi']:.2f} PWI**\n\nВведите сумму ставки PWI:")
    await state.set_state(UnicornGame.waiting_for_bet)

@dp.message(UnicornGame.waiting_for_bet)
async def unicorn_bet(message: types.Message, state: FSMContext):
    try:
        bet = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("⚠️ Введите число:")
        return
    u = get_user(message.from_user.id, message.from_user.first_name)
    if bet <= 0 or bet > u["pwi"]:
        await message.answer("⚠️ Неверная ставка!")
        return
    await state.update_data(bet=bet)
    await message.answer("✨ Задайте целевую **высоту полёта** (от 2 до 36):")
    await state.set_state(UnicornGame.waiting_for_height)

@dp.message(UnicornGame.waiting_for_height)
async def unicorn_height(message: types.Message, state: FSMContext):
    try:
        target_h = int(message.text)
    except ValueError:
        await message.answer("⚠️ Введите целое число от 2 до 36:")
        return
    if target_h < 2 or target_h > 36:
        await message.answer("⚠️ Высота должна быть в пределах от 2 до 36!")
        return
        
    data = await state.get_data()
    bet = data["bet"]
    u = get_user(message.from_user.id, message.from_user.first_name)
    
    actual_height = random.randint(1, 40)
    mult = round(target_h * 1.2, 2)
    
    if actual_height >= target_h:
        win = bet * mult
        u["pwi"] += (win - bet)
        await message.answer(f"🦄 УРА! Единорог набрал высоту **{actual_height}**!\nВы заказывали **{target_h}** и выиграли **+{win:.2f} PWI** (x{mult})!")
    else:
        u["pwi"] -= bet
        await message.answer(f"💥 Увы! Единорог упал на высоте **{actual_height}** (не долетел до {target_h}).\nПроигрыш: **-{bet:.2f} PWI**.")
    await state.clear()

# 6. БИРЖА ЗАДАНИЙ (ПОДПИСКИ ЗА TON И АЛМАЗЫ)
@dp.message(F.text == "💎 Задания (Алмазы)")
async def process_tasks(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Заказать подписчиков (0.05 TON/шт)", callback_data="create_sub_task")],
        [InlineKeyboardButton(text="📋 Список заданий (+1 Алмаз)", callback_data="list_sub_tasks")]
    ])
    await message.answer("💎 **Биржа Заданий:**\nВыполняйте задания и получайте Алмазы!", reply_markup=kb)

@dp.callback_query(F.data == "create_sub_task")
async def start_create_task(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте ссылку на ваш Telegram канал (например https://t.me/your_channel):")
    await state.set_state(CreateTask.waiting_for_link)
    await callback.answer()

@dp.message(CreateTask.waiting_for_link)
async def task_link(message: types.Message, state: FSMContext):
    await state.update_data(link=message.text)
    await message.answer("Сколько подписчиков вам нужно? (0.05 TON за 1 подписчика):")
    await state.set_state(CreateTask.waiting_for_count)

@dp.message(CreateTask.waiting_for_count)
async def task_count(message: types.Message, state: FSMContext):
    try:
        count = int(message.text)
    except ValueError:
        await message.answer("⚠️ Введите число:")
        return
    data = await state.get_data()
    ton_cost = count * 0.05
    await message.answer(f"🧾 Заказ: {count} подписок на {data['link']}\nК оплате: **{ton_cost:.2f} TON** (Оплатите через xRocket).")
    await state.clear()

# WEB SERVER & MAIN
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
