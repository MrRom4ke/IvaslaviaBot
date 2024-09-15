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
    context_data = await state.get_data()
    await msg.answer(f'{context_data.get('name')} surmane is {msg.text}, put your age')
    await state.update_data(surname=msg.text)
    await state.set_state(StepsForm.GET_AGE)

async def get_age(msg: Message, state: FSMContext):
    await msg.answer(f'Your age is: {msg.text}')
    context_data = await state.get_data()
    await msg.answer(f'Saved data is: {context_data}')
    name = context_data.get('name')
    surname = context_data.get('surname')
    data_user = f'This is your data: Name - {name}, Surname - {surname}, Age - {msg.text}'
    await msg.answer(data_user)
    await state.clear()