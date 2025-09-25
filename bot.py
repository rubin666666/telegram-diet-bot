from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram import types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime
import asyncio
import logging
import json
import os
import random

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Токен бота (отримайте від @BotFather)
BOT_TOKEN = "8458486366:AAH4DnunseoCOdyyRS7fueLKeW4ELSZc3QA"

# Ініціалізація бота та диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Стани для FSM
class UserProfile(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_weight = State()
    waiting_for_height = State()
    waiting_for_activity = State()
    waiting_for_goal = State()

class FoodCalories(StatesGroup):
    waiting_for_food = State()
    waiting_for_weight = State()

class WeightTracker(StatesGroup):
    waiting_for_weight = State()

class FoodDiary(StatesGroup):
    waiting_for_food = State()
    waiting_for_weight = State()

# База даних користувачів
users_db = {}
USER_DATA_FILE = "users.json"

# База продуктів (калорії на 100г)
FOOD_DATABASE = {
    # Фрукти та ягоди
    "яблуко": 52, "банан": 89, "апельсин": 47, "груша": 57, "виноград": 62,
    "полуниця": 32, "малина": 52, "ківі": 61, "ананас": 50, "манго": 60,
    "персик": 39, "абрикос": 48, "слива": 46, "вишня": 50, "черешня": 63,
    "лимон": 16, "грейпфрут": 35, "арбуз": 30, "диня": 34, "гранат": 83,
    
    # Овочі
    "помідор": 18, "огірок": 16, "морква": 35, "капуста": 25, "картопля": 77,
    "буряк": 43, "цибуля": 40, "часник": 149, "перець болгарський": 27, "баклажан": 24,
    "кабачок": 23, "гарбуз": 26, "броколі": 34, "цвітна капуста": 30, "шпинат": 23,
    "салат": 15, "редис": 16, "селера": 14, "петрушка": 36, "кріп": 38,
    "редька": 34, "топінамбур": 61, "спаржа": 20,
    
    # М'ясо та птиця
    "куриця": 165, "яловичина": 187, "свинина": 242, "індичка": 144, "качка": 337,
    "телятина": 172, "баранина": 203, "кролик": 156, "печінка куряча": 140, "печінка яловича": 127,
    "серце": 112, "нирки": 86, "язик яловичий": 173, "ковбаса": 257, "сосиски": 266,
    "бекон": 541,
    
    # Риба та морепродукти
    "лосось": 208, "тунець": 144, "скумбрія": 191, "селедка": 246, "треска": 78,
    "судак": 84, "короп": 112, "щука": 84, "окунь": 103, "минтай": 72,
    "креветки": 106, "краби": 96, "мідії": 77, "кальмари": 110, "ікра червона": 263,
    "ікра чорна": 264, "лобстер": 89,
    
    # Молочні продукти
    "молоко": 60, "кефір": 56, "ряжанка": 85, "сметана": 206, "творог": 103,
    "сир твердий": 364, "сир м'який": 173, "йогурт": 66, "масло вершкове": 748,
    "згущене молоко": 320, "вершки": 118,
    
    # Крупи та каші
    "рис": 130, "гречка": 132, "вівсянка": 68, "манка": 98, "перловка": 109,
    "пшоно": 119, "киноа": 120, "булгур": 83, "кус-кус": 112,
    
    # Горіхи та насіння
    "волоські горіхи": 654, "мигдаль": 575, "фундук": 628, "арахіс": 551, "кешью": 553,
    "фісташки": 556, "кедрові горіхи": 673, "насіння соняшника": 578, "насіння гарбуза": 559,
    "льняне насіння": 534,
    
    # Солодощі
    "цукор": 387, "мед": 304, "шоколад молочний": 534, "шоколад чорний": 546, "варення": 263,
    "зефір": 326, "мармелад": 321, "халва": 516, "печиво": 417, "тортик": 400,
    "морозиво": 207,
    
    # Напої
    "чай зелений": 0, "чай чорний": 0, "кава без цукру": 2, "сік яблучний": 46,
    "сік апельсиновий": 45, "сік томатний": 17, "компот": 60, "квас": 27,
    "кола": 42, "пепсі": 41, "спрайт": 37, "фанта": 38, "енергетик": 45,
    
    # Хліб та вироби
    "хліб білий": 265, "хліб чорний": 210, "хліб житній": 181, "батон": 260,
    "булочка": 317, "круасан": 406, "лаваш": 236,
    
    # Алкогольні напої
    "пиво світле": 43, "пиво темне": 48, "вино червоне": 68, "вино біле": 66,
    "шампанське": 88, "горілка": 235, "коньяк": 239, "віскі": 250, "ром": 220,
    "джин": 263, "текіла": 231, "лікер": 327, "мартіні": 140, "самогон": 235,
    "наливка": 196, "глінтвейн": 132, "пунш": 165, "медовуха": 120, "сидр": 45,
    "абсент": 171, "бренді": 225,
    
    # Снеки та фастфуд
    "чіпси картопляні": 536, "чіпси кукурудзяні": 498, "попкорн": 387, "крекери": 440,
    "сухарики": 331, "піцца": 266, "бургер": 295, "хот-дог": 290, "картопля фрі": 365,
    "наггетси": 302, "тако": 217, "буріто": 206, "сендвіч": 252, "шаурма": 215,
    "донер": 230, "кебаб": 245, "паніні": 280, "багет": 155, "круасан з начинкою": 350,
    "претцель": 380, "начос": 346, "оніон рингс": 411, "моцарела стікс": 280,
    "курячі крильця": 203, "рибні палички": 238, "кальцоне": 274, "кальмари в кляре": 175,
    "сирні кульки": 320, "мініпіца": 280, "ролл каліфорнія": 176, "ролл філадельфія": 142,
    "суші з лососем": 142, "суші з тунцем": 144, "темпура": 255,
    
    # Делікатеси
    "моцарела": 280, "пармезан": 431, "фета": 264, "камамбер": 291, "бpи": 334,
    "дор блю": 353, "рокфор": 369, "чеддер": 402, "гауда": 356, "емменталь": 380,
    "маскарпоне": 429, "рікотта": 174, "салямі": 407, "прошутто": 335, "хамон": 241,
    "чорізо": 455, "пепероні": 494, "капіколло": 300, "панчетта": 458, "бастурма": 240,
    "в'ялене м'ясо": 410, "оливки зелені": 166, "маслини чорні": 361, "корнішони": 11,
    "каперси": 23
}

# Синоніми для продуктів
FOOD_SYNONYMS = {
    "курка": "куриця", "картошка": "картопля", "говядина": "яловичина",
    "молочко": "молоко", "рибка": "лосось", "м'ясо": "яловичина",
    "пивко": "пиво світле", "винце": "вино червоне", "горілочка": "горілка",
    "чіпсі": "чіпси картопляні", "попкон": "попкорн", "піца": "піцца",
    "бренді": "коньяк", "самогонка": "самогон", "макдак": "бургер",
    "фастфуд": "бургер", "хотдог": "хот-дог"
}

# Постійна клавіатура
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏠 Головне меню"), KeyboardButton(text="📊 Мій профіль")],
        [KeyboardButton(text="🍎 Калорії"), KeyboardButton(text="💧 Вода")],
        [KeyboardButton(text="⚖️ ІМТ"), KeyboardButton(text="💡 Поради")],
        [KeyboardButton(text="📈 Вага"), KeyboardButton(text="📅 Щоденник")]
    ],
    resize_keyboard=True,
    persistent=True
)

