import asyncio
import logging
# Настройка логирования: уровень INFO будет выводить основные события
logging.basicConfig(level=logging.INFO)
import math
import threading
from flask import Flask

# Мини-сервер для "анти-сна"
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

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

TOKEN = "8639396565:AAH909EJPvicReJSUgJjmyhK1XtlafsvKg8"

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
        InlineKeyboardButton(text="📢 Канал", url="https://t.me/Ra1f_Shop"),
        InlineKeyboardButton(text="📝 Отзывы", url="https://t.me/Ra1f_Shopevievs1")
    )
    builder.row(InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me/i666zxc666"))
    return builder.as_markup()

# Команда /start и кнопка возврата
@dp.message(CommandStart())
@dp.message(F.text == "⬅️ Вернуться в меню")
async def start(message: types.Message, state: FSMContext):
    await state.clear() # Сброс состояний (FSM)
    await message.answer(
        "👋 Привет! Это Ra1fShop — лучший сервис по продаже Телеграм звёзд.\n\n"
        "Выбирай нужный раздел в меню ниже 👇", 
        reply_markup=get_permanent_kb() # Даем постоянную кнопку внизу
    )
    # Отправляем инлайн-кнопки
    await message.answer("Главное меню:", reply_markup=get_main_menu())

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
    await start(callback.message, state)
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
    # Если юзер нажал "Вернуться в меню" вместо ввода числа, сработает верхний хендлер
    if message.text == "⬅️ Вернуться в меню":
        return 

    if message.text.isdigit():
        stars = int(message.text)
        price = math.ceil(stars * 1.4)
        await show_checkout(message, stars, price)
        await state.clear()
    else:
        await message.answer("Введите число цифрами или нажмите кнопку возврата ниже.")

async def show_checkout(message_obj, stars, price):
    text = f"💎 **Ваш заказ:**\n\n— {stars} Stars\n— К оплате: {price}₽\n\nНажми кнопку ниже, чтобы оплатить заказ."
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"💳 ОПЛАТИТЬ {price}₽", callback_data="final_step"))
    kb.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="start_buying"))

    if isinstance(message_obj, types.Message):
        await message_obj.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    else:
        await message_obj.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "final_step")
async def yookassa_waiting(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "⏳ **Ждём подтверждения платежа от ЮKassa...**\n\n"
        "Обычно это занимает от 10 секунд до 2 минут.",
        parse_mode="Markdown"
    )
    await callback.answer()

async def main():
    # 1. Запускаем сервер анти-сна
    keep_alive()
    
    # 2. Пишем в лог и отправляем сообщение (замени ID на свой цифровой, если юзернейм не сработает)
    print("--- БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ ---")
    try:
        await bot.send_message("@i666zxc666", "🚀 Я переродился и снова в сети!")
    except Exception as e:
        print(f"Не удалось отправить сообщение админу: {e}")

    # 3. Запуск самого бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

