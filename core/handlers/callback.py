from aiogram import Bot
from aiogram.types import CallbackQuery


async def select_macbook(call: CallbackQuery, bot: Bot):
    firm = call.data.split('_')[0]
    model = call.data.split('_')[1]
    num_model = call.data.split('_')[2]
    processor = call.data.split('_')[3]
    year = call.data.split('_')[4]
    answer = f'Hello {call.message.from_user.first_name}, you choose:\
        Firm: {firm},\
            Model: {model} {num_model} on chip {processor} {year} years'
    await call.message.answer(answer)
    await call.answer()