# Функції роботи з базою даних
def save_users():
    """Збереження даних користувачів у JSON"""
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_db, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Помилка збереження: {e}")

def load_users():
    """Завантаження даних користувачів з JSON"""
    global users_db
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                users_db = json.load(f)
    except Exception as e:
        print(f"Помилка завантаження: {e}")
        users_db = {}

# Функції розрахунків
def calculate_bmr(weight, height, age, gender):
    """Розрахунок базового метаболізму за формулою Харріса-Бенедикта"""
    if gender == "Чоловік":
        return round(88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age))
    else:
        return round(447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age))

def get_activity_multiplier(activity):
    """Коефіцієнт активності"""
    multipliers = {
        "Мінімальна (сидячий спосіб життя)": 1.2,
        "Легка (1-3 тренування на тиждень)": 1.375,
        "Помірна (3-5 тренувань на тиждень)": 1.55,
        "Активна (6-7 тренувань на тиждень)": 1.725,
        "Дуже активна (2 тренування на день)": 1.9
    }
    return multipliers.get(activity, 1.2)

def calculate_daily_calories(bmr, activity):
    """Розрахунок денної норми калорій"""
    multiplier = get_activity_multiplier(activity)
    return round(bmr * multiplier)

def adjust_calories_for_goal(daily_calories, goal):
    """Коригування калорій відповідно до мети"""
    if goal == "Схуднути":
        return daily_calories - 500
    elif goal == "Набрати вагу":
        return daily_calories + 500
    return daily_calories

