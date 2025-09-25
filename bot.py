import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram import types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import json
import os
from datetime import datetime

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
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_height = State()
    waiting_for_weight = State()
    waiting_for_activity = State()
    waiting_for_goal = State()

class FoodCalories(StatesGroup):
    waiting_for_food = State()
    waiting_for_weight_food = State()

class WeightTracker(StatesGroup):
    waiting_for_weight = State()

class FoodDiary(StatesGroup):
    waiting_for_food_diary = State()
    waiting_for_food_weight_diary = State()

class DishConstructor(StatesGroup):
    waiting_for_dish_name = State()
    waiting_for_ingredients = State()
    waiting_for_ingredient_weight = State()

# База даних користувачів (в реальному проекті краще використовувати БД)
users_db = {}

# Постійна клавіатура головного меню
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏠 Головне меню"), KeyboardButton(text="📊 Мій профіль")],
        [KeyboardButton(text="🍎 Калорії"), KeyboardButton(text="💧 Вода")],
        [KeyboardButton(text="⚖️ ІМТ"), KeyboardButton(text="💡 Поради")],
        [KeyboardButton(text="📈 Вага"), KeyboardButton(text="📅 Щоденник")]
    ],
    resize_keyboard=True,
    persistent=True,
    placeholder="Оберіть дію..."
)

