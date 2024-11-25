from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def cancel_button_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Отменить создание", callback_data="cancel_creation")
    )
    return builder.as_markup()

def generate_admin_menu_keyboard():
    """Создает клавиатуру для меню управления розыгрышами."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✴️Активные", callback_data="active_draws"),
        InlineKeyboardButton(text="✅Завершенные", callback_data="completed_draws")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_previous_menu")
    )
    return builder.as_markup()

def create_check_buttons(drawing_id):
    """Создает кнопки для проверки скриншотов и оплат для выбранного розыгрыша."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏞Скриншоты", callback_data=f"check_screenshots_{drawing_id}"))
    builder.row(InlineKeyboardButton(text="💰Оплаты", callback_data=f"check_payments_{drawing_id}"))
    builder.row(InlineKeyboardButton(text="⏳Ожидающие розыгрыша", callback_data=f"awaiting_draw_{drawing_id}"))
    # Кнопка "Назад" для возврата к списку активных розыгрышей
    builder.row(InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_previous_menu"))
    return builder.as_markup()

def create_back_button_keyboard(callback_data):
    """Создает клавиатуру с кнопкой 'Назад'."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬅️Назад", callback_data=callback_data)
    )
    return builder.as_markup()

def create_screenshot_review_keyboard(drawing_id, participant_index, total_participants):
    """Создает клавиатуру для одобрения или отклонения скриншота с пагинацией."""
    builder = InlineKeyboardBuilder()

    # Кнопки "Одобрить" и "Отклонить"
    builder.row(
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_screenshot_{drawing_id}_{participant_index}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_screenshot_{drawing_id}_{participant_index}")
    )

    # Кнопки пагинации (вперед и назад)
    if participant_index > 0:
        builder.row(
            InlineKeyboardButton(text="⬅️ Предыдущий", callback_data=f"prev_screenshot_{drawing_id}_{participant_index}")
        )
    if participant_index < total_participants - 1:
        builder.row(
            InlineKeyboardButton(text="➡️ Следующий", callback_data=f"next_screenshot_{drawing_id}_{participant_index}")
        )

    # Кнопка "Назад" к предыдущему меню
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"manage_drawing_{drawing_id}")
    )

    return builder.as_markup()
