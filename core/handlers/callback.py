from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from database import delete_application, get_application, update_status
from core.config import ADMIN_ID
from core.utils.stateform import ApplicationForm
from core.keyboards.inline import admin_confirm_payment_keyboard, call_operator_button, confirm_payment_button


# Обработка нажатия кнопок инлайн клавиатуры
async def inline_handler(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data
    if data == 'participate':
        await callback_query.message.answer("Пожалуйста, отправьте коректный скриншот участника.\nУ вас одна попытка\nЕсли ваша заявка была отклонена обратитесь в тех. поддержку")
        await state.set_state(ApplicationForm.WAITING_FOR_SCREEN)
    elif data == 'draw_info':
        await callback_query.message.answer("Здесь информация о том, как устроен розыгрыш.")
    elif data == 'participation_conditions':
        await callback_query.message.answer("Здесь условия участия в розыгрыше.")
    else:
        await callback_query.message.answer("Неизвестная команда.")

    await callback_query.answer()

# Обработка подтверждения или отклонения заявки администратором
async def admin_callback(callback_query: CallbackQuery):
    data = callback_query.data
    bot = callback_query.bot
    if data.startswith("approve_") or data.startswith("reject_"):
        action, user_id = data.split("_")
        user_id = int(user_id)
        
        if action == "approve":
            update_status(user_id, 'approved')
            await callback_query.message.reply(
                f"Заявка пользователя [ID {user_id}]({f"tg://user?id={user_id}"}) одобрена.",
                parse_mode="Markdown"
                )
            
            # Отправляем пользователю сообщение об одобрении и реквизиты для оплаты
            payment_details = "Пожалуйста, оплатите участие по следующим реквизитам:\n\n[Ваши реквизиты]"
            await bot.send_message(user_id, "Ваша заявка одобрена. " + payment_details, reply_markup=confirm_payment_button())
            
            # Обновляем статус заявки
            update_status(user_id, 'payment_pending')
        elif action == "reject":
            delete_application(user_id)
            # update_status(user_id, 'rejected')
            await callback_query.message.reply(
                f"Заявка пользователя [ID {user_id}]({f"tg://user?id={user_id}"}) отклонена.",
                parse_mode="Markdown"
                )
            await bot.send_message(
                user_id, 
                "Вы не выполнили условия конкурса. Ваша заявка отклонена.\nОбратитесь в тех поддержку",
                reply_markup=call_operator_button()
                )
        
        await callback_query.answer()
    elif data.startswith("payment_confirm_") or data.startswith("payment_reject_"):
        action, user_id = data.rsplit("_", 1)
        user_id = int(user_id)
        
        if action == "payment_confirm":
            update_status(user_id, 'payment_confirmed')
            await callback_query.message.reply(
                f"Оплата пользователя [ID {user_id}]({f"tg://user?id={user_id}"}) подтверждена.",
                parse_mode="Markdown"
                )
            await bot.send_message(user_id, "Ваша оплата подтверждена. Вы успешно участвуете в конкурсе!")
        elif action == "payment_reject":
            update_status(user_id, 'payment_failed')
            await callback_query.message.reply(
                f"Оплата пользователя [ID {user_id}]({f"tg://user?id={user_id}"}) не подтверждена.",
                parse_mode="Markdown"
                )
            await bot.send_message(
                user_id, 
                "Ваша оплата не подтверждена.\nОбратитесь в тех поддержку",
                reply_markup=call_operator_button()
            )
        
        await callback_query.answer()
    else:
        await callback_query.answer("Неизвестное действие.", show_alert=True)
    # Удаление клавиатуры
    await callback_query.message.edit_reply_markup(reply_markup=None)

# Обработка нажатия кнопки "Связаться с оператором"
async def call_operator_callback(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    bot = callback_query.bot

    # Сообщаем пользователю, что оператор будет вызван, и даем ссылку на администратора
    await callback_query.message.answer(
        f"Связаться с оператором: [нажмите здесь]({f"tg://user?id={ADMIN_ID}"})",
        parse_mode="Markdown"
    )

    await bot.send_message(
        ADMIN_ID,
        f"Пользователь [ID {user_id}]({f"tg://user?id={user_id}"}) хочет связаться с оператором.",
        parse_mode="Markdown"
    )

    # Подтверждаем callback (чтобы не было ошибки на клиенте)
    await callback_query.answer()

# Обработка нажатия кнопок "Оплата подтверждена/Не подтверждена"
async def confirm_payment_callback(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id  # Получаем ID пользователя из колбэка
    bot = callback_query.bot  # Получаем объект бота
    application = get_application(user_id)
    
    if not application or application[2] != 'payment_pending':
        await bot.send_message(user_id, "У вас нет заявки, ожидающей оплаты.")
        return
    
    await bot.send_message(
        ADMIN_ID,
        text=f'Пользователь [ID {user_id}]({f"tg://user?id={user_id}"}) сообщил об оплате.',
        reply_markup=admin_confirm_payment_keyboard(user_id),
        parse_mode="Markdown",
    )
    
    await bot.send_message(user_id, "Ваше сообщение об оплате отправлено на проверку администратору.")
    await state.clear()
    await callback_query.answer()