# База даних продуктів (калорії на 100г)
food_db = {
    # 🍎 Фрукти та ягоди
    "яблуко": 52,
    "банан": 89,
    "апельсин": 47,
    "мандарин": 53,
    "лимон": 29,
    "грейпфрут": 35,
    "груша": 57,
    "персик": 39,
    "абрикос": 48,
    "слива": 46,
    "вишня": 52,
    "черешня": 63,
    "виноград": 65,
    "полуниця": 32,
    "малина": 46,
    "чорниця": 57,
    "смородина": 44,
    "ківі": 61,
    "ананас": 50,
    "манго": 60,
    
    # 🥕 Овочі
    "помідор": 18,
    "огірок": 16,
    "морква": 41,
    "цибуля": 40,
    "картопля": 77,
    "капуста": 25,
    "буряк": 43,
    "кабачок": 24,
    "баклажан": 24,
    "перець": 27,
    "перець болгарський": 27,
    "перець гострий": 40,
    "салат": 14,
    "шпинат": 23,
    "броколі": 34,
    "цвітна капуста": 25,
    "кукурудза": 96,
    "горошок": 81,
    "квасоля": 93,
    "редиска": 19,
    "редька": 36,
    "часник": 149,
    "імбир": 80,
    
    # 🌾 Крупи та каші
    "рис": 130,
    "гречка": 343,
    "вівсянка": 389,
    "пшоно": 348,
    "перловка": 320,
    "манка": 328,
    "кукурудзяна каша": 337,
    "ячмінь": 288,
    "киноа": 368,
    
    # 🍞 Хлібобулочні вироби
    "хліб": 265,
    "хліб чорний": 214,
    "хліб білий": 265,
    "батон": 260,
    "лаваш": 236,
    "тости": 290,
    "сухарики": 331,
    "печиво": 417,
    "пряники": 364,
    
    # 🍝 Макаронні вироби
    "макарони": 371,
    "спагеті": 371,
    "лапша": 322,
    "вермішель": 371,
    
    # 🥛 Молочні продукти
    "молоко": 60,
    "кефір": 56,
    "ряжанка": 85,
    "сметана": 206,
    "йогурт": 59,
    "творог": 101,
    "сир": 402,
    "сир російський": 364,
    "сир голландський": 377,
    "сир козячий": 364,
    "масло вершкове": 717,
    "вершки": 118,
    
    # 🥚 Яйця
    "яйце": 155,
    "яйце курече": 155,
    "яйце перепелине": 168,
    "яєчний білок": 52,
    "яєчний жовток": 322,
    
    # 🍖 М'ясо
    "яловичина": 187,
    "свинина": 259,
    "баранина": 203,
    "телятина": 97,
    "куриця": 165,
    "індичка": 104,
    "качка": 405,
    "гусак": 412,
    "кролик": 156,
    "печінка": 135,
    "серце": 87,
    "нирки": 66,
    "ковбаса": 301,
    "сосиски": 266,
    "шинка": 270,
    "бекон": 541,
    
    # 🐟 Риба та морепродукти
    "риба": 206,
    "лосось": 208,
    "тунець": 296,
    "скумбрія": 305,
    "селедка": 262,
    "щука": 84,
    "судак": 84,
    "короп": 112,
    "минтай": 72,
    "хек": 86,
    "треска": 78,
    "камбала": 83,
    "креветки": 95,
    "краби": 96,
    "кальмари": 110,
    "мідії": 77,
    "ікра": 263,
    
    # 🥜 Горіхи та насіння
    "волоські горіхи": 654,
    "мигдаль": 575,
    "фундук": 628,
    "арахіс": 567,
    "кедрові горіхи": 673,
    "кешью": 553,
    "фісташки": 556,
    "насіння соняшника": 578,
    "насіння гарбуза": 559,
    "кунжут": 565,
    
    # 🫘 Бобові
    "горох": 298,
    "квасоля біла": 102,
    "квасоля червона": 93,
    "сочевиця": 295,
    "нут": 364,
    "соя": 381,
    
    # 🍯 Солодощі та цукор
    "цукор": 387,
    "мед": 329,
    "варення": 263,
    "джем": 263,
    "шоколад": 546,
    "шоколад молочний": 534,
    "шоколад чорний": 539,
    "цукерки": 453,
    "мармелад": 321,
    "зефір": 326,
    "халва": 516,
    
    # 🧂 Олії та жири
    "олія соняшникова": 899,
    "олія оливкова": 884,
    "олія кукурудзяна": 899,
    "маргарин": 719,
    "сало": 797,
    
    # 🥤 Напої безалкогольні
    "чай": 0,
    "кава": 2,
    "сік яблучний": 46,
    "сік апельсиновий": 36,
    "сік томатний": 21,
    "компот": 85,
    "морс": 41,
    "квас": 27,
    "лимонад": 26,
    "кола": 42,
    "пепсі": 41,
    "спрайт": 37,
    "фанта": 38,
    "енергетик": 45,
    "вода": 0,
    "мінеральна вода": 0,
    
    # 🍺 Алкогольні напої
    "пиво світле": 43,
    "пиво темне": 48,
    "пиво безалкогольне": 26,
    "вино червоне": 68,
    "вино біле": 66,
    "шампанське": 88,
    "горілка": 235,
    "коньяк": 239,
    "віскі": 250,
    "ром": 220,
    "джин": 263,
    "текіла": 231,
    "абсент": 83,
    "лікер": 327,
    "мартіні": 140,
    "самогон": 235,
    "наливка": 196,
    "глінтвейн": 132,
    "пунш": 260,
    "коктейль алкогольний": 150,
    
    # 🌿 Зелень та спеції
    "петрушка": 36,
    "кріп": 38,
    "зелена цибуля": 19,
    "базилік": 27,
    "м'ята": 70,
    "розмарин": 331,
    "орегано": 306,
    "тим'ян": 276,
    
    # 🍄 Гриби
    "гриби білі": 22,
    "шампіньйони": 27,
    "лисички": 38,
    "підберезники": 31,
    "опеньки": 17,
    "печериці": 27,
    
    # 🍿 Снеки та закуски
    "чіпси картопляні": 536,
    "чіпси кукурудзяні": 498,
    "попкорн": 387,
    "попкорн солодкий": 401,
    "попкорн солоний": 375,
    "крекери": 440,
    "сухарики": 331,
    "брецелі": 380,
    "кільця луково": 410,
    "снеки сирні": 520,
    "горішки солоні": 607,
    "горішки в глазурі": 580,
    "насіння смажене": 601,
    "сушена риба": 462,
    "сушене м'ясо": 550,
    "ковбаса сушена": 473,
    "піцца": 266,
    "бургер": 295,
    "хот-дог": 290,
    "сендвіч": 304,
    "шаурма": 215,
    "начос": 346,
    "тако": 226,
    "картопля фрі": 365,
    "пончики": 452,
    "вафлі": 305,
    "тістечка": 544,
    "кекси": 389,
    "маффіни": 377,
    "круасани": 406,
    "багет": 278,
    "піта": 275,
    
    # 🧀 Закусочні сири та делікатеси
    "сир плавлений": 226,
    "сир з пліснявою": 353,
    "моцарела": 280,
    "пармезан": 431,
    "фета": 264,
    "камамбер": 299,
    "чеддер": 403,
    "маскарпоне": 429,
    "рокфор": 369,
    "крем-сир": 342,
    "салямі": 407,
    "прошутто": 335,
    "пепероні": 494,
    "хамон": 241,
    "оливки": 166,
    "маслини": 361,
    "каперси": 23,
    "корнішони": 11,
    "оселедець": 262,
    "ікра червона": 263,
    "ікра чорна": 264,
    "паштет": 301,
    "тушонка": 338
}

def load_users():
    """Завантаження користувачів з файлу"""
    global users_db
    if os.path.exists('users.json'):
        with open('users.json', 'r', encoding='utf-8') as f:
            users_db = json.load(f)

def save_users():
    """Збереження користувачів у файл"""
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users_db, f, ensure_ascii=False, indent=2)

def calculate_bmr(gender, age, height, weight):
    """Розрахунок базового метаболізму за формулою Харріса-Бенедикта"""
    if gender.lower() == 'чоловік':
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    return round(bmr)

def calculate_daily_calories(bmr, activity_level):
    """Розрахунок денної норми калорій"""
    activity_multipliers = {
        'мінімальна': 1.2,
        'легка': 1.375,
        'помірна': 1.55,
        'активна': 1.725,
        'дуже активна': 1.9
    }
    return round(bmr * activity_multipliers.get(activity_level, 1.2))

def adjust_calories_for_goal(daily_calories, goal):
    """Коригування калорій залежно від мети"""
    if goal == 'схуднути':
        return daily_calories - 500
    elif goal == 'набрати вагу':
        return daily_calories + 500
    else:
        return daily_calories

def calculate_bmi(weight, height):
    """Розрахунок індексу маси тіла (ІМТ)"""
    height_m = height / 100  # переводимо см в метри
    bmi = weight / (height_m ** 2)
    return round(bmi, 1)

