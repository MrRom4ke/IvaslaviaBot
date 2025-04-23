from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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

def create_drawing_info_buttons(drawing_id, btn_name):
    """Создает кнопки для управления розыгрышем: 'Принять участие' и 'Вернуться'."""
    builder = InlineKeyboardBuilder()
    if btn_name:
        builder.row(InlineKeyboardButton(text=btn_name, callback_data=f"continue_drawing_{drawing_id}"))
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


def generate_end_drawings_keyboard(drawings):
    """Создает клавиатуру с розыгрышами для завершения."""
    builder = InlineKeyboardBuilder()

    for drawing in drawings:
        builder.row(
            InlineKeyboardButton(
                text=f"{drawing['title']} ({drawing['end_date']})",
                callback_data=f"end_drawing_{drawing['drawing_id']}"
            )
        )

    # Добавляем кнопку "Назад" вне цикла
    builder.row(InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_previous_menu"))

    return builder.as_markup()


def generate_complete_drawing_keyboard(drawing_id: int):
    """Создает клавиатуру для завершения розыгрыша."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Завершить розыгрыш", callback_data=f"complete_drawing_{drawing_id}")
    )
    return builder.as_markup()

def generate_drawing_summary_keyboard(drawing_id: int, winners_count: int) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для отображения сводки розыгрыша."""
    builder = InlineKeyboardBuilder()

    if winners_count == 0:
        # Добавляем кнопки для выбора количества победителей
        buttons = [
            InlineKeyboardButton(text=f"{count}", callback_data=f"set_winners_count_{drawing_id}_{count}")
            for count in range(1, 6)
        ]

        # Формируем строки из кнопок
        builder.row(*buttons[:3])  # Первая строка: 1 2 3
        builder.row(*buttons[3:])  # Вторая строка: 4 5

        # Добавляем кнопку "Назад"
        builder.row(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="end_draw")
        )
    else:
        # Если количество победителей уже выбрано, предлагаем выбрать победителей
        builder.button(
            text="👑 Выбрать победителей",
            callback_data=f"select_winners_{drawing_id}"
        )
        # Добавляем кнопку "Назад"
        builder.row(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="end_draw")
        )

    return builder.as_markup()

def generate_completed_drawings_list_keyboard(drawings, show_back_button=True):
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
                callback_data=f"completed_drawing_{drawing['drawing_id']}"
            )
        )
    # Кнопка "Назад"
    if show_back_button:
        builder.row(InlineKeyboardButton(text="⬅️Назад", callback_data="manage_draw"))

    return builder.as_markup()

def generate_cancel_drawing_keyboard(drawing_id: int):
    """Создает клавиатуру для аннулирования розыгрыша."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отменить розыгрыш", callback_data=f"cancel_drawing_{drawing_id}")
    )
    return builder.as_markup()