import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram import F
from aiogram.filters import Command

from IvaslaviaBot.core.handlers.application_handlers import handle_screenshot
from IvaslaviaBot.core.handlers.drawing_handlers import view_drawing_info, participate_in_drawing, go_back_to_list, \
    show_drawing_info
from IvaslaviaBot.core.utils.stateform import NewDrawingState, ApplicationForm
from config import ADMIN_ID, TOKEN
from core.handlers.basic import cmd_start
from core.handlers.admin_handlers import cmd_admin, handle_admin_callback, set_drawing_title, set_drawing_description, \
    set_drawing_start_date, set_drawing_end_date, admin_manage_draws, show_active_draws, show_completed_draws, \
    check_screenshots, check_payments
from core.handlers.callback import call_operator_callback, inline_handler
from core.utils.commands import set_commands
from core.db.models import initialize_tables


# Настройка логирования
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - [%(levelname)s] - %(name)s - "
                           "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Создание директории для изображений
os.makedirs('images/application', exist_ok=True)
os.makedirs('images/payment', exist_ok=True)

# Инициализация БД
initialize_tables()

# Уведомление администратора при старте и остановке бота
async def on_startup():
    await set_commands(bot)  # Устанавливаем список команд
    await bot.send_message(ADMIN_ID, "Бот запущен")  # Уведомляем администратора

async def on_shutdown():
    await bot.send_message(ADMIN_ID, "Бот остановлен")
    await bot.session.close()

# Регистрация обработчиков сообщений
dp.message.register(cmd_start, Command(commands=['start']))
dp.message.register(cmd_admin, Command(commands=['admin']))
dp.message.register(set_drawing_title, NewDrawingState.title)
dp.message.register(set_drawing_description, NewDrawingState.description)
dp.message.register(set_drawing_start_date, NewDrawingState.start_date)
dp.message.register(set_drawing_end_date, NewDrawingState.end_date)
dp.message.register(handle_screenshot, ApplicationForm.WAITING_FOR_SCREEN, F.photo)

# dp.message.register(handle_screen, ApplicationForm.WAITING_FOR_SCREEN, F.photo)
# dp.message.register(handle_payment_screen, ApplicationForm.WAITING_FOR_PAYMENT_SCREEN, F.photo)

# Регистрация обработчиков колбэков
dp.callback_query.register(call_operator_callback, lambda c: c.data == 'call_operator')
dp.callback_query.register(inline_handler, lambda c: c.data and c.data in ['participate', 'draw_info', 'participation_conditions'])
dp.callback_query.register(handle_admin_callback, lambda c: c.data in ['start_draw', 'manage_draw', 'end_draw'])
dp.callback_query.register(view_drawing_info, lambda c: c.data.startswith("view_drawing_"))
dp.callback_query.register(participate_in_drawing, lambda c: c.data.startswith("participate_"))
dp.callback_query.register(go_back_to_list, lambda c: c.data == "back_to_list")
dp.callback_query.register(show_active_draws, lambda c: c.data == "active_draws")
dp.callback_query.register(show_completed_draws, lambda c: c.data == "completed_draws")
dp.callback_query.register(show_drawing_info, lambda c: c.data.startswith("manage_drawing_"))
dp.callback_query.register(check_screenshots, lambda c: c.data.startswith("check_screenshots_"))
dp.callback_query.register(check_payments, lambda c: c.data.startswith("check_payments_"))

# dp.callback_query.register(confirm_payment_callback, lambda c: c.data == 'confirm_payment')
# dp.callback_query.register(admin_callback, lambda c: c.data and (c.data.startswith("approve_") or c.data.startswith("reject_") or c.data.startswith("payment_confirm_") or c.data.startswith("payment_reject_")))
# dp.callback_query.register(admin_view_application, lambda c: c.data and c.data.startswith("admin_view_"))
# dp.callback_query.register(admin_approve_application, lambda c: c.data and c.data.startswith("admin_approve_application_"))
# dp.callback_query.register(admin_approve_payment, lambda c: c.data and c.data.startswith("admin_approve_payment_"))


if __name__ == '__main__':
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        asyncio.run(dp.start_polling(bot, skip_updates=True))
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
