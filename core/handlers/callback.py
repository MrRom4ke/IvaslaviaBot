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

async def get_screen(msg: Message, state: FSMContext, bot: Bot):
    try:
        file = await bot.get_file(msg.photo[-1].file_id)
        user_id = msg.from_user.id
        print(user_id)
        await bot.download(file.file_id, f'IvaslaviaBot/images/{str(user_id)}.jpg')
        await msg.answer('Ваш скриншот обрабатывается оператором')
        await state.update_data(user_id=user_id)
        await state.set_state(StepsForm.CHECK_IMAGE)
        await bot.send_message(1120483862, text=f'Поступила заявка на участие от пользователя {user_id}')
        with open(f'IvaslaviaBot/images/{str(user_id)}.jpg', 'rb') as photo:
            await bot.send_photo(1120483862, photo=photo, caption=f'Фото от пользователя {user_id}')
    except:
        await msg.answer('Ошибка, пришлите картинку')

async def check_image_operator(msg: Message, state: FSMContext, bot: Bot):
    pass
    # user_data = await state.get_data()
    # user_id = user_data.get('user_id')
    # print('another', user_id)
    # await bot.send_message(1120483862, text=f'Поступила заявка на участие от пользователя {user_id}')
    # # await bot.send_photo(1120483862, )
    
