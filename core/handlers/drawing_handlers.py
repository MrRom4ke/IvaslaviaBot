from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.markdown import hbold

from core.db.applications_crud import user_participates_in_drawing, create_application, get_status_counts, \
    get_application_by_user_and_drawing, get_participants_by_status
from core.db.drawings_crud import get_drawing_by_id, get_drawings_by_status, get_winners
from core.keyboards.admin_inline import create_check_buttons, generate_winners_summary_keyboard
from core.keyboards.drawing_inline import create_drawing_info_buttons, generate_end_drawings_keyboard, \
    generate_drawing_summary_keyboard
from core.utils.menu_utils import update_or_send_callback_message

from core.utils.stateform import ApplicationForm


async def view_drawing_info(callback_query: CallbackQuery, state: FSMContext):
    """Отображает информацию о выбранном розыгрыше и статус заявки пользователя."""
    await state.update_data(previous_menu="draws_menu")

    drawing_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id

    # Получаем информацию о розыгрыше через метод репозитория
    drawing = get_drawing_by_id(drawing_id)

    if not drawing:
        await callback_query.message.edit_text("Информация о выбранном розыгрыше не найдена.")
        return

    # Получаем заявку пользователя
    application = get_application_by_user_and_drawing(user_id, drawing_id)

    # Форматируем даты
    start_date = datetime.strptime(drawing['start_date'], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y") if drawing['start_date'] else "Не указана"
    end_date = datetime.strptime(drawing['end_date'], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y") if drawing['end_date'] else "Не указана"

    # Формируем сообщение с информацией о розыгрыше
    info_message = (
        f"Название: {drawing['title']}\n"
        f"Описание: {drawing['description']}\n"
        f"Дата начала: {start_date}\n"
        f"Дата окончания: {end_date}\n\n"
    )

    # Добавляем информацию о заявке пользователя
    if application:
        status = application["status"]
        attempts = application.get("attempts", 0)

        if status == "pending":
            await callback_query.message.edit_text(
                "🔵 Статус вашей заявки: Ожидает проверки скриншота.\n",
                reply_markup=create_drawing_info_buttons(drawing_id, None))
        elif status == "approved":
            await callback_query.message.edit_text(
                "✅ Статус вашей заявки: \nСкриншот одобрен. Ожидаем оплату.\n",
                reply_markup=create_drawing_info_buttons(drawing_id, None))
        elif status == "rejected":
            await callback_query.message.edit_text(
                "f❌ Статус вашей заявки: \nСкриншот отклонён.\nУ вас осталось попыток: {3 - attempts}.\nВы можете загрузить новый скриншот.",
                reply_markup=create_drawing_info_buttons(drawing_id, "🆕 Загрузить новый скриншот"))
        elif status == "payment_pending":
            await callback_query.message.edit_text(
                "💳 Статус вашей заявки: \nОжидается оплата по реквизитам\nРЕКВИЗИТЫ:\n1234 5678 8901 2345",
                reply_markup=create_drawing_info_buttons(drawing_id, "🧾 Загрузить чек об оплате"))
        elif status == 'payment_bill_loaded':
            await callback_query.message.edit_text(
                "💳 Статус вашей заявки: \nЧек об оплате на проверке\n",
                reply_markup=create_drawing_info_buttons(drawing_id, None))
        elif status == "payment_confirmed":
            await callback_query.message.edit_text(
                "✅ Статус вашей заявки: \nОплата подтверждена.\nОжидайте завершения розыгрыша.",
                reply_markup=create_drawing_info_buttons(drawing_id, None))
        elif status == "payment_reject":
            await callback_query.message.edit_text(
                "❌ Статус вашей заявки: \nОплата отклонена. \nВы можете загрузить новый скриншот оплаты.",
                reply_markup=create_drawing_info_buttons(drawing_id, "🧾 Загрузить новый чек об оплате"))
    else:
        await callback_query.message.edit_text(
            "🔘 У вас нет активной заявки на участие в этом розыгрыше.\n",
            reply_markup=create_drawing_info_buttons(drawing_id, "❇️ Принять участие"))


async def continue_drawing(callback_query: CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие кнопки для продолжения участия в розыгрыше."""
    drawing_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id

    # Получаем текущую заявку пользователя
    application = get_application_by_user_and_drawing(user_id, drawing_id)

    if application:
        status = application["status"]

        if status == "pending":
            # Пользователь ожидает проверки скриншота
            await callback_query.message.edit_text(
                "Ваша заявка находится в обработке. Пожалуйста, дождитесь завершения проверки."
            )
        elif status == "rejected":
            # Пользователю нужно загрузить новый скриншот
            await callback_query.message.edit_text(
                "Ваш скриншот не прошёл проверку. Пожалуйста, загрузите новый скриншот для участия."
            )
            await state.update_data(selected_drawing_id=drawing_id)
            await state.set_state(ApplicationForm.WAITING_FOR_SCREEN)
        elif status == "payment_pending":
            # Пользователь должен загрузить скриншот оплаты
            await callback_query.message.edit_text(
                "Загрузите чек об оплате"
            )
            await state.update_data(selected_drawing_id=drawing_id)
            await state.set_state(ApplicationForm.WAITING_FOR_PAYMENT_SCREEN)
        elif status == "payment_bill_loaded":
            # Пользователь загрузил скриншот оплаты
            await callback_query.message.edit_text(
                "Ваш чек об оплате загружен и ожидает проверки"
            )
            await state.update_data(selected_drawing_id=drawing_id)
            await state.clear()
        elif status == "payment_confirmed":
            # Оплата подтверждена
            await callback_query.message.edit_text(
                "Ваша заявка одобрена, и ваша оплата была подтверждена. Ожидайте завершения розыгрыша."
            )
        elif status == "payment_reject":
            # Оплата отклонена
            await callback_query.message.edit_text(
                "Ваша оплата была отклонена. Пожалуйста, свяжитесь с организатором для решения проблемы."
            )
        elif status == "completed":
            # Заявка аннулирована - пользователь может попробовать снова
            # Проверяем лимит участников перед созданием новой заявки
            from core.db.drawings_crud import check_participant_limit
            can_join, current_count, max_count = check_participant_limit(drawing_id)
            
            if not can_join:
                drawing = get_drawing_by_id(drawing_id)
                drawing_title = drawing['title'] if drawing else "Неизвестный"
                await callback_query.message.edit_text(
                    f"❌ К сожалению, в розыгрыше \"{drawing_title}\" уже достигнут лимит участников.\n\n"
                    f"📊 Текущее количество: {current_count}/{max_count}\n"
                    f"🔒 Попробуйте позже, возможно количество участников уменьшится."
                )
                return
            
            # Создаём новую заявку
            create_application(user_id, drawing_id)
            drawing = get_drawing_by_id(drawing_id)
            drawing_title = drawing['title'] if drawing else "Неизвестный"

            await callback_query.message.edit_text(
                f"🔄 Ваша предыдущая заявка была аннулирована. Попробуйте снова!\n\n"
                f"Для участия в розыгрыше \"{drawing_title}\" пришлите один корректный скриншот."
            )
            await state.update_data(selected_drawing_id=drawing_id)
            await state.set_state(ApplicationForm.WAITING_FOR_SCREEN)
        else:
            # Любой другой статус
            await callback_query.message.edit_text(
                "Ваша заявка находится в неизвестном состоянии. Пожалуйста, свяжитесь с поддержкой."
            )
    else:
        # Проверяем лимит участников перед созданием заявки
        from core.db.drawings_crud import check_participant_limit
        can_join, current_count, max_count = check_participant_limit(drawing_id)
        
        if not can_join:
            drawing = get_drawing_by_id(drawing_id)
            drawing_title = drawing['title'] if drawing else "Неизвестный"
            await callback_query.message.edit_text(
                f"❌ К сожалению, в розыгрыше \"{drawing_title}\" уже достигнут лимит участников.\n\n"
                f"📊 Текущее количество: {current_count}/{max_count}\n"
                f"🔒 Попробуйте позже, возможно количество участников уменьшится. "
            )
            return
        
        # Создаём новую заявку, если её нет и есть место
        create_application(user_id, drawing_id)
        drawing = get_drawing_by_id(drawing_id)
        drawing_title = drawing['title'] if drawing else "Неизвестный"

        await callback_query.message.edit_text(
            f"Отлично! Для участия в розыгрыше \"{drawing_title}\" пришлите один корректный скриншот."
        )
        await state.update_data(selected_drawing_id=drawing_id)
        await state.set_state(ApplicationForm.WAITING_FOR_SCREEN)


async def show_drawing_info(callback_query: CallbackQuery, state: FSMContext):
    """Отображает информацию о выбранном розыгрыше и статистику участников администратору в меню Управление"""
    await state.update_data(previous_menu=f"active_draws")

    drawing_id = int(callback_query.data.split("_")[-1])
    drawing = get_drawing_by_id(drawing_id)  # Получение информации о розыгрыше из БД
    status_counts = get_status_counts(drawing_id)
    # Подготовка данных
    participants_count = sum(status_counts.values())  # Общее количество заявок
    pending = status_counts.get('pending', 0)
    approved = status_counts.get('approved', 0)
    rejected = status_counts.get('rejected', 0)
    payment_pending = status_counts.get('payment_pending', 0)
    payment_bill_loaded = status_counts.get('payment_bill_loaded', 0)
    payment_confirmed = status_counts.get('payment_confirmed', 0)
    payment_reject = status_counts.get('payment_reject', 0)

    # Учитываем все статусы оплаты как часть одобренных
    total_approved = approved + payment_pending + payment_confirmed + payment_reject

    if not drawing:
        await callback_query.message.answer("Информация о выбранном розыгрыше не найдена.")
        return

    # Преобразуем строки в datetime, если они существуют
    start_date = datetime.strptime(drawing['start_date'], "%Y-%m-%d %H:%M:%S").strftime('%d.%m.%Y') if drawing['start_date'] else "Не указана"
    end_date = datetime.strptime(drawing['end_date'], "%Y-%m-%d %H:%M:%S").strftime('%d.%m.%Y') if drawing['end_date'] else "Не указана"

    # Получаем информацию о лимите участников
    max_participants = drawing.get('max_participants', 0)
    limit_info = f"  Лимит участников:----------- {max_participants}" if max_participants > 0 else "  Лимит участников:------------ Не установлен"
    
    info_message = (
        f"```\n"
        f"Название: {drawing['title']}\n"
        f"Описание: {drawing['description']}\n"
        f"Дата начала:                  {start_date}\n"
        f"Дата окончания:               {end_date}\n\n"
        f"Общая статистика заявок:\n"
        f"  Количество участников:------ {participants_count}\n"
        f"{limit_info}\n"
        f"  Ожидают проверки:----------- {pending}\n"
        f"  Одобрено:------------------- {total_approved}\n"
        f"  Отклонено:------------------ {rejected}\n"
        f"  Ожидаем оплату:------------- {payment_pending}\n"
        f"  Ожидают проверки оплаты:---- {payment_bill_loaded}\n"
        f"  Подтверждено оплата:-------- {payment_confirmed}\n"
        f"  Оплата отклонена:----------- {payment_reject}\n"
        f"```"
    )

    await update_or_send_callback_message(callback_query, info_message, reply_markup=create_check_buttons(drawing_id), parse_mode="Markdown")


async def handle_end_draw_callback(query: CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие кнопки завершения розыгрыша."""
    await state.update_data(previous_menu="admin_panel")

    # Получаем список розыгрышей в статусе ready_to_draw
    drawings = get_drawings_by_status(['ready_to_draw'])

    if not drawings:
        await query.message.answer("На данный момент нет розыгрышей, готовых к завершению.")
        return

    # Генерируем клавиатуру с розыгрышами
    await update_or_send_callback_message(
        callback_query=query,
        text="Выберите розыгрыш, который хотите завершить:",
        reply_markup=generate_end_drawings_keyboard(drawings)
    )


async def show_drawing_summary(query: CallbackQuery, state: FSMContext, drawing_id: int = None):
    """Отображает информацию о розыгрыше и предоставляет выбор победителей."""

    # Проверяем, передан ли drawing_id напрямую
    if drawing_id is None:
        drawing_id = int(query.data.split("_")[-1])

    print(f"DEBUG: Received drawing_id={drawing_id}")

    drawing = get_drawing_by_id(drawing_id)

    if not drawing:
        print(f"ERROR: drawing_id={drawing_id} not found in DB.")
        await query.message.answer("Информация о розыгрыше не найдена.")
        return

    # Получаем количество победителей и участников со статусом "payment_confirmed"
    winners_count = drawing.get("winners_count", 0)
    participants_count = len(get_participants_by_status(drawing_id, status="payment_confirmed"))

    # Форматируем сообщение
    summary_message = (
        f"🏆 Название: {drawing['title']}\n"
        f"📅 Дата окончания: {drawing['end_date']}\n"
        f"👥 Количество участников: {participants_count}\n"
        f"🎖 Количество победителей: {winners_count}\n"
    )

    # Генерируем клавиатуру
    if winners_count == 0:
        reply_markup = generate_drawing_summary_keyboard(drawing_id, winners_count)  # Выбор числа победителей
    else:
        reply_markup = generate_winners_summary_keyboard(drawing_id)  # Выбор самих победителей

    # Отправляем сообщение
    await update_or_send_callback_message(query, summary_message, reply_markup)


async def show_drawing_winners(query: CallbackQuery):
    """Отображает список победителей для указанного розыгрыша."""
    drawing_id = int(query.data.split("_")[-1])

    # Получаем данные о розыгрыше
    result = get_drawing_by_id(drawing_id)
    print(f"DEBUG: get_drawing_by_id({drawing_id}) returned: {result}")  # 🔍 Проверяем, что пришло

    # Если `result` — список, берем первый элемент
    if isinstance(result, list) and result:
        result = result[0]

    # Проверяем, что это словарь
    if not isinstance(result, dict):
        await query.answer("Ошибка: данные о розыгрыше не найдены.", show_alert=True)
        return

    drawing_title = result.get("title", "Неизвестный розыгрыш")  # ✅ Теперь точно словарь

    # Получаем победителей
    winners = get_winners(drawing_id)

    if not winners:
        await query.answer("Победители еще не выбраны.", show_alert=True)
        return

    # Формируем список победителей: если есть alias — используем @alias, иначе ссылка по ID
    winners_lines = []
    for i, w in enumerate(winners):
        alias = w.get('telegram_alias')
        if alias:
            winners_lines.append(f"{i + 1}. [@{alias}](tg://user?id={w['telegram_id']})")
        else:
            winners_lines.append(f"{i + 1}. [{w['telegram_id']}](tg://user?id={w['telegram_id']})")
    winners_list = "\n".join(winners_lines)

    message_text = f"🏆 Победители розыгрыша **{drawing_title}**:\n\n{winners_list}"

    await update_or_send_callback_message(query, message_text, parse_mode="Markdown")
