import os
from datetime import datetime

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from IvaslaviaBot.core.db.applications_crud import get_confirmed_participants, update_application_status, \
    get_pending_participants, increase_attempts, delete_application, get_application_by_user_and_drawing
from IvaslaviaBot.core.db.drawings_crud import create_new_drawing, update_drawings_status, \
    get_completed_drawings, get_upcoming_and_active_drawings
from IvaslaviaBot.core.handlers.application_handlers import show_screenshot_review
from IvaslaviaBot.core.keyboards.admin_inline import generate_admin_menu_keyboard, cancel_button_keyboard, \
    create_back_button_keyboard
from IvaslaviaBot.core.keyboards.app_inline import create_back_only_keyboard
from IvaslaviaBot.core.keyboards.drawing_inline import generate_drawings_list_keyboard
from IvaslaviaBot.core.utils.menu_utils import update_or_send_message, update_or_send_callback_message
from IvaslaviaBot.core.utils.stateform import ApplicationForm, NewDrawingState
from IvaslaviaBot.core.keyboards.inline import admin_keyboard
from IvaslaviaBot.config import ADMIN_ID


# Проверка, является ли пользователь администратором
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# Команда /admin
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде.")
        return

    # Вызов метода для отображения админ-панели
    await show_admin_panel(message, state)

async def show_admin_panel(message, state):
    """Выводит админ-панель с информацией о розыгрышах и кнопками управления."""
    await state.update_data(previous_menu="admin_panel")

    # Обновляем статусы розыгрышей
    active_count, upcoming_count = update_drawings_status()
    await update_or_send_message(
        message=message,
        text=(
            f"Админ-панель:\n\n"
            f"Активные розыгрыши:          {active_count}\n"
            f"Предстоящие розыгрыши:   {upcoming_count}\n\n"
            "Выберите действие:"
        ),
        reply_markup=admin_keyboard()
    )

# Проверка кнопок Начать, управлять и закончить розыгрыш
async def handle_admin_callback(query: CallbackQuery, state: FSMContext):
    await state.update_data(previous_menu="admin_panel")

    if query.data == "start_draw":
        # Переход к созданию нового розыгрыша
        await state.set_state(NewDrawingState.title)
        await query.message.edit_text("Введите название розыгрыша:", reply_markup=cancel_button_keyboard())

    elif query.data == "manage_draw":
        await update_or_send_callback_message(
            callback_query=query,
            text="Выберите категорию розыгрышей:",
            reply_markup=generate_admin_menu_keyboard()
        )

    elif query.data == "end_draw":
        await query.message.answer("Розыгрыш завершен.")
        # Логика для завершения розыгрыша

    await query.answer()  # Закрываем уведомление в Telegram

# Шаг 1: Ввод названия
async def set_drawing_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(NewDrawingState.description)  # Переход к следующему состоянию
    await message.answer("Введите описание розыгрыша:", reply_markup=cancel_button_keyboard())

# Шаг 2: Ввод описания
async def set_drawing_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(NewDrawingState.start_date)  # Переход к следующему состоянию
    await message.answer("Введите дату начала розыгрыша (в формате dd.mm.yyyy):", reply_markup=cancel_button_keyboard())

# Шаг 3: Ввод даты начала
async def set_drawing_start_date(message: Message, state: FSMContext):
    try:
        # Ожидаем ввод в формате dd.mm.yyyy
        start_date = datetime.strptime(message.text, "%d.%m.%Y")
        await state.update_data(start_date=start_date)
        await state.set_state(NewDrawingState.end_date)  # Переход к следующему состоянию
        await message.answer("Введите дату окончания розыгрыша (в формате dd.mm.yyyy):", reply_markup=cancel_button_keyboard())
    except ValueError:
        await message.answer("Некорректный формат даты. Попробуйте снова (dd.mm.yyyy):", reply_markup=cancel_button_keyboard())

