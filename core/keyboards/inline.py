from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def start_inline_keyboard():
    builder = InlineKeyboardBuilder()
    # Каждая строка содержит по одной кнопке
    builder.row(InlineKeyboardButton(text='🔗 Ссылка на основной канал', url='http://t.me/ivaslavskov'))
    builder.row(InlineKeyboardButton(text='📝 Участвовать!', callback_data='participate'))
    builder.row(InlineKeyboardButton(text='📞 Вызвать оператора', callback_data="call_operator"))
    return builder.as_markup()

def call_operator_button():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Связаться с оператором", callback_data="call_operator"))
    return builder.as_markup()

def confirm_payment_button():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Подтвердить оплату", callback_data="confirm_payment"))
    return builder.as_markup()

def admin_confirm_photo_keyboard(user_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Одобрить", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{user_id}")
        )
    return builder.as_markup()

def admin_confirm_payment_keyboard(user_id):
    # Создание инлайн-клавиатуры для администратора
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Оплата подтверждена", callback_data=f"payment_confirm_{user_id}"),
        InlineKeyboardButton(text="Оплата не подтверждена", callback_data=f"payment_reject_{user_id}")
    )
    return builder.as_markup()

# ------------------------------------------------------------------------------------------------

def admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🆕Создать розыгрыш", callback_data="start_draw"))
    builder.row(InlineKeyboardButton(text="⚙️Управление розыгрышами", callback_data="manage_draw"))
    builder.row(InlineKeyboardButton(text="🏁Завершить розыгрыш", callback_data="end_draw"))
    # builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_previous_menu"))
    return builder.as_markup()

