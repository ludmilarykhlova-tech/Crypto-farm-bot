@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    animal_key = callback.data.split("_")[1]
    user = get_user(callback.from_user.id)
    animal = MARKET.get(animal_key)
    if user["balance"] < animal["price"]:
        await callback.answer("Недостаточно монет!", show_alert=True)
        return
    earned, _ = calculate_income(user)
    user["balance"] += earned
    user["last_collect"] = time()
    user["balance"] -= animal["price"]
    user["animals"][animal_key] = user["animals"].get(animal_key, 0) + 1
    await callback.answer(f"Куплен: {animal['name']}!")
    await callback.message.edit_text(f"Успешная покупка!\nВы приобрели {animal['name']}.\nОстаток монет: {user['balance']}")

@dp.message(F.text == "📺 Реклама (+1000)")
async def watch_ad(message: types.Message):
    user = get_user(message.from_user.id)
    reward = 1000
    user["balance"] += reward
    user["ads_watched"] += 1
    await message.answer(f"🎬 Вы посмотрели рекламный ролик!\nНачислено: +{reward} монет.\nВсего просмотрено: {user['ads_watched']}")

@dp.message(F.text == "🎁 Бонус")
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
    await message.answer(f"🎉 Вы получили ежедневный бонус: +{bonus} монет!")

@dp.message(F.text == "💳 Вывод (100€)")
async def withdraw(message: types.Message):
    user = get_user(message.from_user.id)
    target = 1000000
    if user["balance"] >= target:
        await message.answer("🎉 Заявка на вывод 100€ принята!\nОна находится на проверке модератором.")
    else:
        left = target - user["balance"]
        progress = round((user["balance"] / target) * 100, 2)
        await message.answer(f"💳 Вывод средств\n\nМинимальная сумма: 1 000 000 монет (100€)\nВаш баланс: {user['balance']} монет\nОсталось собрать: {left} монет\nПрогресс: {progress}%")

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())
