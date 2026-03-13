import asyncio
import logging
# Настройка логирования: уровень INFO будет выводить основные события
logging.basicConfig(level=logging.INFO)
import math
import threading
import os
from flask import Flask

# Мини-сервер для "анти-сна"
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    # Render передает порт в переменной окружения PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Запуск сервера в отдельном потоке
def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

TOKEN = "8639396565:AAGTxYhR08VfMzJrbcVyyODeMcAE6uBvXsg"
ADMIN_ID = 1285110076
bot = Bot(token=TOKEN)
dp = Dispatcher()

class OrderStates(StatesGroup):
    waiting_for_amount = State()

# --- ПОСТОЯННАЯ КЛАВИАТУРА ВНИЗУ ---
def get_permanent_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="⬅️ Вернуться в меню"))
    return builder.as_markup(resize_keyboard=True)

# --- ГЛАВНОЕ ИНЛАЙН МЕНЮ ---
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⭐ КУПИТЬ ЗВЁЗДЫ", callback_data="start_buying"))
    builder.row(
        InlineKeyboardButton(text="📢 Основной канал", url="https://t.me/Ra1f_Shop"),
        InlineKeyboardButton(text="📝 Отзывы", url="https://t.me/Ra1f_Shopevievs1")
    )
    builder.row(InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me/i666zxc666"))
    return builder.as_markup()

# Команда /start и кнопка возврата
# Только для самой первой команды /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    with open("users.txt", "a+") as f:
        f.seek(0)
        lines = f.read().splitlines()
        if user_id not in lines:
            f.write(user_id + "\n")
    await state.clear()
    await message.answer(
        "👋 Привет! Это Ra1fShop — лучший сервис по продаже Телеграм звёзд.\n\n"
        "Выбирай нужный раздел в меню ниже 👇", 
        reply_markup=get_permanent_kb()
    )
    await send_main_menu(message) # Кидаем меню сразу после приветствия

# Для кнопки "Вернуться в меню" и инлайн-кнопки "Назад"
@dp.message(F.text == "⬅️ Вернуться в меню")
@dp.callback_query(F.data == "back_to_start")
async def back_to_menu_handler(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    # Определяем, откуда пришел вызов (сообщение или кнопка)
    if isinstance(event, types.Message):
        await send_main_menu(event)
    else:
        # Если это инлайн-кнопка, лучше редактировать старое сообщение, а не слать новое
        await event.message.edit_text("Главное меню:", reply_markup=get_main_menu())
        await event.answer()

# --- МЕНЮ ПАКЕТОВ ---
@dp.callback_query(F.data == "start_buying")
async def buy_stars_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    
    # 50 звезд — широкая
    builder.row(InlineKeyboardButton(text="50 ⭐ — 70₽", callback_data="pay_50_70"))
    
    # 100-1000 — парами
    stars_list = []
    for stars in range(100, 1050, 50):
        price = math.ceil(stars * 1.4)
        stars_list.append(InlineKeyboardButton(text=f"{stars} ⭐ — {price}₽", callback_data=f"pay_{stars}_{price}"))
    
    builder.add(*stars_list)
    builder.adjust(1, 2) 
    
    # Своё количество и Назад — широкие
    builder.row(InlineKeyboardButton(text="💎 Своё количество", callback_data="pay_custom"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start"))
    
    await callback.message.edit_text("Выбери пакет звёзд:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "back_to_start")
async def back_to_start(callback: types.CallbackQuery, state: FSMContext):
    # При нажатии инлайн-кнопки "Назад" просто вызываем функцию старта
    await back_to_menu_handler(callback.message, state)
    await callback.answer()

@dp.callback_query(F.data.startswith('pay_'))
async def process_payment(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "pay_custom":
        await callback.message.answer("Введите количество звёзд:")
        await state.set_state(OrderStates.waiting_for_amount)
    else:
        parts = callback.data.split('_')
        await show_checkout(callback.message, parts[1], parts[2])
    await callback.answer()

@dp.message(OrderStates.waiting_for_amount)
async def custom_amount(message: types.Message, state: FSMContext):
    # Если юзер передумал и нажал кнопку возврата
    if message.text == "⬅️ Вернуться в меню":
        await state.clear()
        return 

    # Проверяем, что введено именно число
    if message.text.isdigit():
        stars = int(message.text)
        
        # --- ВОТ ТУТ ДОБАВЛЯЕМ ПРОВЕРКУ ДИАПАЗОНА ---
        if stars < 50:
            await message.answer("❌ Минимальное количество для заказа — 50 ⭐")
        elif stars > 5000:
            await message.answer("❌ Максимальное количество для разового заказа — 5000 ⭐")
        else:
            # Если всё ок, считаем цену и показываем чек
            price = math.ceil(stars * 1.4)
            await show_checkout(message, stars, price)
            await state.clear() # Сбрасываем состояние только при успешном вводе
    else:
        await message.answer("⚠️ Введите количество звёзд цифрами (например, 150) или нажмите кнопку возврата.")

async def show_checkout(message_obj, stars, price):
    text = f"💎 **Ваш заказ:**\n\n— {stars} звёзд\n— К оплате: {price}₽\n\nНажми кнопку ниже, чтобы оплатить заказ."
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"💳 ОПЛАТИТЬ {price}₽", callback_data=f"final_{price}"))
    kb.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="start_buying"))

    if isinstance(message_obj, types.Message):
        await message_obj.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    else:
        await message_obj.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")

# --- БЛОК ОПЛАТЫ И УВЕДОМЛЕНИЯ АДМИНА ---
@dp.callback_query(F.data.startswith("final_"))
async def process_final_step(callback: types.CallbackQuery):
    # 1. Извлекаем цену из callback_data (например, из "final_140")
    # Важно: убедись, что кнопка создается как callback_data=f"final_{price}"
    data_parts = callback.data.split('_')
    price = data_parts[1] if len(data_parts) > 1 else "неизвестно"
    
    user_name = callback.from_user.username if callback.from_user.username else "скрыт"
    user_id = callback.from_user.id

    # 2. Уведомление тебе
    admin_text = (
        f"🔔 **НОВЫЙ ЗАКАЗ!**\n\n"
        f"👤 **Клиент:** @{user_name}\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"💰 **Сумма:** {price}₽"
    )
    
    try:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка уведомления админа: {e}")

    # 3. Ответ юзеру (проверь, чтобы price была внутри фигурных скобок {})
    await callback.message.edit_text(
        f"✅ **Заказ на сумму {price}₽ сформирован!**\n\n"
        "Для оплаты напишите администратору:\n"
        "👉 @i666zxc666\n\n"
        "Пришлите скриншот этого сообщения.",
        parse_mode="Markdown"
    )
    await callback.answer()

async def send_main_menu(message_obj: types.Message):
    # Эта функция просто кидает меню
    await message_obj.answer("Главное меню:", reply_markup=get_main_menu())

@dp.message(F.text.startswith("/send"))
async def start_broadcast(message: types.Message):
    # Проверка, что пишет именно админ (твой ID 1285110076)
    if message.from_user.id != ADMIN_ID:
        return 

    # Берем текст после команды /send
    broadcast_text = message.text[6:].strip()
    
    if not broadcast_text:
        return await message.answer("⚠️ Ошибка! Напиши текст после команды.\nПример: `/send Привет всем!`")

    if not os.path.exists("users.txt"):
        return await message.answer("❌ База пользователей пуста.")

    with open("users.txt", "r") as f:
        users = f.read().splitlines()

    await message.answer(f"📢 Начинаю рассылку для {len(users)} пользователей...")
    
    success_count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, broadcast_text, parse_mode="Markdown")
            success_count += 1
            await asyncio.sleep(0.05) # Пауза, чтобы Телеграм не забанил за спам
        except Exception:
            continue # Пропускаем тех, кто удалил бота

    await message.answer(f"✅ Рассылка завершена!\nДоставлено: {success_count} пользователям.")

async def main():
    # 1. Запускаем сервер анти-сна
    keep_alive()
    
    await bot.delete_webhook(drop_pending_updates=True)

    # 2. Пишем в лог и отправляем сообщение (замени ID на свой цифровой, если юзернейм не сработает)
    print("--- БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ ---")
    try:
        await bot.send_message(ADMIN_ID, "🚀 Я переродился и снова в сети!")
    except Exception as e:
        print(f"Не удалось отправить сообщение админу: {e}")

    # 3. Запуск самого бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

