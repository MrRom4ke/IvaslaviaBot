from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_back_only_keyboard(drawing_id):
    """Создает клавиатуру с единственной кнопкой 'Вернуться'."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️Назад", callback_data=f"manage_drawing_{drawing_id}"))
    return builder.as_markup()