from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery


async def back_to_previous_menu(callback_query: CallbackQuery, state: FSMContext):
    """Возвращает пользователя в предыдущее меню."""
    data = await state.get_data()
    previous_menu = data.get("previous_menu")

    if previous_menu == "admin_panel":
        from core.handlers.admin_handlers import show_admin_panel
        await show_admin_panel(callback_query.message, state)
    elif previous_menu == "active_draws":
        from core.handlers.admin_handlers import show_active_draws
        await show_active_draws(callback_query, state)
    elif previous_menu == "start_menu":
        from core.handlers.basic import show_start_menu
        await show_start_menu(callback_query.message, state)
    elif previous_menu == "draws_menu":
        from core.handlers.callback import inline_handler
        await inline_handler(callback_query, state)


    await callback_query.answer()

async def update_or_send_message(message: Message, text: str, reply_markup=None):
    """
    Универсальная функция для обновления существующего сообщения или отправки нового.
    Если редактирование сообщения невозможно, удаляем и отправляем новое.
    """
    try:
        await message.edit_text(text=text, reply_markup=reply_markup)
    except Exception:
        try:
            # Удаляем текущее сообщение
            await message.delete()
        except Exception:
            pass  # Игнорируем ошибки, если сообщение уже удалено
        # Отправляем новое сообщение
        await message.answer(text=text, reply_markup=reply_markup)


async def update_or_send_callback_message(callback_query: CallbackQuery, text: str, reply_markup=None, parse_mode=None):
    """
    Универсальная функция для обновления существующего сообщения, вызванного колбэком,
    или отправки нового сообщения, если обновление невозможно.
    """
    try:
        # Пытаемся отредактировать сообщение
        await callback_query.message.edit_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        try:
            # Удаляем текущее сообщение
            await callback_query.message.delete()
        except Exception:
            pass  # Игнорируем ошибки удаления
        # Отправляем новое сообщение
        await callback_query.message.answer(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    finally:
        # Закрываем уведомление о callback
        await callback_query.answer()
