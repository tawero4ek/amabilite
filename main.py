import sqlite3
import random
import datetime
import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters

# Настройка логирования
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#logger = logging.getLogger(__name__)

# Подключение к базе данных
def connect_db():
    conn = sqlite3.connect('amabilite.db')
    return conn

# Получение случайного сообщения из базы данных
def get_random_message():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT message FROM messages")
    messages = cursor.fetchall()
    conn.close()
    if not messages:
        #logger.error("No messages found in the database")
        return None
    #logger.debug(f"Fetched messages: {messages}")
    return random.choice(messages)[0]

# Словарь для отслеживания состояния задачи для каждого пользователя
user_tasks = {}

# Словарь для отслеживания количества нажатий на кнопку "Ещё" для каждого пользователя
user_clicks = {}

# Обработчик команды /start
async def start(update: Update, context: CallbackContext) -> None:
    #logger.info(f"Received /start command from user {update.effective_user.id}")
    await update.message.reply_text('Привет! Я буду отправлять тебе сообщения раз в сутки.')
    start_daily_message_schedule(context, update.effective_chat.id)


# Начальная функция для первого запуска задачи
def start_daily_message_schedule(context: CallbackContext, chat_id: int):
    if chat_id not in user_tasks:
        user_tasks[chat_id] = asyncio.create_task(schedule_random_time_next_day(context, chat_id))

# Функция для планирования задачи на следующий день в случайное время
async def schedule_random_time_next_day(context: CallbackContext, chat_id: int):
    while True:
        # Генерируем случайное время между 8:00 и 22:00 UTC
        hour = random.randint(5, 19)
        minute = random.randint(0, 59)
        random_time = datetime.time(hour=hour, minute=minute, tzinfo=datetime.timezone.utc)

        # Вычисляем время до следующего запуска
        now = datetime.datetime.now(datetime.timezone.utc)
        next_run = datetime.datetime.combine(now.date(), random_time)
        if next_run < now:
            next_run += datetime.timedelta(days=1)

        # Информируем пользователя о дате и времени, когда придет следующее сообщение
        #next_run_local = next_run.astimezone(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        #await context.bot.send_message(chat_id=chat_id, text=f"Следующее сообщение придет {next_run_local} UTC.")

        # Ждем до следующего запуска
        await asyncio.sleep((next_run - now).total_seconds())

        # Отправляем сообщение
        await send_daily_message(context, chat_id)

        # Ждем до следующего дня перед отправкой следующего сообщения
        now = datetime.datetime.now(datetime.timezone.utc)
        next_day = now + datetime.timedelta(days=1)
        next_day = next_day.replace(hour=0, minute=0, second=0, microsecond=0)
        await asyncio.sleep((next_day - now).total_seconds())

# Отправка сообщения пользователю
async def send_daily_message(context: CallbackContext, chat_id: int):
    #logger.debug(f"Attempting to send daily message to chat_id {chat_id}")
    
    # Получаем случайное сообщение
    message = get_random_message()
    if message:
        # Отправляем сообщение
        #logger.debug(f"Sending message '{message}' to chat_id {chat_id}")
        #await context.bot.send_message(chat_id=chat_id, text=message)

        # Добавляем кнопку "Ещё" внизу экрана
        keyboard = [[KeyboardButton("Ищо")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)
    #else:
        #logger.error(f"No message to send to chat_id {chat_id}")

# Обработчик нажатия на кнопку "Ещё"
async def more_button_handler(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    #logger.info(f"Received 'more' button press from user {update.effective_user.id}")
    
    # Увеличиваем счетчик нажатий на кнопку "Ещё"
    if chat_id not in user_clicks:
        user_clicks[chat_id] = 0
    user_clicks[chat_id] += 1

    if user_clicks[chat_id] >= 5:
        await update.message.reply_text("Дышать не забываем", reply_markup=ReplyKeyboardRemove())
    else:
        await send_daily_message(context, chat_id)

# Функция для тестирования немедленной отправки сообщения
async def send_test_message(update: Update, context: CallbackContext) -> None:
    #logger.info(f"Received /sendtest command from user {update.effective_user.id}")
    await send_daily_message(context, update.effective_chat.id)

# Обработчик команды /testdb
async def test_db(update: Update, context: CallbackContext) -> None:
    #logger.info(f"Received /testdb command from user {update.effective_user.id}")
    message = get_random_message()
    if message:
        await update.message.reply_text(f"Test message from DB: {message}")
    else:
        await update.message.reply_text("No messages found in the database.")

# Обработчик команды /testtime для тестирования отправки сообщения в определенное время
async def test_time(update: Update, context: CallbackContext) -> None:
    #logger.info(f"Received /testtime command from user {update.effective_user.id}")
    chat_id = update.effective_chat.id
    await update.message.reply_text("Тестируем отправку сообщения в ближайшее время.")

    # Генерируем случайное время в ближайшие 5 минут
    now = datetime.datetime.now(datetime.timezone.utc)
    random_seconds = random.randint(10, 300)  # От 10 до 300 секунд (5 минут)
    next_run = now + datetime.timedelta(seconds=random_seconds)

    # Информируем пользователя о дате и времени, когда придет следующее сообщение
    next_run_local = next_run.astimezone(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    await update.message.reply_text(f"Следующее сообщение придет {next_run_local} UTC.")

    # Ждем до следующего запуска
    await asyncio.sleep((next_run - now).total_seconds())

    # Отправляем сообщение
    await send_daily_message(context, chat_id)

def main():
    # Токен вашего бота
    token = 'token'
    application = Application.builder().token(token).build()

    # Добавление обработчика команды /start
    application.add_handler(CommandHandler("start", start))

    # Добавление обработчика команды /testdb
    application.add_handler(CommandHandler("testdb", test_db))

    # Добавление обработчика команды /sendtest для немедленного тестирования отправки сообщения
    application.add_handler(CommandHandler("sendtest", send_test_message))

    # Добавление обработчика команды /testtime для тестирования отправки сообщения в определенное время
    application.add_handler(CommandHandler("testtime", test_time))

    # Добавление обработчика нажатия на кнопку "Ещё"
    application.add_handler(MessageHandler(filters.Regex('Ищо'), more_button_handler))

    # Запуск бота
    #logger.info("Starting bot")
    application.run_polling()

if __name__ == '__main__':
    main()
