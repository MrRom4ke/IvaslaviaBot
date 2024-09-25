from aiogram import Bot
from aiogram.types import Message
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from core.utils.stateform import StepsForm


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

async def get_help(call: CallbackQuery, bot: Bot):
    user_id = 1120483862
    await bot.send_message(chat_id=user_id, text='Привет! Мне нужна помощь с розыгрышем!')

async def start_draw(call: CallbackQuery, bot: Bot, state: FSMContext):
    await bot.send_message(call.from_user.id, 'Пришлите скриншот!')
    await state.set_state(StepsForm.GET_SCREEN)

async def get_screen(msg: Message, state: FSMContext):
    await msg.answer('Ваш скриншот обрабатывается оператором')
