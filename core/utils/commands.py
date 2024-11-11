from aiogram import Bot
from aiogram.types import BotCommand


# Функция установки команд бота
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Нажми чтобы начать"),
    ]
    await bot.set_my_commands(commands)
