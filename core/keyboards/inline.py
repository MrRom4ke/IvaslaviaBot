from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.config import ADMIN_ID


def start_inline_keyboard():
    user_id = ADMIN_ID
    builder = InlineKeyboardBuilder()
    
    # Каждая строка содержит по одной кнопке
    builder.row(InlineKeyboardButton(text='Ссылка на основной канал', url='http://t.me/ivaslavskov'))
    builder.row(InlineKeyboardButton(text='Подать заявку для участия', callback_data='participate'))
    builder.row(InlineKeyboardButton(text='Как устроен розыгрыш', callback_data='draw_info'))
    builder.row(InlineKeyboardButton(text='Условия участия в розыгрыше', callback_data='participation_conditions'))
    builder.row(InlineKeyboardButton(text='Вызвать свободного оператора', url=f'tg://user?id={user_id}'))
    
    return builder.as_markup()