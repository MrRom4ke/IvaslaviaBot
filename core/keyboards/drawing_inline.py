from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def generate_drawings_keyboard(drawings):
    """Создает инлайн-клавиатуру с названиями розыгрышей для выбора в каком участвовать Пользователю"""
    builder = InlineKeyboardBuilder()
    for drawing in drawings:
        builder.row(
            InlineKeyboardButton(
                text=f"{drawing[1]}",  # Отображаем только название
                callback_data=f"view_drawing_{drawing[0]}"  # Используем ID розыгрыша
            )
        )
    return builder.as_markup()

def create_drawing_info_buttons(drawing_id):
    """Создает кнопки для управления розыгрышем: 'Принять участие' и 'Вернуться'."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Принять участие", callback_data=f"participate_{drawing_id}"),
        InlineKeyboardButton(text="Вернуться", callback_data="back_to_list")
    )
    return builder.as_markup()

def generate_drawings_list_keyboard(drawings):
    """Создает клавиатуру для списка розыгрышей в меню админа Управление"""
    builder = InlineKeyboardBuilder()
    for drawing in drawings:
        builder.row(
            InlineKeyboardButton(
                text=f"{drawing['title']} (Статус: {drawing['status']})",
                callback_data=f"manage_drawing_{drawing['drawing_id']}"
            )
        )
    return builder.as_markup()