def calculate_bmi(weight, height):
    """Розрахунок індексу маси тіла"""
    height_m = height / 100
    return round(weight / (height_m ** 2), 1)

def get_bmi_category(bmi):
    """Категорія ІМТ"""
    if bmi < 18.5:
        return "Недостатня вага", "🔵"
    elif 18.5 <= bmi < 25:
        return "Нормальна вага", "🟢"
    elif 25 <= bmi < 30:
        return "Надлишкова вага", "🟡"
    else:
        return "Ожиріння", "🔴"

def calculate_water_intake(weight, activity):
    """Розрахунок норми води"""
    base_water = weight * 35  # мл на кг
    activity_multiplier = get_activity_multiplier(activity)
    if activity_multiplier > 1.5:
        base_water *= 1.2
    elif activity_multiplier > 1.3:
        base_water *= 1.1
    return round(base_water)

# Обробники кнопок постійної клавіатури (ВАЖЛИВО: ПЕРЕД FSM обробниками)
@dp.message(F.text == "🏠 Головне меню")
async def main_menu_button(message: Message):
    await main_menu(message)

@dp.message(F.text == "📊 Мій профіль")
async def profile_button(message: Message):
    await show_profile(message)

@dp.message(F.text == "🍎 Калорії")
async def calories_button(message: Message, state: FSMContext):
    await message.answer("🍎 Введіть назву продукту для розрахунку калорій:")
    await state.set_state(FoodCalories.waiting_for_food)

@dp.message(F.text == "💧 Вода")
async def water_button(message: Message):
    await show_water_recommendations(message)

@dp.message(F.text == "⚖️ ІМТ")
async def bmi_button(message: Message):
    await show_bmi_info(message)

@dp.message(F.text == "💡 Поради")
async def tips_button(message: Message):
    await show_daily_tips(message)

@dp.message(F.text == "📈 Вага")
async def weight_button(message: Message):
    await show_weight_tracker_menu(message)

@dp.message(F.text == "📅 Щоденник")
async def diary_button(message: Message):
    await show_food_diary_menu(message)

