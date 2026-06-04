from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery


def _is_message_not_modified_error(error: TelegramBadRequest) -> bool:
    return bool(error.message and "message is not modified" in error.message)


def _cannot_edit_as_text_error(error: TelegramBadRequest) -> bool:
    if not error.message:
        return False
    msg = error.message.lower()
    return (
        "there is no text in the message to edit" in msg
        or "message can't be edited" in msg
    )


async def _send_new_callback_message(
    callback_query: CallbackQuery,
    text: str,
    reply_markup=None,
    parse_mode=None,
):
    try:
        await callback_query.message.delete()
    except Exception:
        pass
    await callback_query.message.answer(
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )


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


async def safe_edit_callback_message(
    callback_query: CallbackQuery,
    text: str,
    reply_markup=None,
    parse_mode=None,
    disable_web_page_preview: bool | None = None,
) -> bool:
    """
    Редактирует сообщение колбэка.
    Возвращает False, если Telegram считает, что контент не изменился.
    """
    kwargs = {"text": text, "reply_markup": reply_markup}
    if parse_mode:
        kwargs["parse_mode"] = parse_mode
    if disable_web_page_preview is not None:
        kwargs["disable_web_page_preview"] = disable_web_page_preview
    try:
        await callback_query.message.edit_text(**kwargs)
        return True
    except TelegramBadRequest as e:
        if _is_message_not_modified_error(e):
            return False
        if _cannot_edit_as_text_error(e):
            await _send_new_callback_message(
                callback_query, text, reply_markup, parse_mode
            )
            return True
        raise
    except Exception:
        await _send_new_callback_message(
            callback_query, text, reply_markup, parse_mode
        )
        return True


async def update_or_send_callback_message(callback_query: CallbackQuery, text: str, reply_markup=None, parse_mode=None):
    """
    Универсальная функция для обновления существующего сообщения, вызванного колбэком,
    или отправки нового сообщения, если обновление невозможно (например, было фото).
    """
    replace_needed = False
    try:
        await callback_query.message.edit_text(
            text=text, reply_markup=reply_markup, parse_mode=parse_mode
        )
    except TelegramBadRequest as e:
        if _is_message_not_modified_error(e):
            pass
        elif _cannot_edit_as_text_error(e):
            replace_needed = True
        else:
            raise
    except Exception:
        replace_needed = True

    if replace_needed:
        await _send_new_callback_message(
            callback_query, text, reply_markup, parse_mode
        )

    await callback_query.answer()
