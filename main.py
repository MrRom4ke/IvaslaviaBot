import asyncio
import logging
import configparser
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ContentType
from aiogram.filters import Command, CommandStart
from core.filters.iscontact import IsTrueContact
from aiogram import F
from core.handlers.basic import get_start, get_photo, get_hello, get_first_option, get_second_option, get_third_option, get_fourth_option, get_fifth_option
from core.handlers.contact import get_true_contact, get_false_contact
from core.utils.commands import set_commands


config = configparser.ConfigParser()
config.read('IvaslaviaBot/config.ini')
TOKEN = config['settings']['TOKEN']
ADMIN_ID = config['settings']['ADMIN_ID']


async def start_bot(bot: Bot):
    await bot.send_message(ADMIN_ID, text='Бот запущен')
    await set_commands(bot)

async def stop_bot(bot: Bot):
    await bot.send_message(ADMIN_ID, text='Бот остановлен')


async def start():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - [%(levelname)s] - %(name)s - "
                                "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
                        )
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    # Порядок обработки хэндлеров в диспетчере
    dp.message.register(get_true_contact, F.contact, IsTrueContact())
    dp.message.register(get_false_contact, F.contact)
    dp.message.register(get_first_option, Command(commands='/first'))
    # dp.message.register(get_first_option, F.text == '1')
    dp.message.register(get_second_option, F.text == '2')
    dp.message.register(get_third_option, F.text == '3')
    dp.message.register(get_fourth_option, F.text == '4')
    dp.message.register(get_fifth_option, F.text == '5')
    dp.message.register(get_photo, F.photo)
    dp.message.register(get_start, Command(commands=['start']))
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)
    # dp.message.register(get_start, CommandStart)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(start())
