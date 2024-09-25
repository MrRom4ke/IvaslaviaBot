from aiogram import Bot
from aiogram.types import Message
from aiogram.types import CallbackQuery
from core.keyboards.reply import reply_keyboard, loc_tel_poll_keyboard, get_reply_builder
from core.keyboards.inline import select_macbook, get_inline_keyboard, start_inline_keyboard




async def get_start(msg: Message, bot: Bot):
    await bot.send_message(msg.from_user.id, f'Привет {msg.from_user.first_name}!', reply_markup=start_inline_keyboard())

async def get_photo(msg: Message, bot: Bot):
    await msg.answer('Ok, you send me photo, I will save it')
    try:
        file = await bot.get_file(msg.photo[-1].file_id)
        await bot.download(file.file_id, 'photo.jpg')
    except:
        await msg.answer('Error')

async def get_hello(msg: Message, bot: Bot):
    await msg.answer('And hello to you', reply_markup=loc_tel_poll_keyboard)

async def get_location(msg: Message, bot: Bot):
    await msg.answer(f'You sent me yor location it is Longitude:{msg.location.longitude} Latitude:{msg.location.latitude}')

async def get_first_option(msg: Message, bot: Bot):
    await msg.answer('Link to main chanel', reply_markup=get_reply_builder())

async def get_second_option(msg: Message, bot: Bot):
    await msg.answer('Application', reply_markup=select_macbook)

async def get_third_option(call: CallbackQuery, bot: Bot):
    await call.message.answer('How to use draw')

async def get_fourth_option(msg: Message, bot: Bot):
    await msg.answer('Draws rules', reply_markup=get_inline_keyboard())

async def get_fifth_option(msg: Message, bot: Bot):
    await msg.answer('Call to operator')