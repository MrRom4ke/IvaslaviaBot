import logging
from asyncio import Lock
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from IvaslaviaBot.core.db.users_crud import get_user_by_telegram_id, create_user
# from core.db.models import add_application, add_payment, get_application, increment_attempts
from IvaslaviaBot.core.keyboards.inline import admin_confirm_payment_keyboard, admin_confirm_photo_keyboard, call_operator_button, confirm_payment_button, start_inline_keyboard


# Создаём глобальный словарь для блокировки по пользователю
locks = {}

# Команда /start
async def cmd_start(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        create_user(
            name=message.from_user.full_name,
            telegram_id=message.from_user.id,
            contact_info=message.from_user.username
        )
    kb = start_inline_keyboard()
    await message.answer("Добро пожаловать! Выберите опцию ниже:", reply_markup=kb)

# # Обработка команды /second
# async def cmd_second(message: Message, state: FSMContext):
#     user_id = message.from_user.id
#     application = get_application(user_id)
    
#     if application and application[2] in ['pending', 'payment_pending', 'payment_confirmed']:
#         await message.answer("Ваша заявка уже находится на рассмотрении или одобрена.")
#         return
    
#     await message.answer("Пожалуйста, отправьте коректный скриншот участника.\nУ вас одна попытка\nЕсли ваша заявка была отклонена обратитесь в тех. поддержку")
#     await state.set_state(ApplicationForm.WAITING_FOR_SCREEN)

# # Обработка получения изображения
# async def handle_screen(message: Message, state: FSMContext):
#     user_id = message.from_user.id
#     # Если у пользователя нет блокировки, создаём её
#     if user_id not in locks:
#         locks[user_id] = Lock()

#     async with locks[user_id]:
#         application = get_application(user_id)

#         # Если заявка уже в статусе одобрена и требует оплаты
#         if application and application[2] == 'payment_pending':
#             # Сообщение об оплате и предоставление реквизитов
#             await message.answer('Ваша заявка уже одобрена, но требует оплаты. Пожалуйста, сделайте оплату по следующим реквизитам:\n[Указать реквизиты].', reply_markup=confirm_payment_button())
#             # Сообщение Для вызова оператора
#             await message.answer('Если у вас есть другие вопросы, обратитесь к оператору', reply_markup=call_operator_button())
#             return

#         # Проверка на наличие активной заявки
#         if application and application[2] in ['pending', 'payment_pending', 'payment_confirmed']:
#             await message.answer("Допускается присылать только один скриншот\nВаш первый скриншотн аходится в обработке, дождитесь проверки")
#             return
        
#         # Проверка при отклоненной заявке
#         if application and application[2] == 'rejected':
#             await message.answer("Допускается присылать только один скриншот\nВаш первый скриншотн аходится в обработке, дождитесь проверки")
#             return

#         if not message.photo:
#             await message.answer("Пожалуйста, отправьте изображение.")
#             return

#         try:
#             # Работаем с последней фотографией
#             photo = message.photo[-1]
#             file = await message.bot.get_file(photo.file_id)
#             file_path = f'IvaslaviaBot/images/application/{user_id}.jpg'
#             await message.bot.download(file.file_id, file_path)

#             # Сохраняем заявку в базе данных
#             add_application(user_id, file_path)

#             await message.answer("Ваша заявка отправлена на проверку администратору.")

#             # Отправка только последней фотографии администратору с инлайн-клавиатурой
#             await message.bot.send_message(
#                 ADMIN_ID, 
#                 f'АДМИН: Поступила заявка от пользователя [ID {user_id}]({f"tg://user?id={user_id}"}).',
#                 parse_mode="Markdown"
#                 )
#             await message.bot.send_photo(chat_id=ADMIN_ID, photo=photo.file_id, reply_markup=admin_confirm_photo_keyboard(user_id))

#         except Exception as e:
#             logging.error(f"Ошибка при обработке изображения: {e}")
#             await message.answer("Произошла ошибка при сохранении изображения. Попробуйте снова.")

# # Обработка скриншотов оплаты
# async def handle_payment_screen(message: Message, state: FSMContext):
#     user_id = message.from_user.id

#     # Если у пользователя нет блокировки, создаём её
#     if user_id not in locks:
#         locks[user_id] = Lock()

#     async with locks[user_id]:
#         application = get_application(user_id)

#         # Проверка состояния заявки пользователя
#         if not application:
#             await message.answer("У вас нет активной заявки.")
#             return
        
#         status = application[2]
#         attempts = application[3]  # Предполагаем, что количество попыток хранится в базе данных в 4-й колонке

#         # Проверка, если заявка уже подтверждена
#         if status == 'payment_confirmed':
#             await message.answer("Ваша заявка уже подтверждена, больше не требуется отправлять скриншоты.")
#             return
        
#         # Проверка на максимальное количество попыток (например, 3 попытки)
#         if attempts >= 3:
#             await message.answer("Вы исчерпали количество попыток отправки скриншота. Обратитесь к оператору для дальнейших действий.", reply_markup=call_operator_button())
#             return

#         # Проверка, если пользователь находится в статусе 'payment_pending' или 'payment_failed'
#         if status in ['payment_pending', 'payment_failed']:
#             if not message.photo:
#                 await message.answer("Пожалуйста, отправьте изображение скриншота оплаты.")
#                 return

#             try:
#                 # Работаем с последней фотографией
#                 photo = message.photo[-1]
#                 file = await message.bot.get_file(photo.file_id)
#                 file_path = f'IvaslaviaBot/images/payment/{user_id}.jpg'
#                 await message.bot.download(file.file_id, file_path)

#                 # Сохраняем заявку в базе данных
#                 add_payment(user_id, file_path)

#                 # Отправляем скриншот оплаты админу с инлайн-клавиатурой
#                 await message.bot.send_message(
#                     ADMIN_ID,
#                     f'АДМИН: Пользователь [ID {user_id}]({f"tg://user?id={user_id}"}) сообщил об оплате.\nПожалуйста, проверьте оплату.',
#                     parse_mode="Markdown"
#                 )
#                 await message.bot.send_photo(chat_id=ADMIN_ID, photo=photo.file_id, reply_markup=admin_confirm_payment_keyboard(user_id))

#                 # Информируем пользователя о том, что его сообщение об оплате отправлено на проверку
#                 await message.answer("Ваш скриншот об оплате отправлен на проверку администратору. Пожалуйста, подождите.")

#             except Exception as e:
#                 logging.error(f"Ошибка при обработке скриншота оплаты: {e}")
#                 await message.answer("Произошла ошибка при сохранении изображения. Попробуйте снова.")

#         else:
#             await message.answer("У вас нет заявки, ожидающей оплаты!")

# # Обработка подтверждения оплаты пользователем
# async def handle_payment_confirmation(user_id: int, bot: Bot, state: FSMContext):
#     application = get_application(user_id)
    
#     if not application or application[2] != 'payment_pending':
#         await bot.send_message(user_id, "У вас нет заявки, ожидающей оплаты.")
#         return
    
#     await bot.send_message(
#         ADMIN_ID,
#         text=f'АДМИН: Пользователь {user_id} сообщил об оплате.',
#         reply_markup=admin_confirm_payment_keyboard(user_id)
#     )
    
#     await bot.send_message(user_id, "Ваше сообщение об оплате отправлено на проверку администратору.")
#     await state.clear()