def get_bmi_category(bmi):
    """Визначення категорії ІМТ"""
    if bmi < 18.5:
        return "недостатня вага", "🔵"
    elif 18.5 <= bmi < 25:
        return "нормальна вага", "🟢"
    elif 25 <= bmi < 30:
        return "надлишкова вага", "🟡"
    else:
        return "ожиріння", "🔴"

def calculate_water_intake(weight, activity_level):
    """Розрахунок норми води"""
    base_water = weight * 35  # 35 мл на кг ваги
    
    # Коригування залежно від активності
    activity_multipliers = {
        'мінімальна': 1.0,
        'легка': 1.1,
        'помірна': 1.2,
        'активна': 1.3,
        'дуже активна': 1.4
    }
    
    water_ml = base_water * activity_multipliers.get(activity_level, 1.0)
    return round(water_ml)

def add_weight_record(user_id, weight):
    """Додавання запису ваги"""
    if user_id not in users_db:
        return False
    
    if 'weight_history' not in users_db[user_id]:
        users_db[user_id]['weight_history'] = []
    
    # Додаємо новий запис
    weight_record = {
        'weight': weight,
        'date': datetime.now().isoformat(),
        'timestamp': datetime.now().timestamp()
    }
    
    users_db[user_id]['weight_history'].append(weight_record)
    users_db[user_id]['weight'] = weight  # Оновлюємо поточну вагу
    
    # Зберігаємо тільки останні 100 записів
    if len(users_db[user_id]['weight_history']) > 100:
        users_db[user_id]['weight_history'] = users_db[user_id]['weight_history'][-100:]
    
    save_users()
    return True

def get_weight_progress(user_id):
    """Отримання прогресу ваги"""
    if user_id not in users_db or 'weight_history' not in users_db[user_id]:
        return None
    
    history = users_db[user_id]['weight_history']
    if len(history) < 2:
        return None
    
    # Останній і перший запис
    current = history[-1]
    first = history[0]
    
    # Прогрес за весь період
    total_change = current['weight'] - first['weight']
    
    # Прогрес за останні 7 днів
    week_ago = datetime.now().timestamp() - (7 * 24 * 60 * 60)
    recent_records = [r for r in history if r['timestamp'] > week_ago]
    
    week_change = 0
    if len(recent_records) >= 2:
        week_change = recent_records[-1]['weight'] - recent_records[0]['weight']
    
    return {
        'total_change': total_change,
        'week_change': week_change,
        'current_weight': current['weight'],
        'start_weight': first['weight'],
        'records_count': len(history)
    }

def add_food_diary_entry(user_id, food_name, weight, calories):
    """Додавання запису в щоденник харчування"""
    if user_id not in users_db:
        return False
    
    if 'food_diary' not in users_db[user_id]:
        users_db[user_id]['food_diary'] = []
    
    # Додаємо новий запис
    diary_entry = {
        'food_name': food_name,
        'weight': weight,
        'calories': calories,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time': datetime.now().strftime('%H:%M'),
        'timestamp': datetime.now().timestamp()
    }
    
    users_db[user_id]['food_diary'].append(diary_entry)
    
    # Зберігаємо тільки останні 1000 записів
    if len(users_db[user_id]['food_diary']) > 1000:
        users_db[user_id]['food_diary'] = users_db[user_id]['food_diary'][-1000:]
    
    save_users()
    return True

def get_daily_calories(user_id, date=None):
    """Отримання калорій за день"""
    if user_id not in users_db or 'food_diary' not in users_db[user_id]:
        return 0
    
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    daily_entries = [entry for entry in users_db[user_id]['food_diary'] if entry['date'] == date]
    total_calories = sum(entry['calories'] for entry in daily_entries)
    
    return total_calories, daily_entries

@dp.message(CommandStart())
async def start_handler(message: Message):
    """Обробник команди /start"""
    user_id = str(message.from_user.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Створити профіль", callback_data="create_profile")],
        [InlineKeyboardButton(text="🍎 Розрахувати калорії продукту", callback_data="calculate_food")],
        [InlineKeyboardButton(text="📈 Мій профіль", callback_data="my_profile")],
        [InlineKeyboardButton(text="💧 Норма води", callback_data="water_intake")],
        [InlineKeyboardButton(text="⚖️ Розрахунок ІМТ", callback_data="calculate_bmi")],
        [InlineKeyboardButton(text="💡 Щоденні поради", callback_data="daily_tips")],
        [InlineKeyboardButton(text="ℹ️ Допомога", callback_data="help")]
    ])
    
    # Відправляємо фото з привітанням
    photo_url = "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=800&h=600&fit=crop"
    
    await message.answer_photo(
        photo=photo_url,
        caption=f"Привіт, {message.from_user.first_name}! 👋\n\n"
                "Я бот для розрахування калорій та підтримки дієти! 🥗\n\n"
                "📊 Розраховую BMR та денну норму калорій\n"
                "🍎 Знаю калорійність 250+ продуктів\n"
                "💡 Даю персональні рекомендації\n\n"
                "Що ти хочеш зробити?",
        reply_markup=keyboard
    )
    
    # Встановлюємо постійну клавіатуру
    await message.answer(
        "🎯 Швидкий доступ до функцій:",
        reply_markup=main_keyboard
    )

