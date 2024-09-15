from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonPollType
from aiogram.utils.keyboard import ReplyKeyboardBuilder


reply_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
        KeyboardButton(text='1 Row 1 Button'), 
        KeyboardButton(text='1 Row 2 Button'),
        KeyboardButton(text='1 Row 3 Button'),
        ],
        [
        KeyboardButton(text='2 Row 1 Button'), 
        KeyboardButton(text='2 Row 2 Button'),
        KeyboardButton(text='2 Row 3 Button'),
        ],
        [
        KeyboardButton(text='3 Row 1 Button'), 
        KeyboardButton(text='3 Row 2 Button'),
        KeyboardButton(text='3 Row 3 Button'),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Choose button V',
    selective=True,
)

loc_tel_poll_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Send me location', request_location=True)],
        [KeyboardButton(text='Send me number', request_contact=True)],
        [KeyboardButton(text='Create poll', request_poll=KeyboardButtonPollType(type='regular'))],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Tips',
)

def get_reply_builder():
    keyboard_builder = ReplyKeyboardBuilder()
    keyboard_builder.button(text='1 Button')
    keyboard_builder.button(text='2 Button')
    keyboard_builder.button(text='3 Button')
    keyboard_builder.button(text='Send me number', request_contact=True)
    keyboard_builder.button(text='Create poll', request_poll=KeyboardButtonPollType(type='regular'))
    keyboard_builder.adjust(3, 2, 1)
    return keyboard_builder.as_markup(resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='Tips')