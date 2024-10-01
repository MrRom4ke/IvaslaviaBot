import logging
from asyncio import Lock
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.config import ADMIN_ID
from database import add_application, get_application, increment_attempts
from core.utils.stateform import ApplicationForm
from core.keyboards.inline import admin_confirm_payment_keyboard, admin_confirm_photo_keyboard, call_operator_button, confirm_payment_button, start_inline_keyboard


# Создаём глобальный словарь для блокировки по пользователю
locks = {}

# Команда /start
async def cmd_start(message: Message):
    kb = start_inline_keyboard()
    await message.answer("Добро пожаловать! Выберите опцию ниже:", reply_markup=kb)

# Обработка команды /second
async def cmd_second(message: Message, state: FSMContext):
    user_id = message.from_user.id
    application = get_application(user_id)
    
    if application and application[2] in ['pending', 'payment_pending', 'payment_confirmed']:
        await message.answer("Ваша заявка уже находится на рассмотрении или одобрена.")
        return
    
    await message.answer("Пожалуйста, отправьте коректный скриншот участника.\nУ вас одна попытка\nЕсли ваша заявка была отклонена обратитесь в тех. поддержку")
    await state.set_state(ApplicationForm.WAITING_FOR_SCREEN)

# Обработка получения изображения
async def handle_screen(message: Message, state: FSMContext):
    user_id = message.from_user.id
    # Если у пользователя нет блокировки, создаём её
    if user_id not in locks:
        locks[user_id] = Lock()

    async with locks[user_id]:
        application = get_application(user_id)

        # Если заявка уже в статусе одобрена и требует оплаты
        if application and application[2] == 'payment_pending':
            # Сообщение об оплате и предоставление реквизитов
            await message.answer('Ваша заявка уже одобрена, но требует оплаты. Пожалуйста, сделайте оплату по следующим реквизитам:\n[Указать реквизиты].', reply_markup=confirm_payment_button())
            # Сообщение Для вызова оператора
            await message.answer('Если у вас есть другие вопросы, обратитесь к оператору', reply_markup=call_operator_button())
            return

        # Проверка на наличие активной заявки
        if application and application[2] in ['pending', 'payment_pending', 'payment_confirmed']:
            await message.answer("Допускается присылать только один скриншот\nВаш первый скриншотн аходится в обработке, дождитесь проверки")
            return
        
        # Проверка при отклоненной заявке
        if application and application[2] == 'rejected':
            await message.answer("Допускается присылать только один скриншот\nВаш первый скриншотн аходится в обработке, дождитесь проверки")
            return

        if not message.photo:
            await message.answer("Пожалуйста, отправьте изображение.")
            return

        try:
            # Работаем с последней фотографией
            photo = message.photo[-1]
            file = await message.bot.get_file(photo.file_id)
            file_path = f'IvaslaviaBot/images/{user_id}.jpg'
            await message.bot.download(file.file_id, file_path)

            # Сохраняем заявку в базе данных
            add_application(user_id, file_path)

            await message.answer("Ваша заявка отправлена на проверку администратору.")

            # Отправка только последней фотографии администратору с инлайн-клавиатурой
            await message.bot.send_photo(chat_id=ADMIN_ID, photo=photo.file_id, reply_markup=admin_confirm_photo_keyboard(user_id))
            await message.bot.send_message(
                ADMIN_ID, 
                f'Поступила заявка от пользователя [ID {user_id}]({f"tg://user?id={user_id}"}).',
                parse_mode="Markdown"
                )

        except Exception as e:
            logging.error(f"Ошибка при обработке изображения: {e}")
            await message.answer("Произошла ошибка при сохранении изображения. Попробуйте снова.")
            increment_attempts(user_id)


# Обработка подтверждения оплаты пользователем
async def handle_payment_confirmation(user_id: int, bot: Bot, state: FSMContext):
    application = get_application(user_id)
    
    if not application or application[2] != 'payment_pending':
        await bot.send_message(user_id, "У вас нет заявки, ожидающей оплаты.")
        return
    
    await bot.send_message(
        ADMIN_ID,
        text=f'Пользователь {user_id} сообщил об оплате.',
        reply_markup=admin_confirm_payment_keyboard(user_id)
    )
    
    await bot.send_message(user_id, "Ваше сообщение об оплате отправлено на проверку администратору.")
    await state.clear()
