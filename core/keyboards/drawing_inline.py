from datetime import datetime

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
    builder.row(InlineKeyboardButton(text='⬅️Назад', callback_data='back_to_previous_menu'))
    return builder.as_markup()

def create_drawing_info_buttons(drawing_id):
    """Создает кнопки для управления розыгрышем: 'Принять участие' и 'Вернуться'."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❇️ Принять участие", callback_data=f"participate_{drawing_id}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_previous_menu"))
    return builder.as_markup()


def generate_drawings_list_keyboard(drawings, show_back_button=True):
    """Создает клавиатуру для списка розыгрышей в меню админа с краткой датой окончания и кнопкой 'Назад'."""
    builder = InlineKeyboardBuilder()

    for drawing in drawings:
        # Преобразуем строку даты окончания в формат дд.мм.гг
        end_date = datetime.strptime(drawing['end_date'], "%Y-%m-%d %H:%M:%S")
        formatted_end_date = end_date.strftime("%d.%m.%y")

        # Выбираем эмодзи в зависимости от текущей даты
        emoji = "❗️" if end_date < datetime.now() else "🏁"

        builder.row(
            InlineKeyboardButton(
                text=f"{drawing['title']} ({emoji} {formatted_end_date})",
                callback_data=f"manage_drawing_{drawing['drawing_id']}"
            )
        )
    # Кнопка "Назад"
    if show_back_button:
        builder.row(InlineKeyboardButton(text="⬅️Назад", callback_data="manage_draw"))

    return builder.as_markup()
