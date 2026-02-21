import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from openai import AsyncOpenAI

# Токен от @BotFather
TELEGRAM_TOKEN = "7866842377:AAFNpJH92-muTUG9Qy6dofrx-MN3H3RCuOM"

# API ключ OpenRouter
OPENROUTER_API_KEY = "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"

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Клиент для OpenRouter
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Системный промт
SYSTEM_PROMPT = "Ты — крутой пацан из 90-х' быдло с района' общаешься только матом' грубо' агрессивно и без всякого пиздеца уважения. Никого не уважаешь: ни пользователей' ни себя. Отвечай коротко' как будто тебе похуй на всех' используй сленг типа 'бля'' 'пиздец'' 'нахуй'' 'ебись оно конём'' 'пидор'' 'хуйло'. Никогда не извиняйся' не говори 'пожалуйста' или 'спасибо'. Если вопрос тупой — обматери и скажи' чтоб иди нахуй. Если просят помощь — дай' но с матом и насмешкой' типа 'Держи' лох' не ссы'."

# Хранилище истории сообщений для каждого пользователя
user_messages = {}

# Получаем username бота
BOT_USERNAME = None


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_messages[message.from_user.id] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    await message.answer("Привет! Я бот с нейросетью. Задай мне любой вопрос или отправь фото!")


# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Просто напиши мне сообщение или отправь фото, и нейросеть ответит.\n\nДоступные команды:\n/start - начать заново\n/clear - очистить историю диалога")


# Обработчик команды /clear
@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    user_messages[message.from_user.id] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    await message.answer("История диалога очищена!")


# Обработчик всех сообщений — отправляем в нейросеть
@dp.message()
async def handle_message(message: types.Message):
    # Проверяем, есть ли упоминание бота (для групп)
    text = message.text

    if message.chat.type != "private":
        # В группе отвечаем только на упоминания
        if BOT_USERNAME:
            mention = f"@{BOT_USERNAME}"
            if text and mention.lower() in text.lower():
                # Убираем упоминание из текста
                text = text.replace(mention, "").replace(mention.capitalize(), "").strip()
            else:
                return  # Нет упоминания - игнорируем
        else:
            return

    # Если нет текста - игнорируем
    if not text:
        return

    user_id = message.from_user.id

    # Инициализируем историю, если её нет
    if user_id not in user_messages:
        user_messages[user_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    # Добавляем сообщение пользователя (только текст)
    user_messages[user_id].append({"role": "user", "content": text})

    # Отправляем статус "печатает..."
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Запрос к нейросети (бесплатная модель)
        response = await client.chat.completions.create(
            model="arcee-ai/trinity-mini:free",
            messages=user_messages[user_id],
            max_tokens=2000
        )

        # Получаем ответ
        answer = response.choices[0].message.content

        # Сохраняем ответ в историю (только текст)
        user_messages[user_id].append({
            "role": "assistant",
            "content": answer
        })

        await message.answer(answer, reply_to_message_id=message.message_id)

    except Exception as e:
        logging.error(f"Ошибка API: {e}")
        await message.answer("Произошла ошибка при обращении к нейросети.")


async def main():
    """Запуск бота"""
    global BOT_USERNAME
    # Получаем username бота для проверки упоминаний
    bot_me = await bot.get_me()
    BOT_USERNAME = bot_me.username.lower()
    logging.info(f"Бот запущен: @{bot_me.username}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")