# Шаг 4: Ввод даты окончания
async def set_drawing_end_date(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде.")
        await state.clear()  # Завершение текущего состояния
        return

    try:
        # Ожидаем ввод в формате dd.mm.yyyy
        end_date = datetime.strptime(message.text, "%d.%m.%Y")
        data = await state.get_data()

        if end_date <= data["start_date"]:
            await message.answer("Дата окончания должна быть позже даты начала. Попробуйте снова:", reply_markup=cancel_button_keyboard())
            return

        # Сохраняем данные и создаем новый розыгрыш
        create_new_drawing(
            title=data["title"],
            description=data["description"],
            start_date=data["start_date"],
            end_date=end_date,
            status="upcoming"  # или "active", в зависимости от логики
        )

        await message.answer("Новый розыгрыш успешно создан!")
        await state.clear()  # Завершение состояния после создания
    except ValueError:
        await message.answer("Некорректный формат даты. Попробуйте снова (dd.mm.yyyy):", reply_markup=cancel_button_keyboard())

async def cancel_creation(callback_query: CallbackQuery, state: FSMContext, bot: Bot):
    """Отменяет процесс создания розыгрыша и очищает состояние."""
    await state.clear()
    await show_admin_panel(callback_query.message, state)

async def show_active_draws(callback_query: CallbackQuery, state: FSMContext):
    """Отображает список активных розыгрышей."""
    await state.update_data(previous_menu="active_draws")

    drawings = get_upcoming_and_active_drawings()  # Предположим, метод возвращает список активных розыгрышей
    if not drawings:
        await callback_query.message.edit_text(
            "Нет активных розыгрышей.",
            reply_markup=generate_drawings_list_keyboard([], show_back_button=True)
        )
        return

    await update_or_send_callback_message(
        callback_query=callback_query,
        text="Активные розыгрыши:",
        reply_markup=generate_drawings_list_keyboard(drawings, show_back_button=True)
    )

#TODO Доделать функционал
async def show_completed_draws(callback_query: CallbackQuery):
    """Отображает список завершенных розыгрышей."""
    drawings = get_completed_drawings()  # Предположим, метод возвращает список завершенных розыгрышей
    if not drawings:
        await callback_query.message.edit_text(
            "Нет завершенных розыгрышей.",
            reply_markup=generate_drawings_list_keyboard([], show_back_button=True)
        )
        return

    await callback_query.message.edit_text(
        "Завершенные розыгрыши:",
        reply_markup=generate_drawings_list_keyboard(drawings, show_back_button=True)
    )

async def show_awaiting_draw(callback_query: CallbackQuery):
    """Отображает список участников, ожидающих розыгрыша, со статусом 'payment_confirmed'."""
    drawing_id = int(callback_query.data.split("_")[-1])
    participants = get_confirmed_participants(drawing_id)  # Получаем список участников с подтвержденной оплатой

    # Формируем ответное сообщение
    if not participants:
        response = "Нет участников, ожидающих розыгрыша для этого розыгрыша."
    else:
        response = "Участники, ожидающие розыгрыша:\n"
        for participant in participants:
            response += f"ID участника: {participant['user_id']}\n"

    # Отправляем сообщение с кнопкой "Назад"
    await callback_query.message.edit_text(
        response,
        reply_markup=create_back_button_keyboard(callback_data=f"back_to_check_menu_{drawing_id}")
    )
    await callback_query.answer()

async def approve_screenshot(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    """Обрабатывает одобрение скриншота и обновляет статус заявки на 'approved'."""
    drawing_id, participant_index = map(int, callback_query.data.split("_")[2:])
    participant = get_pending_participants(drawing_id)[participant_index]
    update_application_status(participant['application_id'], status="payment_pending")
    payment_details = "Пожалуйста, оплатите участие по следующим реквизитам:\n[Ваши реквизиты]"
    await bot.send_message(participant['telegram_id'], "Ваша заявка одобрена. " + payment_details + '\nПосле оплаты, пришлите скриншот об оплате')
    await state.update_data(selected_drawing_id=drawing_id)
    await state.set_state(ApplicationForm.WAITING_FOR_PAYMENT_SCREEN)
    await show_screenshot_review(callback_query, callback_query.bot, state, participant_index)
    await callback_query.answer()

async def reject_screenshot(callback_query: CallbackQuery, state: FSMContext):
    """Обрабатывает отклонение скриншота и обновляет статус заявки на 'rejected'."""
    drawing_id, participant_index = map(int, callback_query.data.split("_")[2:])
    participants = get_pending_participants(drawing_id)

    if not participants:
        await callback_query.answer("Нет участников для проверки.", show_alert=True)
        return

    participant = participants[participant_index]
    application_id = participant['application_id']
    telegram_id = participant['telegram_id']

    # Увеличиваем количество попыток
    increase_attempts(application_id)
    # Получаем количество попыток
    application = get_application_by_user_and_drawing(participant['telegram_id'], drawing_id)
    attempts = application.get('attempts', 0)
    max_attempts = 3

    if attempts >= max_attempts:
        # Удаляем заявку и фотографию
        photo_path = os.path.abspath(f"images/application/{telegram_id}_{drawing_id}.jpg")
        delete_application(application_id)

        # Удаляем фотографию, если она существует
        if os.path.exists(photo_path):
            os.remove(photo_path)

        await callback_query.bot.send_message(
            chat_id=telegram_id,
            text="Ваша заявка была аннулирована, так как вы не выполнили условия конкурса."
        )

        # Проверяем, есть ли еще участники
        remaining_participants = get_pending_participants(drawing_id)
        if remaining_participants:
            await show_screenshot_review(callback_query, callback_query.bot, state, 0)
        else:
            await callback_query.message.edit_text(
                "Нет участников, ожидающих проверки скриншотов.",
                reply_markup=create_back_only_keyboard(drawing_id)
            )
    else:
        # Обновляем статус на "rejected" и уведомляем пользователя
        update_application_status(application_id, status="rejected")
        remaining_attempts = max_attempts - attempts
        await callback_query.bot.send_message(
            chat_id=telegram_id,
            text=f"Ваш скриншот не прошёл проверку.\nУ вас осталось {remaining_attempts} попыток загрузить новый скриншот."
        )
        await state.update_data(selected_drawing_id=drawing_id)
        await state.set_state(ApplicationForm.WAITING_FOR_SCREEN)

        # Переходим к следующему участнику или обновляем текущего
        await show_screenshot_review(callback_query, callback_query.bot, state, participant_index)

    await callback_query.answer()


async def next_screenshot(callback_query: CallbackQuery, state: FSMContext):
    """Переход к следующему скриншоту участника."""
    drawing_id, participant_index = map(int, callback_query.data.split("_")[2:])
    await show_screenshot_review(callback_query, callback_query.bot, state, participant_index + 1)
    await callback_query.answer()

async def prev_screenshot(callback_query: CallbackQuery, state: FSMContext):
    """Переход к предыдущему скриншоту участника."""
    drawing_id, participant_index = map(int, callback_query.data.split("_")[2:])
    await show_screenshot_review(callback_query, callback_query.bot, state, participant_index - 1)
    await callback_query.answer()
