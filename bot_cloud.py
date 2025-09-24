import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import json
import os
from datetime import datetime

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Токен бота (отримайте від @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8458486366:AAH4DnunseoCOdyyRS7fueLKeW4ELSZc3QA")

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

# База даних користувачів (в реальному проекті краще використовувати БД)
users_db = {}

# База даних продуктів (калорії на 100г) - Розширена база
food_db = {
    # 🍎 Фрукти та ягоди
    "яблуко": 52, "банан": 89, "апельсин": 47, "мандарин": 53, "лимон": 29,
    "грейпфрут": 35, "груша": 57, "персик": 39, "абрикос": 48, "слива": 46,
    "вишня": 52, "черешня": 63, "виноград": 65, "полуниця": 32, "малина": 46,
    "чорниця": 57, "смородина": 44, "ківі": 61, "ананас": 50, "манго": 60,
    
    # 🥕 Овочі
    "помідор": 18, "огірок": 16, "морква": 41, "цибуля": 40, "картопля": 77,
    "капуста": 25, "буряк": 43, "кабачок": 24, "баклажан": 24, "перець": 27,
    "перець болгарський": 27, "перець гострий": 40, "салат": 14, "шпинат": 23,
    "броколі": 34, "цвітна капуста": 25, "кукурудза": 96, "горошок": 81,
    "квасоля": 93, "редиска": 19, "редька": 36, "часник": 149, "імбир": 80,
    
    # 🌾 Крупи та каші
    "рис": 130, "гречка": 343, "вівсянка": 389, "пшоно": 348, "перловка": 320,
    "манка": 328, "кукурудзяна каша": 337, "ячмінь": 288, "киноа": 368,
    
    # 🍞 Хлібобулочні вироби
    "хліб": 265, "хліб чорний": 214, "хліб білий": 265, "батон": 260,
    "лаваш": 236, "тости": 290, "сухарики": 331, "печиво": 417, "пряники": 364,
    
    # 🍝 Макаронні вироби
    "макарони": 371, "спагеті": 371, "лапша": 322, "вермішель": 371,
    
    # 🥛 Молочні продукти
    "молоко": 60, "кефір": 56, "ряжанка": 85, "сметана": 206, "йогурт": 59,
    "творог": 101, "сир": 402, "сир російський": 364, "сир голландський": 377,
    "масло вершкове": 717, "вершки": 118,
    
    # 🥚 Яйця
    "яйце": 155, "яйце курече": 155, "яйце перепелине": 168,
    "яєчний білок": 52, "яєчний жовток": 322,
    
    # 🍖 М'ясо
    "яловичина": 187, "свинина": 259, "баранина": 203, "телятина": 97,
    "куриця": 165, "індичка": 104, "качка": 405, "гусак": 412, "кролик": 156,
    "печінка": 135, "серце": 87, "нирки": 66, "ковбаса": 301, "сосиски": 266,
    "шинка": 270, "бекон": 541,
    
    # 🐟 Риба та морепродукти
    "риба": 206, "лосось": 208, "тунець": 296, "скумбрія": 305, "селедка": 262,
    "щука": 84, "судак": 84, "короп": 112, "минтай": 72, "хек": 86,
    "треска": 78, "камбала": 83, "креветки": 95, "краби": 96, "кальмари": 110,
    "мідії": 77, "ікра": 263,
    
    # 🥜 Горіхи та насіння
    "волоські горіхи": 654, "мигдаль": 575, "фундук": 628, "арахіс": 567,
    "кедрові горіхи": 673, "кешью": 553, "фісташки": 556,
    "насіння соняшника": 578, "насіння гарбуза": 559, "кунжут": 565,
    
    # 🫘 Бобові
    "горох": 298, "квасоля біла": 102, "квасоля червона": 93,
    "сочевиця": 295, "нут": 364, "соя": 381,
    
    # 🍯 Солодощі
    "цукор": 387, "мед": 329, "варення": 263, "джем": 263, "шоколад": 546,
    "шоколад молочний": 534, "шоколад чорний": 539, "цукерки": 453,
    "мармелад": 321, "зефір": 326, "халва": 516,
    
    # 🧂 Олії та жири
    "олія соняшникова": 899, "олія оливкова": 884, "маргарин": 719, "сало": 797,
    
    # 🥤 Напої безалкогольні
    "чай": 0, "кава": 2, "сік яблучний": 46, "сік апельсиновий": 36,
    "сік томатний": 21, "компот": 85, "морс": 41, "квас": 27,
    "кола": 42, "пепсі": 41, "спрайт": 37, "енергетик": 45, "вода": 0,
    
    # 🍺 Алкогольні напої
    "пиво світле": 43, "пиво темне": 48, "вино червоне": 68, "вино біле": 66,
    "шампанське": 88, "горілка": 235, "коньяк": 239, "віскі": 250, "ром": 220,
    "джин": 263, "текіла": 231, "лікер": 327, "мартіні": 140, "глінтвейн": 132,
    
    # 🍿 Снеки та закуски
    "чіпси картопляні": 536, "чіпси кукурудзяні": 498, "попкорн": 387,
    "крекери": 440, "сухарики": 331, "брецелі": 380, "горішки солоні": 607,
    "піцца": 266, "бургер": 295, "хот-дог": 290, "картопля фрі": 365,
    "пончики": 452, "вафлі": 305, "тістечка": 544, "начос": 346,
    
    # 🧀 Делікатеси
    "моцарела": 280, "пармезан": 431, "фета": 264, "салямі": 407,
    "прошутто": 335, "оливки": 166, "маслини": 361, "ікра червона": 263,
    
    # 🌿 Зелень та спеції
    "петрушка": 36, "кріп": 38, "зелена цибуля": 19, "базилік": 27,
    
    # 🍄 Гриби
    "гриби білі": 22, "шампіньйони": 27, "лисички": 38, "опеньки": 17
}

def load_users():
    """Завантаження користувачів з файлу"""
    global users_db
    if os.path.exists('users.json'):
        try:
            with open('users.json', 'r', encoding='utf-8') as f:
                users_db = json.load(f)
        except:
            users_db = {}

def save_users():
    """Збереження користувачів у файл"""
    try:
        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump(users_db, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving users: {e}")

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

@dp.message(CommandStart())
async def start_handler(message: Message):
    """Обробник команди /start"""
    user_id = str(message.from_user.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Створити профіль", callback_data="create_profile")],
        [InlineKeyboardButton(text="🍎 Розрахувати калорії продукту", callback_data="calculate_food")],
        [InlineKeyboardButton(text="📈 Мій профіль", callback_data="my_profile")],
        [InlineKeyboardButton(text="ℹ️ Допомога", callback_data="help")]
    ])
    
    await message.answer(
        f"Привіт, {message.from_user.first_name}! 👋\n\n"
        "Я бот для розрахування калорій та підтримки дієти! 🥗\n\n"
        "Що ти хочеш зробити?",
        reply_markup=keyboard
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
        "🍿 Снеки": ["чіпси картопляні", "попкорн", "крекери", "піцца"],
        "🍺 Алкоголь": ["пиво світле", "вино червоне", "горілка", "коньяк"]
    }
    
    food_list = ""
    for category, foods in categories.items():
        food_list += f"\n{category}:\n"
        food_list += "\n".join([f"• {food}" for food in foods])
        food_list += "\n"
    
    await callback.message.edit_text(
        f"🍎 Розрахунок калорій продукту\n\n"
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
    
    if food_name in food_db:
        await state.update_data(food_name=food_name, calories_per_100g=food_db[food_name])
        await message.answer(
            f"Продукт: {food_name} ✅\n"
            f"Калорійність: {food_db[food_name]} ккал на 100г\n\n"
            f"Тепер введіть вагу продукту в грамах:"
        )
        await state.set_state(FoodCalories.waiting_for_weight_food)
    else:
        similar_foods = [food for food in food_db.keys() if food_name in food or food in food_name]
        if similar_foods:
            suggestions = "\n".join([f"• {food}" for food in similar_foods[:5]])
            await message.answer(
                f"Продукт '{food_name}' не знайдено 😔\n\n"
                f"Можливо, ви мали на увазі:\n{suggestions}\n\n"
                f"Спробуйте ще раз:"
            )
        else:
            await message.answer(
                f"Продукт '{food_name}' не знайдено 😔\n\n"
                f"Спробуйте інший продукт або введіть /start для повернення в меню"
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
🍎 Результат розрахування:

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
        
        await message.answer(result_text, reply_markup=keyboard)
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
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(profile_text, reply_markup=keyboard)

@dp.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Показ довідки"""
    help_text = """
ℹ️ Довідка по боту

🤖 Що я вмію:
• Розраховувати базовий метаболізм (BMR)
• Визначати денну норму калорій
• Враховувати рівень активності та мету
• Розраховувати калорійність продуктів
• Зберігати ваш профіль
• Давати персональні рекомендації

📊 Формули розрахунку:
• BMR (чоловіки): 88.362 + (13.397 × вага) + (4.799 × зріст) - (5.677 × вік)
• BMR (жінки): 447.593 + (9.247 × вага) + (3.098 × зріст) - (4.330 × вік)

🎯 Коригування для мети:
• Схуднути: -500 ккал від норми
• Підтримувати: норма калорій
• Набрати вагу: +500 ккал до норми

📱 Команди:
/start - головне меню

🌟 Бот працює 24/7 в хмарі!
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(help_text, reply_markup=keyboard)

@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    """Повернення до головного меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Створити профіль", callback_data="create_profile")],
        [InlineKeyboardButton(text="🍎 Розрахувати калорії продукту", callback_data="calculate_food")],
        [InlineKeyboardButton(text="📈 Мій профіль", callback_data="my_profile")],
        [InlineKeyboardButton(text="ℹ️ Допомога", callback_data="help")]
    ])
    
    await callback.message.edit_text(
        f"Головне меню 🏠\n\n"
        "Оберіть, що ви хочете зробити:",
        reply_markup=keyboard
    )

async def main():
    """Головна функція запуску бота"""
    load_users()
    print("Бот запущено! 🚀")
    print("Працює в хмарі 24/7 ☁️")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())