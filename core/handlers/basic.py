from aiogram import Bot
from aiogram.types import Message


async def get_start(msg: Message, bot: Bot):
    await bot.send_message(msg.from_user.id, f'Hello')
    await msg.answer(f'Hello {msg.from_user.first_name}')
    await msg.reply(f'Hello {msg.from_user.first_name}')
    print(msg.from_user.id)