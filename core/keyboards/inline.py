from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.utils.callback import MacInfo


select_macbook = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='MacBook Pro 14', callback_data='apple_pro_14_m1_2022')],
        [InlineKeyboardButton(text='MacBook Air 13', callback_data='apple_air_13_m2_2023')],
        [InlineKeyboardButton(text='MacBook Pro 16', callback_data='apple_pro_16_m3_2024')],
        [InlineKeyboardButton(text='Link', url='https://apple.com')],
        [InlineKeyboardButton(text='Profile', url='http://t.me/zloiqw')],
    ]
)

def get_inline_keyboard():
    keyboard_bulder = InlineKeyboardBuilder()
    keyboard_bulder.button(text='MacBook Pro 14', callback_data=MacInfo(model='air', size=14, chip='M1', year=2023))
    keyboard_bulder.button(text='MacBook Pro 14', callback_data=MacInfo(model='pro', size=13, chip='M2', year=2024))
    keyboard_bulder.button(text='MacBook Pro 14', callback_data=MacInfo(model='pro', size=15, chip='M3', year=2025))
    keyboard_bulder.button(text='Link', url='https://apple.com')
    keyboard_bulder.button(text='Profile', url='http://t.me/zloiqw')
    keyboard_bulder.adjust(3)
    return keyboard_bulder.as_markup()