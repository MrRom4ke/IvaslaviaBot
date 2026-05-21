import time

from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID

OPERATOR_COOLDOWN_SEC = 300  # 5 минут
from core.db.applications_crud import get_user_participations_by_telegram_id
from core.db.drawings_crud import get_drawings_by_status, update_drawings_status
from core.utils.application_utils import build_operator_admin_message
from core.keyboards.drawing_inline import generate_drawings_keyboard
from core.utils.menu_utils import update_or_send_callback_message

# from core.db.models import delete_application, get_application, increment_attempts, update_status
from core.utils.stateform import ApplicationForm
# from core.keyboards.inline import admin_confirm_payment_keyboard, call_operator_button, confirm_payment_button


# Обработка нажатия кнопок инлайн клавиатуры
async def inline_handler(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(previous_menu="start_menu")

    update_drawings_status()
    drawings = get_drawings_by_status(['active'])
    if not drawings:
        await callback_query.message.answer("На данный момент нет активных розыгрышей.")
        return
    # Отправляем инлайн-клавиатуру с розыгрышами
    await update_or_send_callback_message(
        callback_query=callback_query,
        text="Выберите розыгрыш:",
        reply_markup=generate_drawings_keyboard(drawings)
    )
    await callback_query.answer()

# Обработка нажатия кнопки "Связаться с оператором"
async def call_operator_callback(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    bot = callback_query.bot

    data = await state.get_data()
    last_call = data.get("operator_last_call")
    now = time.time()
    if last_call and now - last_call < OPERATOR_COOLDOWN_SEC:
        remaining = int(OPERATOR_COOLDOWN_SEC - (now - last_call))
        minutes, seconds = divmod(remaining, 60)
        await callback_query.answer(
            f"Запрос уже отправлен. Повторить можно через {minutes} мин. {seconds} сек.",
            show_alert=True,
        )
        return

    await state.update_data(operator_last_call=now)

    await callback_query.message.answer(
        f"Связаться с оператором: [нажмите здесь](tg://user?id={ADMIN_ID})",
        parse_mode="Markdown"
    )
    participations = get_user_participations_by_telegram_id(user_id)
    admin_text = build_operator_admin_message(
        telegram_id=user_id,
        full_name=callback_query.from_user.full_name,
        username=callback_query.from_user.username,
        participations=participations,
    )
    await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    await callback_query.answer()
    
# # Обработка подтверждения или отклонения заявки администратором
# async def admin_callback(callback_query: CallbackQuery, state: FSMContext):
#     data = callback_query.data
#     bot = callback_query.bot
#     if data.startswith("approve_") or data.startswith("reject_"):
#         action, user_id = data.split("_")
#         user_id = int(user_id)
        
#         if action == "approve":
#             update_status(user_id, 'approved')
#             await callback_query.message.reply(
#                 f"АДМИН: Заявка пользователя [ID {user_id}]({f"tg://user?id={user_id}"}) одобрена.",
#                 parse_mode="Markdown"
#                 )
            
#             # Отправляем пользователю сообщение об одобрении и реквизиты для оплаты, и просим скрин об оплате
#             payment_details = "Пожалуйста, оплатите участие по следующим реквизитам:\n[Ваши реквизиты]"
#             await bot.send_message(user_id, "Ваша заявка одобрена. " + payment_details + '\nПосле оплаты, пришлите скриншот об оплате')
#             await state.set_state(ApplicationForm.WAITING_FOR_PAYMENT_SCREEN)

#             # Обновляем статус заявки
#             update_status(user_id, 'payment_pending')
#         elif action == "reject":
#             update_status(user_id, 'rejected')
#             await callback_query.message.reply(
#                 f"АДМИН: Заявка пользователя [ID {user_id}]({f"tg://user?id={user_id}"}) отклонена.",
#                 parse_mode="Markdown"
#                 )
#             await bot.send_message(
#                 user_id, 
#                 "Вы не выполнили условия конкурса. Ваша заявка отклонена.\nОбратитесь в тех поддержку",
#                 reply_markup=call_operator_button()
#                 )
        
#         await callback_query.answer()
#     elif data.startswith("payment_confirm_") or data.startswith("payment_reject_"):
#         action, user_id = data.rsplit("_", 1)
#         user_id = int(user_id)

#         application = get_application(user_id)
#         attempts = application[3]
        
#         if action == "payment_confirm":
#             update_status(user_id, 'payment_confirmed')
#             await callback_query.message.reply(
#                 f"АДМИН: Оплата пользователя [ID {user_id}]({f"tg://user?id={user_id}"}) подтверждена.",
#                 parse_mode="Markdown"
#                 )
#             await bot.send_message(user_id, "Ваша оплата подтверждена. Вы успешно участвуете в конкурсе!")
#         elif action == "payment_reject":
#             # Увеличиваем количество попыток в базе данных
#             increment_attempts(user_id)            
#             if attempts < 2:
#                 update_status(user_id, 'payment_failed')
#                 await bot.send_message(
#                     user_id, 
#                     f"Оператор сообщил, что ваша оплата не прошла.\nПожалуйста, отправьте скриншот повторно.\nОсталось попыток для оплаты: {2 - attempts}"
#                     )
#                 await callback_query.message.reply(
#                     f"АДМИН: Оплата пользователя [ID {user_id}]({f"tg://user?id={user_id}"}) не подтверждена.",
#                     parse_mode="Markdown"
#                 )
#                 await callback_query.answer()
#             else:
#                 await bot.send_message(
#                     user_id, 
#                     "Вы достигли максимального количества попыток подтверждения оплаты. Пожалуйста, обратитесь в тех. поддержку.", 
#                     reply_markup=call_operator_button()
#                     )
#                 update_status(user_id, 'payment_rejected')
#     else:
#         await callback_query.answer("Неизвестное действие.", show_alert=True)
#     # Удаление клавиатуры
#     await callback_query.message.edit_reply_markup(reply_markup=None)
#     await callback_query.answer()

# # Обработка нажатия кнопок "Оплата подтверждена/Не подтверждена"
# async def confirm_payment_callback(callback_query: CallbackQuery, state: FSMContext):
#     user_id = callback_query.from_user.id  # Получаем ID пользователя из колбэка
#     bot = callback_query.bot  # Получаем объект бота
#     application = get_application(user_id)
    
#     if not application or application[2] != 'payment_pending':
#         await bot.send_message(user_id, "У вас нет заявки, ожидающей оплаты.")
#         return
    
#     await bot.send_message(
#         ADMIN_ID,
#         text=f'АДМИН: Пользователь [ID {user_id}]({f"tg://user?id={user_id}"}) сообщил об оплате.',
#         reply_markup=admin_confirm_payment_keyboard(user_id),
#         parse_mode="Markdown",
#     )
    
#     await bot.send_message(user_id, "Ваше сообщение об оплате отправлено на проверку администратору.")
#     await state.clear()
#     await callback_query.answer()

