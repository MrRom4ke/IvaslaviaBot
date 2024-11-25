from aiogram import Bot
from aiogram.types import CallbackQuery

from IvaslaviaBot.core.db.users_crud import get_user_by_telegram_id, create_user
from IvaslaviaBot.core.keyboards.inline import start_inline_keyboard


# Хендлер для обработки колбэка "back_to_user_menu"
async def back_to_user_menu(callback_query: CallbackQuery, bot: Bot):
    """Возвращает пользователя в главное меню (аналог команды /start)."""
    user = get_user_by_telegram_id(callback_query.from_user.id)
    if not user:
        create_user(
            name=callback_query.from_user.full_name,
            telegram_id=callback_query.from_user.id,
            contact_info=callback_query.from_user.username
        )
    kb = start_inline_keyboard()

    # Удаляем предыдущее сообщение и отправляем новое
    await callback_query.message.delete()
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text="Добро пожаловать! Выберите опцию ниже:",
        reply_markup=kb
    )
    await callback_query.answer()