@dp.callback_query(F.data == "create_profile")
async def create_profile(callback: CallbackQuery, state: FSMContext):
    """Початок створення профілю"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨 Чоловік", callback_data="gender_male")],
        [InlineKeyboardButton(text="👩 Жінка", callback_data="gender_female")]
    ])
    
    await callback.message.edit_text(
        "Давайте створимо ваш профіль! 📝\n\n"
        "Спочатку оберіть вашу стать:",
        reply_markup=keyboard
    )
    await state.set_state(UserProfile.waiting_for_gender)

@dp.callback_query(F.data.in_(["gender_male", "gender_female"]))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору статі"""
    gender = "чоловік" if callback.data == "gender_male" else "жінка"
    await state.update_data(gender=gender)
    
    await callback.message.edit_text(
        f"Стать: {gender} ✅\n\n"
        "Тепер введіть ваш вік (в роках):"
    )
    await state.set_state(UserProfile.waiting_for_age)

@dp.message(UserProfile.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    """Обробка віку"""
    try:
        age = int(message.text)
        if age < 10 or age > 120:
            await message.answer("Будь ласка, введіть коректний вік (10-120 років)")
            return
        
        await state.update_data(age=age)
        await message.answer(f"Вік: {age} років ✅\n\nТепер введіть ваш зріст (в см):")
        await state.set_state(UserProfile.waiting_for_height)
        
    except ValueError:
        await message.answer("Будь ласка, введіть вік числом")

@dp.message(UserProfile.waiting_for_height)
async def process_height(message: Message, state: FSMContext):
    """Обробка зросту"""
    try:
        height = int(message.text)
        if height < 100 or height > 250:
            await message.answer("Будь ласка, введіть коректний зріст (100-250 см)")
            return
        
        await state.update_data(height=height)
        await message.answer(f"Зріст: {height} см ✅\n\nТепер введіть вашу вагу (в кг):")
        await state.set_state(UserProfile.waiting_for_weight)
        
    except ValueError:
        await message.answer("Будь ласка, введіть зріст числом")

@dp.message(UserProfile.waiting_for_weight)
async def process_weight(message: Message, state: FSMContext):
    """Обробка ваги"""
    try:
        weight = float(message.text)
        if weight < 30 or weight > 300:
            await message.answer("Будь ласка, введіть коректну вагу (30-300 кг)")
            return
        
        await state.update_data(weight=weight)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛋️ Мінімальна активність", callback_data="activity_minimal")],
            [InlineKeyboardButton(text="🚶 Легка активність", callback_data="activity_light")],
            [InlineKeyboardButton(text="🏃 Помірна активність", callback_data="activity_moderate")],
            [InlineKeyboardButton(text="💪 Активний спосіб життя", callback_data="activity_active")],
            [InlineKeyboardButton(text="🏋️ Дуже активний", callback_data="activity_very_active")]
        ])
        
        await message.answer(
            f"Вага: {weight} кг ✅\n\n"
            "Оберіть ваш рівень активності:",
            reply_markup=keyboard
        )
        await state.set_state(UserProfile.waiting_for_activity)
        
    except ValueError:
        await message.answer("Будь ласка, введіть вагу числом")

@dp.callback_query(F.data.startswith("activity_"))
async def process_activity(callback: CallbackQuery, state: FSMContext):
    """Обробка рівня активності"""
    activity_map = {
        "activity_minimal": "мінімальна",
        "activity_light": "легка",
        "activity_moderate": "помірна",
        "activity_active": "активна",
        "activity_very_active": "дуже активна"
    }
    
    activity = activity_map[callback.data]
    await state.update_data(activity=activity)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬇️ Схуднути", callback_data="goal_lose")],
        [InlineKeyboardButton(text="➡️ Підтримувати вагу", callback_data="goal_maintain")],
        [InlineKeyboardButton(text="⬆️ Набрати вагу", callback_data="goal_gain")]
    ])
    
    await callback.message.edit_text(
        f"Рівень активності: {activity} ✅\n\n"
        "Яка ваша мета?",
        reply_markup=keyboard
    )
    await state.set_state(UserProfile.waiting_for_goal)

