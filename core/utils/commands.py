from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command='/start', description='Start work'),
        BotCommand(command='/first', description='Ссылка на основной канал'),
        BotCommand(command='/second', description='Подать заявку для участия'),
        BotCommand(command='/third', description='Как устроен розыгрыш'),
        BotCommand(command='/fourth', description='Условия участия в розыгрыше'),
        BotCommand(command='/fifth', description='Вызвать свободного оператора'),
        BotCommand(command='/help', description='Use if you need halp'),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())