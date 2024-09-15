from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from core.utils.stateform import StepsForm


async def get_form(msg: Message, state: FSMContext):
    await msg.answer(f'{msg.from_user.first_name}, start fill qestionary. Put your name')
    await state.set_state(StepsForm.GET_NAME)

async def get_name(msg: Message, state: FSMContext):
    await msg.answer(f'Your name {msg.text} Then put surnname')
    await state.update_data(name=msg.text)
    await state.set_state(StepsForm.GET_SURNAME)

async def get_surname(msg: Message, state: FSMContext):
    await msg.answer(f'{state.get_data().get('name')} surmane is {msg.text}, put your age')
    await state.update_data(surname=msg.text)