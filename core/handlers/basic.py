import logging
from asyncio import Lock
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from core.db.users_crud import get_user_by_telegram_id, create_user
# from core.db.models import add_application, add_payment, get_application, increment_attempts
from core.keyboards.inline import admin_confirm_payment_keyboard, admin_confirm_photo_keyboard, call_operator_button, confirm_payment_button, start_inline_keyboard
from core.utils.menu_utils import update_or_send_message

# Создаём глобальный словарь для блокировки по пользователю
locks = {}

# Команда /start
async def cmd_start(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        create_user(
            name=message.from_user.full_name,
            telegram_id=message.from_user.id,
            contact_info=message.from_user.username
        )
    await update_or_send_message(
        message=message,
        text="Добро пожаловать! Выберите опцию ниже:",
        reply_markup=start_inline_keyboard())
