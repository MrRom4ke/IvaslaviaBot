from aiogram import Bot
from aiogram.types import Message


async def get_start(msg: Message, bot: Bot):
    await bot.send_message(msg.from_user.id, f'''Привет {msg.from_user.first_name}!
Введи цифру из предложенных чтобы узнать больш: 
1. Ссылка на основной канал. 
2. Подать заявку для участия.
3. Как устроен розыгрыш.
4. Условия участия в розыгрыше. 
5. Вызвать свободного оператора.''')

async def get_photo(msg: Message, bot: Bot):
    await msg.answer('Ok, you send me photo, I will save it')
    try:
        file = await bot.get_file(msg.photo[-1].file_id)
        await bot.download(file.file_id, 'photo.jpg')
    except:
        await msg.answer('Error')

async def get_hello(msg: Message, bot: Bot):
    await msg.answer('And hello to you')

async def get_first_option(msg: Message, bot: Bot):
    await msg.answer('Link to main chanel')

async def get_second_option(msg: Message, bot: Bot):
    await msg.answer('Application')

async def get_third_option(msg: Message, bot: Bot):
    await msg.answer('How to use draw')

async def get_fourth_option(msg: Message, bot: Bot):
    await msg.answer('Draws rules')

async def get_fifth_option(msg: Message, bot: Bot):
    await msg.answer('Call to operator')