@dp.callback_query(F.data.startswith("goal_"))
async def process_goal(callback: CallbackQuery, state: FSMContext):
    """Завершення створення профілю"""
    goal_map = {
        "goal_lose": "схуднути",
        "goal_maintain": "підтримувати вагу",
        "goal_gain": "набрати вагу"
    }
    
    goal = goal_map[callback.data]
    await state.update_data(goal=goal)
    
    # Отримуємо всі дані
    data = await state.get_data()
    user_id = str(callback.from_user.id)
    
    # Розраховуємо калорії
    bmr = calculate_bmr(data['gender'], data['age'], data['height'], data['weight'])
    daily_calories = calculate_daily_calories(bmr, data['activity'])
    target_calories = adjust_calories_for_goal(daily_calories, goal)
    
    # Зберігаємо профіль користувача
    users_db[user_id] = {
        **data,
        'bmr': bmr,
        'daily_calories': daily_calories,
        'target_calories': target_calories,
        'created_at': datetime.now().isoformat()
    }
    save_users()
    
    # Показуємо результат
    result_text = f"""
✅ Профіль створено успішно!

👤 Ваші дані:
• Стать: {data['gender']}
• Вік: {data['age']} років
• Зріст: {data['height']} см
• Вага: {data['weight']} кг
• Активність: {data['activity']}
• Мета: {goal}

📊 Ваші калорії:
• Базовий метаболізм: {bmr} ккал/день
• Денна норма: {daily_calories} ккал/день
• Рекомендовано для мети: {target_calories} ккал/день

💡 Рекомендації:
• Пийте достатньо води (30-35 мл на кг ваги)
• Їжте 4-5 разів на день невеликими порціями
• Включайте білки в кожен прийом їжі
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍎 Розрахувати калорії продукту", callback_data="calculate_food")],
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(result_text, reply_markup=keyboard)
    await state.clear()

@dp.callback_query(F.data == "calculate_food")
async def calculate_food_start(callback: CallbackQuery, state: FSMContext):
    """Початок розрахування калорій продукту"""
    # Створюємо список продуктів по категоріях
    categories = {
        "🍎 Фрукти": ["яблуко", "банан", "апельсин", "груша", "виноград"],
        "🥕 Овочі": ["помідор", "огірок", "морква", "капуста", "картопля"],
        "🍖 М'ясо": ["куриця", "яловичина", "свинина", "індичка"],
        "🐟 Риба": ["лосось", "тунець", "скумбрія", "треска"],
        "🥛 Молочні": ["молоко", "сир", "йогурт", "творог", "кефір"],
        "🌾 Крупи": ["рис", "гречка", "вівсянка", "киноа"],
        "🍿 Снеки": ["чіпси картопляні", "попкорн", "крекери", "горішки солоні"],
        "🍺 Алкоголь": ["пиво світле", "вино червоне", "горілка", "коньяк"]
    }
    
    food_list = ""
    for category, foods in categories.items():
        food_list += f"\n{category}:\n"
        food_list += "\n".join([f"• {food}" for food in foods])
        food_list += "\n"
    
    # Фото з різними продуктами
    food_photo = "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=800&h=600&fit=crop"
    
    # Видаляємо попереднє повідомлення та відправляємо нове з фото
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=food_photo,
        caption=f"🍎 Розрахунок калорій продукту\n\n"
                f"У базі є {len(food_db)} продуктів! Ось деякі з них:\n"
                f"{food_list}\n"
                f"...та багато інших! 🥜🍯🍄\n\n"
                f"Просто введіть назву продукту:"
    )
    await state.set_state(FoodCalories.waiting_for_food)

@dp.message(FoodCalories.waiting_for_food)
async def process_food_name(message: Message, state: FSMContext):
    """Обробка назви продукту"""
    food_name = message.text.lower().strip()
    
    # Прямий пошук
    if food_name in food_db:
        await state.update_data(food_name=food_name, calories_per_100g=food_db[food_name])
        await message.answer(
            f"Продукт: {food_name} ✅\n"
            f"Калорійність: {food_db[food_name]} ккал на 100г\n\n"
            f"Тепер введіть вагу продукту в грамах:"
        )
        await state.set_state(FoodCalories.waiting_for_weight_food)
        return
    
    # Розумний пошук - знаходимо схожі продукти
    similar_foods = []
    
    # Шукаємо точні збіги в частині назви
    for food in food_db.keys():
        if food_name in food or food in food_name:
            similar_foods.append(food)
    
    # Якщо не знайшли, шукаємо по словах
    if not similar_foods:
        food_words = food_name.split()
        for food in food_db.keys():
            for word in food_words:
                if word in food and len(word) > 2:
                    similar_foods.append(food)
    
    # Синоніми для популярних продуктів
    synonyms = {
        "курка": "куриця",
        "курятина": "куриця", 
        "говядина": "яловичина",
        "телятина": "телятина",
        "свиняче": "свинина",
        "рибка": "риба",
        "молочко": "молоко",
        "сирок": "сир",
        "яєчко": "яйце",
        "яблучко": "яблуко",
        "картошка": "картопля",
        "помідорка": "помідор",
        "огірочок": "огірок",
        "морквинка": "морква",
        "капустка": "капуста",
        "грибочки": "гриби білі",
        "печериці": "шампіньйони",
        # Алкогольні синоніми
        "пивко": "пиво світле",
        "винце": "вино червоне",
        "винишко": "вино червоне",
        "шампанське": "шампанське",
        "бренді": "коньяк",
        "самогонка": "самогон",
        # Снеки синоніми
        "чіпсі": "чіпси картопляні",
        "чипси": "чіпси картопляні",
        "попкон": "попкорн",
        "сухарі": "сухарики",
        "піца": "піцца",
        "картопля-фрі": "картопля фрі",
        "фастфуд": "бургер",
        "макдак": "бургер",
        "хотдог": "хот-дог"
    }
    
    # Перевіряємо синоніми
    if food_name in synonyms:
        synonym_product = synonyms[food_name]
        if synonym_product in food_db:
            await state.update_data(food_name=synonym_product, calories_per_100g=food_db[synonym_product])
            await message.answer(
                f"Знайшов! 🎯\n"
                f"Продукт: {synonym_product} ✅\n"
                f"Калорійність: {food_db[synonym_product]} ккал на 100г\n\n"
                f"Тепер введіть вагу продукту в грамах:"
            )
            await state.set_state(FoodCalories.waiting_for_weight_food)
            return
    
    # Показуємо схожі продукти
    if similar_foods:
        # Видаляємо дублікати та обмежуємо кількість
        similar_foods = list(set(similar_foods))[:8]
        suggestions = "\n".join([f"• {food} ({food_db[food]} ккал)" for food in similar_foods])
        
        await message.answer(
            f"Продукт '{food_name}' не знайдено 😔\n\n"
            f"🔍 Можливо, ви мали на увазі:\n{suggestions}\n\n"
            f"Спробуйте ще раз або введіть точну назву:"
        )
    else:
        # Показуємо популярні продукти
        popular_foods = ["яблуко", "банан", "куриця", "рис", "молоко", "яйце", "хліб", "картопля"]
        popular_list = "\n".join([f"• {food} ({food_db[food]} ккал)" for food in popular_foods])
        
        await message.answer(
            f"Продукт '{food_name}' не знайдено 😔\n\n"
            f"💡 Популярні продукти:\n{popular_list}\n\n"
            f"У базі є {len(food_db)} продуктів! Спробуйте інший або введіть /start"
        )

@dp.message(FoodCalories.waiting_for_weight_food)
async def process_food_weight(message: Message, state: FSMContext):
    """Обробка ваги продукту"""
    try:
        weight = float(message.text)
        if weight <= 0:
            await message.answer("Будь ласка, введіть позитивне число")
            return
        
        data = await state.get_data()
        food_name = data['food_name']
        calories_per_100g = data['calories_per_100g']
        
        total_calories = round((calories_per_100g * weight) / 100, 1)
        
        result_text = f"""
