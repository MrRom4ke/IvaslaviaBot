from aiogram import Bot
from aiogram.types import BotCommand


# Функция установки команд бота
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Начальное приветствие"),
        BotCommand(command='/first', description='Ссылка на основной канал'),
        BotCommand(command="/second", description="Подать заявку для участия"),
        BotCommand(command='/third', description='Как устроен розыгрыш'),
        BotCommand(command='/fourth', description='Условия участия в розыгрыше'),
        BotCommand(command='/fifth', description='Вызвать свободного оператора'),
    ]
    await bot.set_my_commands(commands)
