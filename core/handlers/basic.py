import logging
import os
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.config import ADMIN_ID
from database import add_application, get_application, increment_attempts
from core.utils.stateform import ApplicationForm
from core.keyboards.inline import start_inline_keyboard

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
    application = get_application(user_id)
    
    if application and application[2] in ['pending', 'payment_pending', 'payment_confirmed']:
        await message.answer("Ваша заявка уже находится на рассмотрении или одобрена.")
        return
    
    if not message.photo:
        await message.answer("Пожалуйста, отправьте изображение.")
        return
    
    # try:
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_path = f'IvaslaviaBot/images/{user_id}.jpg'
    await message.bot.download(file.file_id, file_path)
    
    # Сохраняем заявку в базе данных
    add_application(user_id, file_path)
    
    await message.answer("Ваша заявка отправлена на проверку администратору.")
    
    # Создание инлайн-клавиатуры для администратора
    admin_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Одобрить", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{user_id}")
            ]
        ]
    )

    # Отправка фотографии администратору с инлайн-клавиатурой
    file_id = photo.file_id
    await message.bot.send_photo(chat_id=ADMIN_ID, photo=file_id, reply_markup=admin_kb)
    await message.bot.send_message(ADMIN_ID, f'Поступила заявка от пользователя {user_id}.')
    await state.clear()
    # except Exception as e:
    #     logging.error(f"Ошибка при обработке изображения: {e}")
    #     await message.answer("Произошла ошибка при сохранении изображения. Попробуйте снова.")
    #     increment_attempts(user_id)

# Обработка подтверждения оплаты пользователем
async def handle_payment_confirmation(message: Message, state: FSMContext):
    user_id = message.from_user.id
    application = get_application(user_id)
    
    if not application or application[2] != 'payment_pending':
        await message.answer("У вас нет заявки, ожидающей оплаты.")
        return
    
    # Создание инлайн-клавиатуры для администратора
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Оплата подтверждена", callback_data=f"payment_confirm_{user_id}"),
        InlineKeyboardButton(text="Оплата не подтверждена", callback_data=f"payment_reject_{user_id}")
    )
    admin_kb = builder.as_markup()
    
    await message.bot.send_message(
        ADMIN_ID,
        text=f'Пользователь {user_id} сообщил об оплате.',
        reply_markup=admin_kb
    )
    
    await message.answer("Ваше сообщение об оплате отправлено на проверку администратору.")
    await state.clear()
