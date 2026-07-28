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

users = {}
custom_tokens = {"$PWI": {"price": 1.0, "change": "+0%"}}

IMG_MINE = "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=500&auto=format&fit=crop&q=60"
IMG_PROFILE = "https://i.ibb.co/3ynvchrm/square-gwi-bear.jpg"
IMG_UNICORN = "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=500&auto=format&fit=crop&q=60"
IMG_PETS = "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=500&auto=format&fit=crop&q=60"
IMG_SHOP = "https://images.unsplash.com/photo-1550989460-0adf9ea622e2?w=500&auto=format&fit=crop&q=60"
IMG_GAME = "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=500&auto=format&fit=crop&q=60"

PETS_CATALOG = {
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
    
    "lion": {"name": "🦁 Лев", "cost_bags": 5, "income": 300, "type": "premium"},
    "phoenix": {"name": "🔥 Феникс", "cost_bags": 15, "income": 800, "type": "premium"},
    "panther": {"name": "🐆 Пантера", "cost_bags": 30, "income": 1500, "type": "premium"},
    "griffin": {"name": "🦅 Грифон", "cost_bags": 50, "income": 3000, "type": "premium"},
    
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

class CatJumpGame(StatesGroup):
    waiting_for_bet = State()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⛏ Майнить"), KeyboardButton(text="💼 Профиль")],
        [KeyboardButton(text="🐾 Животные"), KeyboardButton(text="🦄 Высота Единорога")],
        [KeyboardButton(text="🐱 Прыжок Кота"), KeyboardButton(text="💎 Задания (Алмазы)")],
        [KeyboardButton(text="📈 Биржа токенов"), KeyboardButton(text="🎁 Бонус (10 PWI)")],
        [KeyboardButton(text="🛒 Магазин xRocket"), KeyboardButton(text="🏆 Топ игроков")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    get_user(message.from_user.id, message.from_user.first_name)
    await message.answer_photo(
        photo=IMG_PROFILE,
        caption="👋 **Добро пожаловать в PWI Farm World!**\n\nРазвивай ферму, играй в мини-игры и торгуй на бирже!",
        reply_markup=main_keyboard
    )

@dp.message(F.text == "⛏ Майнить")
async def process_mine(message: types.Message, state: FSMContext):
    await state.clear()
    user = get_user(message.from_user.id, message.from_user.first_name)
    now = time.time()
    if now - user["last_mine"] < 3:
        await message.answer("⏳ Не спамь! Майнить можно раз в 3 секунды.")
        return
    user["last_mine"] = now
    
    pet_income = sum(user["pets"][k] * PETS_CATALOG[k]["income"] for k in PETS_CATALOG)
    mined = (1.0 * user["farm_level"]) + pet_income
    user["pwi"] += mined
    
    await message.answer_photo(
        photo=IMG_MINE,
        caption=f"⛏ Смайнено: **+{mined:.1f} PWI**\n💰 Баланс: **{user['pwi']:.2f} PWI**"
    )

@dp.message(F.text == "💼 Профиль")
async def process_profile(message: types.Message, state: FSMContext):
    await state.clear()
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
    await message.answer_photo(photo=IMG_PROFILE, caption=text)

@dp.message(F.text == "🐾 Животные")
async def process_pets_menu(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Обычные (За PWI)", callback_data="cat_common")],
        [InlineKeyboardButton(text="💼 Премиум (За Мешки)", callback_data="cat_premium")],
        [InlineKeyboardButton(text="👑 Супер (За TON)", callback_data="cat_super")]
    ])
    await message.answer_photo(photo=IMG_PETS, caption="🐾 **Каталог Животных (17 видов):**\nВыберите категорию:", reply_markup=kb)

@dp.callback_query(F.data.startswith("cat_"))
async def process_category(callback: types.CallbackQuery):
    cat = callback.data.split("_")[1]
    buttons = []
    for k, v in PETS_CATALOG.items():
        if v["type"] == cat:
            if cat == "common":
                txt = f"{v['name']} — {v['cost_pwi']} PWI"
            elif cat == "premium":
                txt = f"{v['name']} — {v['cost_bags']} Мешков"
            else:
                txt = f"{v['name']} — {v['cost_ton']} TON"
            buttons.append([InlineKeyboardButton(text=txt, callback_data=f"buy_pet_{k}")])
    await callback.message.edit_caption(caption="Выберите питомца для покупки:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

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
            await callback.answer("❌ Недостаточно Мешков!", show_alert=True)
            return
        u["bags"] -= pet["cost_bags"]
    elif pet["type"] == "super":
        await callback.answer("👑 Покупка через xRocket в Магазине!", show_alert=True)
        return

    u["pets"][pet_key] += 1
    await callback.message.answer(f"🎉 Вы успешно купили **{pet['name']}**!")
    await callback.answer()

@dp.message(F.text == "🦄 Высота Единорога")
async def start_unicorn(message: types.Message, state: FSMContext):
    await state.clear()
    u = get_user(message.from_user.id, message.from_user.first_name)
    if u["pwi"] < 1:
        await message.answer("❌ У вас мало PWI монет!")
        return
    await message.answer_photo(
        photo=IMG_UNICORN,
        caption=f"🦄 **Высота Единорога**\nБаланс: **{u['pwi']:.2f} PWI**\n\nВведите сумму ставки PWI:"
    )
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
    await message.answer("✨ Задайте целевую **высоту полёта** (от 1.01 до 36):")
    await state.set_state(UnicornGame.waiting_for_height)

@dp.message(UnicornGame.waiting_for_height)
async def unicorn_height(message: types.Message, state: FSMContext):
    try:
        target_h = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("⚠️ Введите число от 1.01 до 36:")
        return
    if target_h < 1.01 or target_h > 36:
        await message.answer("⚠️ Высота должна быть от 1.01 до 36!")
        return
        
    data = await state.get_data()
    bet = data["bet"]
    u = get_user(message.from_user.id, message.from_user.first_name)
    
    actual_height = round(random.uniform(1.0, 38.0), 2)
    mult = round(target_h * 1.1, 2)
    
    if actual_height >= target_h:
        win = bet * mult
        u["pwi"] += (win - bet)
        await message.answer(f"🦄 УРА! Единорог набрал высоту **{actual_height}**!\nВы угадали цель **{target_h}** и выиграли **+{win:.2f} PWI** (x{mult})!")
    else:
        u["pwi"] -= bet
        await message.answer(f"💥 Бабах! Единорог упал на высоте **{actual_height}** (не долетел до {target_h}).\nПроигрыш: **-{bet:.2f} PWI**.")
    await state.clear()

@dp.message(F.text == "🐱 Прыжок Кота")
async def start_cat_jump(message: types.Message, state: FSMContext):
    await state.clear()
    u = get_user(message.from_user.id, message.from_user.first_name)
    await message.answer_photo(
        photo=IMG_GAME,
        caption=f"🐱 **Прыжок Кота**\nКот прыгает через преграды. Угадай, перепрыгнет ли он?\nБаланс: **{u['pwi']:.2f} PWI**\n\nВведите ставку:"
    )
    await state.set_state(CatJumpGame.waiting_for_bet)

@dp.message(CatJumpGame.waiting_for_bet)
async def cat_jump_play(message: types.Message, state: FSMContext):
    try:
        bet = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("⚠️ Введите число:")
        return
    u = get_user(message.from_user.id, message.from_user.first_name)
    if bet <= 0 or bet > u["pwi"]:
        await message.answer("⚠️ Неверная ставка!")
        return
    
    success = random.choice([True, False])
    if success:
        win = bet * 1.8
        u["pwi"] += (win - bet)
        await message.answer(f"🎉 Кот успешно перепрыгнул препятствие!\nВы выиграли **+{win:.2f} PWI**!")
    else:
        u["pwi"] -= bet
        await message.answer(f"😿 Кот зацепился за сугроб и упал...\nПроигрыш: **-{bet:.2f} PWI**.")
    await state.clear()

@dp.message(F.text == "💎 Задания (Алмазы)")
async def process_tasks(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Получить Алмаз за подписку", callback_data="do_task")],
        [InlineKeyboardButton(text="➕ Создать свое задание (0.05 TON)", callback_data="create_task")]
    ])
    await message.answer("💎 **Биржа Заданий:**\nВыполняй задания, подписывайся на каналы и получай Алмазы!", reply_markup=kb)

@dp.callback_query(F.data == "do_task")
async def do_task(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id, callback.from_user.first_name)
    u["diamonds"] += 1
    await callback.message.answer("🎉 Задание выполнено! Вам зачислен **+1 Алмаз 💎**.")
    await callback.answer()

@dp.callback_query(F.data == "create_task")
async def create_task(callback: types.CallbackQuery):
    await callback.message.answer("💡 Чтобы заказать продвижение канала (0.05 TON за 1 подписчика), оплатите через xRocket в Магазине.")
    await callback.answer()

@dp.message(F.text == "📈 Биржа токенов")
async def process_token_market(message: types.Message, state: FSMContext):
    await state.clear()
    text = "📈 **Биржа Пользовательских Токенов PWI:**\n\n"
    for symbol, data in custom_tokens.items():
        text += f"🔹 **{symbol}** — Курс: `{data['price']}` | Изменение: `{data['change']}`\n"
    text += "\n💡 Курс обновляется каждые 30 минут!"
    await message.answer(text)

@dp.message(F.text == "🎁 Бонус (10 PWI)")
async def process_bonus(message: types.Message, state: FSMContext):
    await state.clear()
    u = get_user(message.from_user.id, message.from_user.first_name)
    now = time.time()
    if now - u["last_bonus"] < 86400:
        await message.answer("⏳ Бонус уже получен! Приходи завтра.")
        return
    u["last_bonus"] = now
    u["pwi"] += 10.0
    await message.answer("🎁 Вы получили **+10.0 PWI**!")

@dp.message(F.text == "🛒 Магазин xRocket")
async def process_shop(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Купить 5 Алмазов — 0.1 TON", callback_data="buy_diag_5")],
        [InlineKeyboardButton(text="🎒 Купить 1 Мешок — 0.3 TON", callback_data="buy_bag_1")],
        [InlineKeyboardButton(text="🤖 Купить Меха-Дракона — 0.5 TON", callback_data="buy_pet_mecha_dragon")]
    ])
    await message.answer_photo(photo=IMG_SHOP, caption="🛒 **Магазин xRocket Pay**\nПокупка премиум-ресурсов и супер-питомцев за TON:", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_"))
async def xrocket_buy(callback: types.CallbackQuery):
    action = callback.data
    if "diag" in action:
        u = get_user(callback.from_user.id, callback.from_user.first_name)
        u["diamonds"] += 5
        await callback.message.answer("🎉 Успешно! Вам зачислено **+5 Алмазов 💎** (Тестовая покупка xRocket).")
    elif "bag" in action:
        u = get_user(callback.from_user.id, callback.from_user.first_name)
        u["bags"] += 1
        await callback.message.answer("🎉 Успешно! Вам зачислен **+1 Мешок с деньгами 🎒**.")
    elif "mecha_dragon" in action:
        u = get_user(callback.from_user.id, callback.from_user.first_name)
        u["pets"]["mecha_dragon"] += 1
        await callback.message.answer("🤖 Успешно! Супер-питомец **Меха-Дракон** добавлен на вашу ферму!")
    await callback.answer()

@dp.message(F.text == "🏆 Топ игроков")
async def process_top(message: types.Message, state: FSMContext):
    await state.clear()
    if not users:
        await message.answer("🏆 Топ пока пуст!")
        return
    sorted_users = sorted(users.values(), key=lambda x: x["pwi"], reverse=True)[:10]
    top_text = "🏆 **ТОП-10 ИГРОКОВ PWI:**\n\n" + "\n".join([f"{i}. {u['name']} — **{u['pwi']:.2f} PWI**" for i, u in enumerate(sorted_users, 1)])
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