🍎 Результат розрахунку:

📦 Продукт: {food_name}
⚖️ Вага: {weight}г
🔥 Калорії: {total_calories} ккал

📊 Деталі:
• Калорійність на 100г: {calories_per_100g} ккал
• Ваша порція: {weight}г
• Загальна калорійність: {total_calories} ккал
        """
        
        # Додаємо інформацію про % від денної норми, якщо є профіль
        user_id = str(message.from_user.id)
        if user_id in users_db:
            target_calories = users_db[user_id]['target_calories']
            percentage = round((total_calories / target_calories) * 100, 1)
            result_text += f"\n💡 Це {percentage}% від вашої денної норми ({target_calories} ккал)"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍎 Розрахувати інший продукт", callback_data="calculate_food")],
            [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
        ])
        
        # Вибираємо картинку залежно від типу продукту
        product_photos = {
            # Фрукти
            "яблуко": "https://images.unsplash.com/photo-1567306226416-28f0efdc88ce?w=400&h=400&fit=crop",
            "банан": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&h=400&fit=crop",
            # М'ясо
            "куриця": "https://images.unsplash.com/photo-1587593810167-148ebbc35e5e?w=400&h=400&fit=crop",
            "яловичина": "https://images.unsplash.com/photo-1558030137-b7a7b4b3d724?w=400&h=400&fit=crop",
            # Молочні
            "молоко": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&h=400&fit=crop",
            "сир": "https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=400&h=400&fit=crop",
            # Снеки
            "піцца": "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=400&fit=crop",
            "бургер": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=400&fit=crop",
            # Алкоголь
            "пиво світле": "https://images.unsplash.com/photo-1608270586620-248524c67de9?w=400&h=400&fit=crop",
            "вино червоне": "https://images.unsplash.com/photo-1547595628-c61a29f496f0?w=400&h=400&fit=crop"
        }
        
        # Загальна картинка для всіх продуктів
        default_photo = "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=400&h=400&fit=crop"
        
        # Вибираємо фото для конкретного продукту або загальне
        photo_url = product_photos.get(food_name, default_photo)
        
        await message.answer_photo(
            photo=photo_url,
            caption=result_text,
            reply_markup=keyboard
        )
        await state.clear()
        
    except ValueError:
        await message.answer("Будь ласка, введіть вагу числом (наприклад: 150)")

@dp.callback_query(F.data == "my_profile")
async def show_profile(callback: CallbackQuery):
    """Показ профілю користувача"""
    user_id = str(callback.from_user.id)
    
    if user_id not in users_db:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Створити профіль", callback_data="create_profile")]
        ])
        await callback.message.edit_text(
            "У вас ще немає профілю 😔\n\n"
            "Створіть профіль для отримання персональних рекомендацій!",
            reply_markup=keyboard
        )
        return
    
    user = users_db[user_id]
    profile_text = f"""
👤 Ваш профіль:

📋 Основні дані:
• Стать: {user['gender']}
• Вік: {user['age']} років
• Зріст: {user['height']} см
• Вага: {user['weight']} кг
• Активність: {user['activity']}
• Мета: {user['goal']}