# Основні функції
async def main_menu(message: Message):
    """Показ головного меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Створити профіль", callback_data="create_profile")],
        [InlineKeyboardButton(text="🍎 Розрахувати калорії продукту", callback_data="calculate_food")],
        [InlineKeyboardButton(text="📈 Мій профіль", callback_data="my_profile")],
        [InlineKeyboardButton(text="💧 Норма води", callback_data="water_intake")],
        [InlineKeyboardButton(text="⚖️ Розрахунок ІМТ", callback_data="calculate_bmi")],
        [InlineKeyboardButton(text="💡 Щоденні поради", callback_data="daily_tips")],
        [InlineKeyboardButton(text="ℹ️ Допомога", callback_data="help")]
    ])
    
    menu_image = "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=800&h=600&fit=crop"
    
    await message.answer_photo(
        photo=menu_image,
        caption="🏠 Головне меню\n\nВітаю у боті для здорового харчування!\nОберіть, що ви хочете зробити:",
        reply_markup=keyboard
    )

async def show_profile(message: Message):
    """Показ профілю користувача"""
    user_id = str(message.from_user.id)
    
    if user_id not in users_db:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Створити профіль", callback_data="create_profile")]
        ])
        await message.answer(
            "👤 У вас ще немає профілю 😔\n\nСтворіть профіль для отримання персональних рекомендацій!",
            reply_markup=keyboard
        )
        return
    
    user = users_db[user_id]
    profile_text = f"""
👤 **Ваш профіль:**

📋 **Основні дані:**
• Ім'я: {user.get('name', 'Не вказано')}
• Стать: {user['gender']}
• Вік: {user['age']} років
• Зріст: {user['height']} см
• Вага: {user['weight']} кг
• Активність: {user['activity']}
• Мета: {user['goal']}

📊 **Розрахунки:**
• Базовий метаболізм: {user['bmr']} ккал/день
• Денна норма: {user['daily_calories']} ккал/день
• Рекомендовано: {user['target_calories']} ккал/день

