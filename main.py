from aiogram import Bot, Dispatcher
from aiogram.types import Message
import asyncio
import logging
import configparser
from core.handlers.basic import get_start


config = configparser.ConfigParser()
config.read('IvaslaviaBot/config.ini')
TOKEN = config['settings']['TOKEN']
ADMIN_ID = config['settings']['ADMIN_ID']


async def start_bot(bot: Bot):
    await bot.send_message(ADMIN_ID, text='Бот запущен')

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
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)
    dp.message.register(get_start)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(start())
