from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from database import increment_attempts, update_status
from core.utils.stateform import ApplicationForm


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
            await callback_query.message.reply(f"Заявка пользователя {user_id} одобрена.")
            
            # Отправляем пользователю сообщение об одобрении и реквизиты для оплаты
            payment_details = "Пожалуйста, оплатите участие по следующим реквизитам:\n\n[Ваши реквизиты]"
            await bot.send_message(user_id, "Ваша заявка одобрена. " + payment_details)
            
            # Обновляем статус заявки
            update_status(user_id, 'payment_pending')
        elif action == "reject":
            update_status(user_id, 'rejected')
            increment_attempts(user_id)
            await callback_query.message.reply(f"Заявка пользователя {user_id} отклонена.")
            await bot.send_message(user_id, "Вы не выполнили условия конкурса. Ваша заявка отклонена.\nОбратитесь в тех поддержку")
        
        await callback_query.answer()
    elif data.startswith("payment_confirm_") or data.startswith("payment_reject_"):
        action, user_id = data.rsplit("_", 1)
        user_id = int(user_id)
        
        if action == "payment_confirm":
            update_status(user_id, 'payment_confirmed')
            await callback_query.message.reply(f"Оплата пользователя {user_id} подтверждена.")
            await bot.send_message(user_id, "Ваша оплата подтверждена. Вы успешно участвуете в конкурсе!")
        elif action == "payment_reject":
            update_status(user_id, 'payment_failed')
            await callback_query.message.reply(f"Оплата пользователя {user_id} не подтверждена.")
            await bot.send_message(user_id, "Ваша оплата не подтверждена. Ваша заявка аннулирована.")
        
        await callback_query.answer()
    else:
        await callback_query.answer("Неизвестное действие.", show_alert=True)