💧 **Вода:** {calculate_water_intake(user['weight'], user['activity'])} мл/день
⚖️ **ІМТ:** {calculate_bmi(user['weight'], user['height'])}
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Оновити профіль", callback_data="create_profile")],
        [InlineKeyboardButton(text="💧 Норма води", callback_data="water_intake")],
        [InlineKeyboardButton(text="⚖️ Розрахунок ІМТ", callback_data="calculate_bmi")]
    ])
    
    profile_image = "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=600&fit=crop"
    
    await message.answer_photo(
        photo=profile_image,
        caption=profile_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def show_water_recommendations(message: Message):
    """Рекомендації води"""
    user_id = str(message.from_user.id)
    
    if user_id not in users_db:
        await message.answer("💧 Для розрахунку норми води створіть профіль!")
        return
    
    user = users_db[user_id]
    water_ml = calculate_water_intake(user['weight'], user['activity'])
    water_glasses = round(water_ml / 250)
    
    water_text = f"""
💧 **Ваша денна норма води:**

📊 **Рекомендації:**
• **{water_ml} мл** на день
• Це приблизно **{water_glasses} склянок** по 250мл
• Пийте рівномірно протягом дня

💡 **Поради:**
• Почніть день зі склянки води
• Пийте воду за 30 хв до їжі
• Носіть пляшку води з собою
• Додайте лимон для смаку
    """
    
    water_image = "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=800&h=600&fit=crop"
    
    await message.answer_photo(
        photo=water_image,
        caption=water_text,
        parse_mode='Markdown'
    )

async def show_bmi_info(message: Message):
    """Інформація про ІМТ"""
    user_id = str(message.from_user.id)
    
    if user_id not in users_db:
        await message.answer("⚖️ Для розрахунку ІМТ створіть профіль!")
        return
    
    user = users_db[user_id]
    bmi = calculate_bmi(user['weight'], user['height'])
    category, emoji = get_bmi_category(bmi)
    
    bmi_text = f"""
⚖️ **Ваш індекс маси тіла (ІМТ):**

📊 **Розрахунок:**
• **ІМТ: {bmi}**
• {emoji} **Категорія:** {category}

📈 **Шкала ІМТ:**
🔵 **< 18.5** - недостатня вага
🟢 **18.5-24.9** - нормальна вага
🟡 **25.0-29.9** - надлишкова вага
🔴 **≥ 30.0** - ожиріння

💡 **Рекомендації:** {'Відмінно! Підтримуйте поточну вагу.' if category == 'Нормальна вага' else 'Розгляньте можливість корегування ваги.'}
    """
    
    bmi_image = "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=600&fit=crop"
    
    await message.answer_photo(
        photo=bmi_image,
        caption=bmi_text,
        parse_mode='Markdown'
    )

async def show_daily_tips(message: Message):
    """Щоденні поради"""
    tips = [
        "🥗 Їжте 5 порцій овочів та фруктів на день",
        "🚶 Робіть мінімум 10,000 кроків щодня",
        "💤 Спіть 7-9 годин для відновлення організму",
        "🥛 Пийте воду одразу після пробудження",
        "🍽️ Їжте повільно та ретельно пережовуйте",
        "🥜 Додайте горіхи до сніданку",
        "🐟 Їжте рибу 2-3 рази на тиждень",
        "🥦 Готуйте овочі на парі замість смаження",
        "🍯 Замініть цукор на мед",
        "🧘 Медитуйте 10 хвилин на день",
        "🏃 Робіть перерви для активності кожні 2 години",
        "🥑 Включайте корисні жири в раціон",
        "🌱 Їжте цільнозернові продукти",
        "🍊 Не пропускайте сніданок",
        "💆 Робіть масаж для покращення кровообігу",
        "🌿 Додавайте зелень до кожного прийому їжі",
        "🏋️ Займайтеся силовими тренуваннями 2 рази на тиждень",
        "🧊 Приймайте контрастний душ",
        "📱 Обмежте час перед екранами",
        "🌅 Прокидайтеся в один і той же час"
    ]
    
    daily_tips_list = random.sample(tips, 5)
    tips_text = "\n".join([f"{i+1}. {tip}" for i, tip in enumerate(daily_tips_list)])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Нові поради", callback_data="daily_tips")]
    ])
    
    tips_full_text = f"💡 **Щоденні поради для здоров'я:**\n\n{tips_text}"
    
    tips_image = "https://images.unsplash.com/photo-1506629905107-bb5842dcbc67?w=800&h=600&fit=crop"
    
    await message.answer_photo(
        photo=tips_image,
        caption=tips_full_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def show_weight_tracker_menu(message: Message):
    """Меню трекера ваги"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Додати вагу", callback_data="add_weight")],
        [InlineKeyboardButton(text="📊 Показати прогрес", callback_data="show_progress")]
    ])
    
    await message.answer(
        "📈 **Трекер ваги**\n\nВиберіть дію:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def show_food_diary_menu(message: Message):
    """Меню щоденника харчування"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Додати продукт", callback_data="add_food_diary")],
        [InlineKeyboardButton(text="📊 Показати за сьогодні", callback_data="show_today_diary")]
    ])
    
    await message.answer(
        "📅 **Щоденник харчування**\n\nВиберіть дію:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# Команда /start
@dp.message(CommandStart())
async def start_handler(message: Message):
    user_name = message.from_user.first_name or "Користувач"
    
    start_text = f"""
👋 Привіт, **{user_name}**!

Я ваш персональний помічник для здорового харчування! 🥗

🎯 **Що я можу:**
• Розраховувати калорії продуктів
• Створювати персональний профіль
• Рахувати норму води та ІМТ
• Давати корисні поради
• Відстежувати прогрес ваги

Почнемо з головного меню! 👇
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Розпочати", callback_data="main_menu")]
    ])
    
    start_image = "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=800&h=600&fit=crop"
    
    await message.answer_photo(
        photo=start_image,
        caption=start_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# Обробник callback запитів
@dp.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    await callback.message.delete()
    await main_menu(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "my_profile")
async def my_profile_callback(callback: CallbackQuery):
    await callback.message.delete()
    await show_profile(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "create_profile")
async def create_profile_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("👋 Як до вас звертатися?")
    await state.set_state(UserProfile.waiting_for_name)
    await callback.answer()

@dp.callback_query(F.data == "calculate_food")
async def calculate_food_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("🍎 Введіть назву продукту для розрахунку калорій:")
    await state.set_state(FoodCalories.waiting_for_food)
    await callback.answer()

@dp.callback_query(F.data == "water_intake")
async def water_intake_callback(callback: CallbackQuery):
    await callback.message.delete()
    await show_water_recommendations(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "calculate_bmi")
async def calculate_bmi_callback(callback: CallbackQuery):
    await callback.message.delete()
    await show_bmi_info(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "daily_tips")
async def daily_tips_callback(callback: CallbackQuery):
    await callback.message.delete()
    await show_daily_tips(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "add_weight")
async def add_weight_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("📈 Введіть вашу поточну вагу (кг):")
    await state.set_state(WeightTracker.waiting_for_weight)
    await callback.answer()

@dp.callback_query(F.data == "add_food_diary")
async def add_food_diary_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("📅 Введіть назву продукту для додавання до щоденника:")
    await state.set_state(FoodDiary.waiting_for_food)
    await callback.answer()

# FSM обробники для створення профілю
@dp.message(UserProfile.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("👤 Оберіть вашу стать:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨 Чоловік", callback_data="gender_male")],
        [InlineKeyboardButton(text="👩 Жінка", callback_data="gender_female")]
    ]))

@dp.callback_query(F.data.startswith("gender_"))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    gender = "Чоловік" if callback.data == "gender_male" else "Жінка"
    await state.update_data(gender=gender)
    await callback.message.edit_text("🎂 Введіть ваш вік (років):")
    await state.set_state(UserProfile.waiting_for_age)
    await callback.answer()

@dp.message(UserProfile.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        if 10 <= age <= 100:
            await state.update_data(age=age)
            await message.answer("⚖️ Введіть вашу вагу (кг):")
            await state.set_state(UserProfile.waiting_for_weight)
        else:
            await message.answer("❌ Вік повинен бути від 10 до 100 років. Спробуйте ще раз:")
    except ValueError:
        await message.answer("❌ Введіть вік числом. Спробуйте ще раз:")

@dp.message(UserProfile.waiting_for_weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
        if 30 <= weight <= 300:
            await state.update_data(weight=weight)
            await message.answer("📏 Введіть ваш зріст (см):")
            await state.set_state(UserProfile.waiting_for_height)
        else:
            await message.answer("❌ Вага повинна бути від 30 до 300 кг. Спробуйте ще раз:")
    except ValueError:
        await message.answer("❌ Введіть вагу числом. Спробуйте ще раз:")

@dp.message(UserProfile.waiting_for_height)
async def process_height(message: Message, state: FSMContext):
    try:
        height = int(message.text)
        if 100 <= height <= 250:
            await state.update_data(height=height)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛋️ Мінімальна", callback_data="activity_minimal")],
                [InlineKeyboardButton(text="🚶 Легка", callback_data="activity_light")],
                [InlineKeyboardButton(text="🏃 Помірна", callback_data="activity_moderate")],
                [InlineKeyboardButton(text="💪 Активна", callback_data="activity_active")],
                [InlineKeyboardButton(text="🏋️ Дуже активна", callback_data="activity_very_active")]
            ])
            
            await message.answer(
                "⚡ Оберіть рівень вашої фізичної активності:\n\n"
                "🛋️ **Мінімальна** - сидячий спосіб життя\n"
                "🚶 **Легка** - 1-3 тренування на тиждень\n"
                "🏃 **Помірна** - 3-5 тренувань на тиждень\n" 
                "💪 **Активна** - 6-7 тренувань на тиждень\n"
                "🏋️ **Дуже активна** - професійний спорт",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            await state.set_state(UserProfile.waiting_for_activity)
        else:
            await message.answer("❌ Зріст повинен бути від 100 до 250 см. Спробуйте ще раз:")
    except ValueError:
        await message.answer("❌ Введіть зріст числом. Спробуйте ще раз:")

@dp.callback_query(F.data.startswith("activity_"))
async def process_activity(callback: CallbackQuery, state: FSMContext):
    activities = {
        "activity_minimal": "Мінімальна (сидячий спосіб життя)",
        "activity_light": "Легка (1-3 тренування на тиждень)",
        "activity_moderate": "Помірна (3-5 тренувань на тиждень)",
        "activity_active": "Активна (6-7 тренувань на тиждень)",
        "activity_very_active": "Дуже активна (2 тренування на день)"
    }
    
    activity = activities[callback.data]
    await state.update_data(activity=activity)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📉 Схуднути", callback_data="goal_lose")],
        [InlineKeyboardButton(text="⚖️ Підтримувати вагу", callback_data="goal_maintain")],
        [InlineKeyboardButton(text="📈 Набрати вагу", callback_data="goal_gain")]
    ])
    
    await callback.message.edit_text("🎯 Яка ваша мета?", reply_markup=keyboard)
    await state.set_state(UserProfile.waiting_for_goal)
    await callback.answer()

@dp.callback_query(F.data.startswith("goal_"))
async def process_goal(callback: CallbackQuery, state: FSMContext):
    goals = {
        "goal_lose": "Схуднути",
        "goal_maintain": "Підтримувати вагу", 
        "goal_gain": "Набрати вагу"
    }
    
    goal = goals[callback.data]
    data = await state.get_data()
    
    # Розрахунки
    bmr = calculate_bmr(data['weight'], data['height'], data['age'], data['gender'])
    daily_calories = calculate_daily_calories(bmr, data['activity'])
    target_calories = adjust_calories_for_goal(daily_calories, goal)
    
    # Збереження профілю
    user_id = str(callback.from_user.id)
    users_db[user_id] = {
        'name': data['name'],
        'gender': data['gender'],
        'age': data['age'],
        'weight': data['weight'],
        'height': data['height'],
        'activity': data['activity'],
        'goal': goal,
        'bmr': bmr,
        'daily_calories': daily_calories,
        'target_calories': target_calories,
        'created_at': datetime.now().isoformat()
    }
    
    save_users()
    
    success_text = f"""
✅ **Профіль створено успішно!**

👤 **{data['name']}** ({data['gender']})
📊 **Ваші рекомендації:**

🔥 **Базовий метаболізм:** {bmr} ккал/день
⚡ **Денна норма:** {daily_calories} ккал/день  
🎯 **Для досягнення мети:** {target_calories} ккал/день
💧 **Норма води:** {calculate_water_intake(data['weight'], data['activity'])} мл/день

Тепер ви можете користуватися всіма функціями бота! 🎉
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍎 Розрахувати калорії", callback_data="calculate_food")],
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(success_text, reply_markup=keyboard, parse_mode='Markdown')
    await state.clear()
    await callback.answer("Профіль створено! 🎉")

# FSM обробники для розрахунку калорій
@dp.message(FoodCalories.waiting_for_food)
async def process_food_search(message: Message, state: FSMContext):
    product_name = message.text.lower().strip()
    
    # Пошук продукту
    found_product = None
    for product, calories in FOOD_DATABASE.items():
        if product_name in product or product in product_name:
            found_product = (product, calories)
            break
    
    # Перевірка синонімів
    if not found_product:
        for synonym, real_name in FOOD_SYNONYMS.items():
            if synonym in product_name:
                if real_name in FOOD_DATABASE:
                    found_product = (real_name, FOOD_DATABASE[real_name])
                    break
    
    if found_product:
        await message.answer(f"🍽️ Знайдено продукт: **{found_product[0]}**\n\n💡 Введіть вагу в грамах (наприклад: 100):", parse_mode='Markdown')
        await state.update_data(product_name=found_product[0], calories_per_100g=found_product[1])
        await state.set_state(FoodCalories.waiting_for_weight)
    else:
        # Показуємо популярні продукти
        popular_products = "🍎 яблуко, 🍌 банан, 🍗 куриця, 🥩 яловичина, 🥛 молоко, 🍞 хліб, 🍚 рис, 🥔 картопля"
        await message.answer(
            f"😕 Продукт '**{product_name}**' не знайдено.\n\n"
            f"💡 **Популярні продукти:**\n{popular_products}\n\n"
            f"🔍 Спробуйте ввести іншу назву або оберіть з популярних.",
            parse_mode='Markdown'
        )

@dp.message(FoodCalories.waiting_for_weight)
async def process_food_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
        if 1 <= weight <= 5000:
            data = await state.get_data()
            calories = round((data['calories_per_100g'] * weight) / 100)
            
            # Визначаємо категорію продукту для картинки
            product = data['product_name'].lower()
            
            if any(fruit in product for fruit in ['яблуко', 'банан', 'апельсин', 'груша', 'ківі', 'ананас']):
                image_url = "https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=800&h=600&fit=crop"
            elif any(veg in product for veg in ['помідор', 'огірок', 'морква', 'капуста', 'картопля']):
                image_url = "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=800&h=600&fit=crop"
            elif any(meat in product for meat in ['куриця', 'яловичина', 'свинина', 'м\'ясо']):
                image_url = "https://images.unsplash.com/photo-1588347818192-6d9c4541ea8f?w=800&h=600&fit=crop"
            else:
                image_url = "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=800&h=600&fit=crop"
            
            result_text = f"""
🍽️ **Результат розрахунку:**

📦 **Продукт:** {data['product_name']}
⚖️ **Вага:** {weight} г
🔥 **Калорії:** {calories} ккал

📊 **Додаткова інформація:**
• Калорійність на 100г: {data['calories_per_100g']} ккал
• Відсоток від денної норми: {round(calories/2000*100, 1)}%
            """
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Інший продукт", callback_data="calculate_food")],
                [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
            ])
            
            await message.answer_photo(
                photo=image_url,
                caption=result_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            await state.clear()
        else:
            await message.answer("❌ Вага повинна бути від 1 до 5000 г. Спробуйте ще раз:")
    except ValueError:
        await message.answer("❌ Введіть вагу числом. Спробуйте ще раз:")

# Додамо більше обробників callback_query
@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    help_text = """
ℹ️ **Довідка по боту**

🎯 **Основні функції:**
• **📊 Профіль** - створення персонального профілю
• **🍎 Калорії** - розрахунок калорій продуктів  
• **💧 Вода** - норма води на день
• **⚖️ ІМТ** - індекс маси тіла
• **💡 Поради** - щоденні рекомендації

🔍 **Як користуватися:**
1. Створіть профіль для персональних рекомендацій
2. Використовуйте кнопки внизу для швидкого доступу
3. Вводьте назви продуктів для розрахунку калорій

❓ **Питання?** Пишіть /start для перезапуску
    """
    
    help_image = "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=800&h=600&fit=crop"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])
    
    await callback.message.answer_photo(
        photo=help_image,
        caption=help_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    await callback.answer()

# Головна функція
async def main():
    """Головна функція запуску бота"""
    load_users()
    print("🚀 Бот запущено успішно!")
    print(f"📊 Завантажено {len(users_db)} користувачів")
    print(f"🍎 База продуктів: {len(FOOD_DATABASE)} позицій")
    
    try:
        await bot.set_my_commands([
            types.BotCommand(command="start", description="🚀 Запустити бота"),
            types.BotCommand(command="help", description="ℹ️ Довідка")
        ])
        
        await dp.start_polling(bot, allowed_updates=['message', 'callback_query'])
    except Exception as e:
        print(f"❌ Помилка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())