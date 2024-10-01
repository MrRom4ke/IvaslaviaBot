import asyncio
import logging
import os
import database

from aiogram import Bot, Dispatcher
from aiogram import F
from aiogram.filters import Command

from core.config import ADMIN_ID, TOKEN
from core.handlers.basic import cmd_second, cmd_start, handle_payment_confirmation, handle_screen
from core.handlers.callback import admin_callback, call_operator_callback, confirm_payment_callback, inline_handler
from core.utils.commands import set_commands
from core.utils.stateform import ApplicationForm

# Настройка логирования
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - [%(levelname)s] - %(name)s - "
                           "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Создание директории для изображений
os.makedirs('IvaslaviaBot/images', exist_ok=True)

# Инициализация БД
database.init_db()

# Уведомление администратора при старте и остановке бота
async def on_startup():
    await set_commands(bot)  # Устанавливаем список команд
    await bot.send_message(ADMIN_ID, "Бот запущен")  # Уведомляем администратора

async def on_shutdown():
    await bot.send_message(ADMIN_ID, "Бот остановлен")
    await bot.session.close()

# Регистрация обработчиков
dp.message.register(cmd_start, Command(commands=['start']))
dp.message.register(cmd_second, Command(commands=['second']))
dp.message.register(handle_screen, ApplicationForm.WAITING_FOR_SCREEN, F.photo)
dp.message.register(handle_screen, F.photo)

dp.callback_query.register(call_operator_callback, lambda c: c.data == 'call_operator')
dp.callback_query.register(confirm_payment_callback, lambda c: c.data == 'confirm_payment')
dp.callback_query.register(inline_handler, lambda c: c.data and c.data in ['participate', 'draw_info', 'participation_conditions'])
dp.callback_query.register(admin_callback, lambda c: c.data and (c.data.startswith("approve_") or c.data.startswith("reject_") or c.data.startswith("payment_confirm_") or c.data.startswith("payment_reject_")))

if __name__ == '__main__':
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        asyncio.run(dp.start_polling(bot, skip_updates=True))
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