📊 Калорії:
• Базовий метаболізм: {user['bmr']} ккал/день
• Денна норма: {user['daily_calories']} ккал/день
• Рекомендовано: {user['target_calories']} ккал/день

💡 Корисні поради:
• Білки: {round(user['target_calories'] * 0.3 / 4)}г на день
• Жири: {round(user['target_calories'] * 0.25 / 9)}г на день
• Вуглеводи: {round(user['target_calories'] * 0.45 / 4)}г на день
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Оновити профіль", callback_data="create_profile")],
        [InlineKeyboardButton(text="🍎 Розрахувати калорії", callback_data="calculate_food")],
        [InlineKeyboardButton(text="💧 Норма води", callback_data="water_intake"), InlineKeyboardButton(text="⚖️ ІМТ", callback_data="calculate_bmi")]
    ])
    
    # Вибираємо картинку профілю залежно від статі та мети
    profile_image = "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=600&fit=crop"  # fitness profile
    if user['gender'] == 'жінка':
        profile_image = "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=600&fit=crop"  # female fitness
    else:
        profile_image = "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&h=600&fit=crop"  # male fitness
    
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=profile_image,
        caption=profile_text,
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Показ довідки"""
    help_text = """
ℹ️ Довідка по боту

🤖 Що я вмію:
• 📊 Розраховувати базовий метаболізм (BMR)
• 🔥 Визначати денну норму калорій
• 🍎 Розраховувати калорійність 250+ продуктів
• 💧 Розраховувати норму води щодня
• ⚖️ Визначати індекс маси тіла (ІМТ)
• 💡 Давати щоденні поради для здоров'я
• 📈 Зберігати персональний профіль
• 🎯 Персональні рекомендації залежно від мети

📊 Формули розрахунку:
• BMR (чоловіки): 88.362 + (13.397 × вага) + (4.799 × зріст) - (5.677 × вік)
• BMR (жінки): 447.593 + (9.247 × вага) + (3.098 × зріст) - (4.330 × вік)
• ІМТ: вага(кг) / зріст(м)²
• Норма води: 35 мл × вага × коефіцієнт активності

🎯 Коригування для мети:
• Схуднути: -500 ккал від норми
• Підтримувати: норма калорій
• Набрати вагу: +500 ккал до норми

📱 Команди:
/start - головне меню

🌟 Версія: 2.0 з розширеними функціями
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])
    
    # Картинка для довідки
    help_image = "https://images.unsplash.com/photo-1551963831-b3b1ca40c98e?w=800&h=600&fit=crop"  # brain/knowledge
    
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=help_image,
        caption=help_text,
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    """Повернення до головного меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Створити профіль", callback_data="create_profile")],
        [InlineKeyboardButton(text="🍎 Розрахувати калорії продукту", callback_data="calculate_food")],
        [InlineKeyboardButton(text="📈 Мій профіль", callback_data="my_profile")],
        [InlineKeyboardButton(text="💧 Норма води", callback_data="water_intake")],
        [InlineKeyboardButton(text="⚖️ Розрахунок ІМТ", callback_data="calculate_bmi")],
        [InlineKeyboardButton(text="💡 Щоденні поради", callback_data="daily_tips")],
        [InlineKeyboardButton(text="ℹ️ Допомога", callback_data="help")]
    ])
    
    # Картинка для головного меню
    menu_image = "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=800&h=600&fit=crop"  # healthy food spread
    
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=menu_image,
        caption=f"Головне меню 🏠\n\n"
        "Оберіть, що ви хочете зробити:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "water_intake")
async def water_intake(callback: CallbackQuery):
    """Розрахунок норми води"""
    user_id = str(callback.from_user.id)
    
    if user_id not in users_db:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Створити профіль", callback_data="create_profile")],
            [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
        ])
        await callback.message.edit_text(
            "💧 Для розрахунку норми води потрібен профіль!\n\n"
            "Створіть профіль для персональних рекомендацій:",
            reply_markup=keyboard
        )
        return
    
    user = users_db[user_id]
    water_ml = calculate_water_intake(user['weight'], user['activity'])
    water_glasses = round(water_ml / 250)  # стандартна склянка 250мл
    
    water_text = f"""
💧 Ваша норма води:

📊 Розрахунок:
• Вага: {user['weight']} кг
• Активність: {user['activity']}
• Базова норма: 35 мл/кг

💦 Рекомендації:
• {water_ml} мл на день
• Це приблизно {water_glasses} склянок по 250мл
• Пийте рівномірно протягом дня

