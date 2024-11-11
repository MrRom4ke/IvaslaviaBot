from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def generate_admin_menu_keyboard():
    """Создает клавиатуру для меню управления розыгрышами."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Активные розыгрыши", callback_data="active_draws"),
        InlineKeyboardButton(text="Завершенные розыгрыши", callback_data="completed_draws")
    )
    return builder.as_markup()

def create_check_buttons(drawing_id):
    """Создает кнопки для проверки скриншотов и оплат для выбранного розыгрыша."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Проверить скриншоты", callback_data=f"check_screenshots_{drawing_id}"),
        InlineKeyboardButton(text="Проверить оплаты", callback_data=f"check_payments_{drawing_id}")
    )
    return builder.as_markup()