from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from IvaslaviaBot.core.db.applications_crud import user_participates_in_drawing, create_application, get_status_counts
from IvaslaviaBot.core.db.drawings_crud import get_drawing_by_id
from IvaslaviaBot.core.keyboards.admin_inline import create_check_buttons
from IvaslaviaBot.core.keyboards.drawing_inline import create_drawing_info_buttons
from IvaslaviaBot.core.utils.menu_utils import update_or_send_callback_message

from IvaslaviaBot.core.utils.stateform import ApplicationForm


async def participate_in_drawing(callback_query: CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие кнопки для подачи заявки на участие в розыгрыше."""
    drawing_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id

    # Проверяем, не участвует ли уже пользователь в данном розыгрыше
    if user_participates_in_drawing(user_id, drawing_id):
        await callback_query.message.answer("Вы уже подали заявку на участие в этом розыгрыше.")
        return

    # Создаем заявку на участие
    try:
        create_application(user_id, drawing_id)
    except ValueError as e:
        await callback_query.message.answer(str(e))
        return

    # Получаем название розыгрыша для сообщения
    drawing = get_drawing_by_id(drawing_id)
    drawing_title = drawing[0] if drawing else "Неизвестный"

    # Удаляем сообщение с клавиатурой
    await callback_query.message.delete()

    # Отправляем короткое сообщение пользователю
    await callback_query.message.answer(
        f"Отлично! Для участия в розыгрыше \"{drawing_title}\" пришлите один корректный скриншот."
    )

    # Сохраняем ID розыгрыша в контекст состояния
    await state.update_data(selected_drawing_id=drawing_id)
    await state.set_state(ApplicationForm.WAITING_FOR_SCREEN)


async def view_drawing_info(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(previous_menu="draws_menu")

    drawing_id = int(callback_query.data.split("_")[-1])
    # Получаем информацию о розыгрыше через метод репозитория
    drawing = get_drawing_by_id(drawing_id)

    if not drawing:
        await callback_query.message.answer("Информация о выбранном розыгрыше не найдена.")
        return

    # Форматируем даты
    start_date = datetime.strptime(drawing[2], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y") if drawing[2] else "Не указана"
    end_date = datetime.strptime(drawing[3], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y") if drawing[3] else "Не указана"

    # Формируем сообщение
    info_message = (
        f"Название: {drawing[0]}\n"
        f"Описание: {drawing[1]}\n"
        f"Дата начала: {start_date}\n"
        f"Дата окончания: {end_date}"
    )

    # Отправляем сообщение с информацией и кнопками
    await callback_query.message.edit_text(info_message, reply_markup=create_drawing_info_buttons(drawing_id))


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
    payment_confirmed = status_counts.get('payment_confirmed', 0)
    payment_reject = status_counts.get('payment_reject', 0)

    if not drawing:
        await callback_query.message.answer("Информация о выбранном розыгрыше не найдена.")
        return

    # Преобразуем строки в datetime, если они существуют
    start_date = datetime.strptime(drawing['start_date'], "%Y-%m-%d %H:%M:%S").strftime('%d.%m.%Y') if drawing['start_date'] else "Не указана"
    end_date = datetime.strptime(drawing['end_date'], "%Y-%m-%d %H:%M:%S").strftime('%d.%m.%Y') if drawing['end_date'] else "Не указана"

    info_message = (
        f"```\n"
        f"Название: {drawing['title']}\n"
        f"Описание: {drawing['description']}\n"
        f"Дата начала:                  {start_date}\n"
        f"Дата окончания:               {end_date}\n\n"
        f"Общая статистика заявок:\n"
        f"  Количество участников:      {participants_count}\n"
        f"  Ожидают проверки:           {pending}\n"
        f"  Одобрено:                   {approved}\n"
        f"  Отклонено:                  {rejected}\n"
        f"  Ожидают проверки оплаты:    {payment_pending}\n"
        f"  Подтверждено оплата:        {payment_confirmed}\n"
        f"  Оплата отклонена:           {payment_reject}\n"
        f"```"
    )

    await update_or_send_callback_message(callback_query, info_message, reply_markup=create_check_buttons(drawing_id), parse_mode="Markdown")
