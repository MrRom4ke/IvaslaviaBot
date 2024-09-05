from aiogram import Bot
from aiogram.types import Message


async def get_true_contact(msg: Message, bot: Bot):
    await msg.answer('You sent your own contact')

async def get_false_contact(msg: Message, bot: Bot):
    await msg.answer('You sent not yours contact')