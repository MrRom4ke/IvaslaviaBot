from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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

def create_check_buttons(drawing_id, drawing_status=None):
    """Создает кнопки для проверки скриншотов и оплат для выбранного розыгрыша."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏞Скриншоты", callback_data=f"check_screenshots_{drawing_id}"))
    builder.row(InlineKeyboardButton(text="💰Оплаты", callback_data=f"check_payments_{drawing_id}"))
    if drawing_status in ("active", "ready_to_draw", "upcoming"):
        builder.row(
            InlineKeyboardButton(text="📅 Продлить", callback_data=f"extend_drawing_{drawing_id}")
        )
    builder.row(InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_previous_menu"))
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


def create_payment_review_keyboard(drawing_id, participant_index, total_participants):
    """Создаёт клавиатуру для проверки скриншотов оплаты."""
    builder = InlineKeyboardBuilder()

    # Кнопки навигации
    if participant_index > 0:
        builder.add(InlineKeyboardButton(text="⬅️ Предыдущий", callback_data=f"prev_payment_{drawing_id}_{participant_index}"))
    if participant_index < total_participants - 1:
        builder.add(InlineKeyboardButton(text="Следующий ➡️", callback_data=f"next_payment_{drawing_id}_{participant_index}"))

    # Кнопки управления
    builder.row(
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_payment_{drawing_id}_{participant_index}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_payment_{drawing_id}_{participant_index}")
    )

    # Кнопка "Назад" к предыдущему меню
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"manage_drawing_{drawing_id}")
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

    return builder.as_markup()




def generate_winner_selection_keyboard(drawing_id, participant_index, total_participants, user_id):
    """Генерирует клавиатуру для выбора победителя."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text="👑 Выбрать победителя",
        callback_data=f"set_winner_{user_id}_{drawing_id}"  # Передаем user_id
    )

    # Добавляем кнопки для переключения участников
    if participant_index > 0:
        builder.button(
            text="⬅️ Назад",
            callback_data=f"prev_participant_{participant_index}_{drawing_id}"
        )
    if participant_index < total_participants - 1:
        builder.button(
            text="➡️ Вперед",
            callback_data=f"next_participant_{participant_index}_{drawing_id}"
        )

    return builder.as_markup()


def generate_winners_summary_keyboard(drawing_id: int) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для управления выбором победителей."""
    builder = InlineKeyboardBuilder()

    # Кнопка для выбора победителей
    builder.button(
        text="👑 Выбрать победителей",
        callback_data=f"select_winners_{drawing_id}"
    )

    # Кнопка "Назад"
    builder.button(
        text="⬅️ Назад",
        callback_data="end_draw"
    )

    return builder.as_markup()