💡 Корисні поради:
• Почніть день зі склянки води
• Пийте воду за 30 хв до їжі
• Більше води при тренуваннях
• Слідкуйте за кольором сечі (має бути світло-жовтою)
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚖️ Розрахунок ІМТ", callback_data="calculate_bmi")],
        [InlineKeyboardButton(text="💡 Щоденні поради", callback_data="daily_tips")],
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])
    
    water_image = "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=800&h=600&fit=crop"
    
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=water_image,
        caption=water_text,
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "calculate_bmi")
async def calculate_bmi_handler(callback: CallbackQuery):
    """Розрахунок ІМТ"""
    user_id = str(callback.from_user.id)
    
    if user_id not in users_db:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Створити профіль", callback_data="create_profile")],
            [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
        ])
        await callback.message.edit_text(
            "⚖️ Для розрахунку ІМТ потрібен профіль!\n\n"
            "Створіть профіль для персональних рекомендацій:",
            reply_markup=keyboard
        )
        return
    
    user = users_db[user_id]
    bmi = calculate_bmi(user['weight'], user['height'])
    category, emoji = get_bmi_category(bmi)
    
    # Рекомендації залежно від ІМТ
    recommendations = {
        "недостатня вага": "Рекомендуємо збільшити калорійність раціону та включити силові тренування",
        "нормальна вага": "Чудово! Підтримуйте поточний спосіб життя",
        "надлишкова вага": "Рекомендуємо помірне зниження калорійності та збільшення активності",
        "ожиріння": "Рекомендуємо звернутися до лікаря та скласти план зниження ваги"
    }
    
    bmi_text = f"""
⚖️ Ваш індекс маси тіла (ІМТ):

📊 Розрахунок:
• Зріст: {user['height']} см
• Вага: {user['weight']} кг
• ІМТ: {bmi}

{emoji} Категорія: {category}

💡 Рекомендації:
{recommendations[category]}

📈 Шкала ІМТ:
🔵 < 18.5 - недостатня вага
🟢 18.5-24.9 - нормальна вага
🟡 25.0-29.9 - надлишкова вага
🔴 ≥ 30.0 - ожиріння
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💧 Норма води", callback_data="water_intake")],
        [InlineKeyboardButton(text="💡 Щоденні поради", callback_data="daily_tips")],
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])
    
    bmi_image = "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=600&fit=crop"
    
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=bmi_image,
        caption=bmi_text,
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "daily_tips")
async def daily_tips(callback: CallbackQuery):
    """Щоденні поради"""
    import random
    
    tips = [
        "🥗 Їжте 5 порцій овочів та фруктів на день",
        "🚶 Робіть мінімум 10,000 кроків щодня",
        "💤 Спіть 7-9 годин для відновлення організму",
        "🥛 Пийте воду одразу після пробудження",
        "🍽️ Їжте повільно та ретельно пережовуйте",
        "🧘 Практикуйте медитацію 10 хвилин щодня",
        "🏃 Додайте кардіо-тренування 3 рази на тиждень",
        "💪 Силові тренування 2-3 рази на тиждень",
        "🥜 Включайте здорові жири: горіхи, авокадо, олії",
        "🐟 Їжте рибу 2-3 рази на тиждень",
        "🚫 Уникайте цукру та обробленої їжі",
        "📱 Зробіть перерву від телефону під час їжі",
        "🌅 Отримуйте ранкове сонячне світло",
        "🍃 Додавайте зелень у кожен прийом їжі",
        "⏰ Дотримуйтесь режиму харчування",
        "🧊 П'ите холодну воду для прискорення метаболізму",
        "🥵 Додавайте гострі спеції для підвищення термогенезу",
        "🛑 Не їжте за 3 години до сну",
        "📊 Ведіть щоденник харчування",
        "🎯 Ставте реалістичні цілі щотижня"
    ]
    
    # Вибираємо 5 випадкових порад
    daily_tips_list = random.sample(tips, 5)
    tips_text = "\n".join([f"{i+1}. {tip}" for i, tip in enumerate(daily_tips_list)])
    
    user_id = str(callback.from_user.id)
    personalized_tip = ""
    
    if user_id in users_db:
        user = users_db[user_id]
        if user['goal'] == 'схуднути':
            personalized_tip = "\n💡 Персональна порада: Створіть дефіцит калорій 300-500 ккал/день для здорового схуднення."
        elif user['goal'] == 'набрати вагу':
            personalized_tip = "\n💡 Персональна порада: Збільште калорійність на 300-500 ккал/день та додайте силові тренування."
        else:
            personalized_tip = "\n💡 Персональна порада: Підтримуйте баланс калорій та регулярну активність."
    
    tips_full_text = f"""
💡 Щоденні поради для здоров'я:

{tips_text}
{personalized_tip}

🌟 Пам'ятайте: маленькі кроки ведуть до великих змін!
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Нові поради", callback_data="daily_tips")],
        [InlineKeyboardButton(text="💧 Норма води", callback_data="water_intake")],
        [InlineKeyboardButton(text="⚖️ Розрахунок ІМТ", callback_data="calculate_bmi")],
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])
    
    tips_image = "https://images.unsplash.com/photo-1506629905107-bb5842dcbc67?w=800&h=600&fit=crop"
    
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=tips_image,
        caption=tips_full_text,
        reply_markup=keyboard
    )

# Обробники кнопок мають бути ПЕРЕД обробниками FSM
@dp.message(F.text == "🏠 Головне меню")
async def main_menu_button(message: Message, state: FSMContext = None):
    await main_menu(message)

@dp.message(F.text == "📊 Мій профіль")
async def profile_button(message: Message):
    await show_profile(message)

@dp.message(F.text == "🍎 Калорії")
async def calories_button(message: Message, state: FSMContext):
    await message.answer("🍎 Введіть назву продукту для розрахунку калорій:")
    await state.set_state(FoodCalories.waiting_for_product)

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

# ...existing code...