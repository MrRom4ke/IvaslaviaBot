from datetime import datetime
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from IvaslaviaBot.core.db.applications_crud import get_applications_awaiting_review, get_applications_awaiting_payment
from IvaslaviaBot.core.db.drawings_crud import create_new_drawing, update_drawings_status, \
    get_completed_drawings, get_upcoming_and_active_drawings
from IvaslaviaBot.core.keyboards.admin_inline import generate_admin_menu_keyboard
from IvaslaviaBot.core.keyboards.drawing_inline import generate_drawings_list_keyboard
from IvaslaviaBot.core.utils.stateform import ApplicationForm, NewDrawingState
from IvaslaviaBot.core.keyboards.inline import admin_keyboard, call_operator_button
from IvaslaviaBot.config import ADMIN_ID


# Проверка, является ли пользователь администратором
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# Команда /admin
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде.")
        return
    
    # Обновляем статусы розыгрышей
    active_count, upcoming_count = update_drawings_status()

    # Выводим информацию о количестве активных и предстоящих розыгрышей
    await message.answer(
        f"Админ-панель:\n\n"
        f"Активные розыгрыши: {active_count}\n"
        f"Предстоящие розыгрыши: {upcoming_count}\n\n"
        "Выберите действие:",
        reply_markup=admin_keyboard()
    )

# Проверка кнопок Начать, управлять и закончить розыгрыш
async def handle_admin_callback(query: CallbackQuery, state: FSMContext):
    if query.data == "start_draw":
        # Переход к созданию нового розыгрыша
        await state.set_state(NewDrawingState.title)
        await query.message.answer("Введите название розыгрыша:")

    elif query.data == "manage_draw":
        await query.message.edit_text(
            "Управление розыгрышами\n-----\nВыберите категорию:",
            reply_markup=generate_admin_menu_keyboard()
        )
        # Логика для управления текущим розыгрышем

    elif query.data == "end_draw":
        await query.message.answer("Розыгрыш завершен.")
        # Логика для завершения розыгрыша

    await query.answer()  # Закрываем уведомление в Telegram


# Шаг 1: Ввод названия
async def set_drawing_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(NewDrawingState.description)  # Переход к следующему состоянию
    await message.answer("Введите описание розыгрыша:")

# Шаг 2: Ввод описания
async def set_drawing_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(NewDrawingState.start_date)  # Переход к следующему состоянию
    await message.answer("Введите дату начала розыгрыша (в формате dd.mm.yyyy):")

# Шаг 3: Ввод даты начала
async def set_drawing_start_date(message: Message, state: FSMContext):
    try:
        # Ожидаем ввод в формате dd.mm.yyyy
        start_date = datetime.strptime(message.text, "%d.%m.%Y")
        await state.update_data(start_date=start_date)
        await state.set_state(NewDrawingState.end_date)  # Переход к следующему состоянию
        await message.answer("Введите дату окончания розыгрыша (в формате dd.mm.yyyy):")
    except ValueError:
        await message.answer("Некорректный формат даты. Попробуйте снова (dd.mm.yyyy):")

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
            await message.answer("Дата окончания должна быть позже даты начала. Попробуйте снова:")
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
        await message.answer("Некорректный формат даты. Попробуйте снова (dd.mm.yyyy):")

async def admin_manage_draws(callback_query: CallbackQuery):
    """Отображает меню управления розыгрышами для администратора."""
    await callback_query.message.edit_text(
        "Управление розыгрышами\n-----\nВыберите категорию:",
        reply_markup=generate_admin_menu_keyboard()
    )

async def show_active_draws(callback_query: CallbackQuery):
    """Отображает список активных розыгрышей."""
    drawings = get_upcoming_and_active_drawings()  # Предположим, метод возвращает список активных розыгрышей
    if not drawings:
        await callback_query.message.edit_text("Нет активных розыгрышей.")
        return

    await callback_query.message.edit_text(
        "Активные розыгрыши:",
        reply_markup=generate_drawings_list_keyboard(drawings)
    )

async def show_completed_draws(callback_query: CallbackQuery):
    """Отображает список завершенных розыгрышей."""
    drawings = get_completed_drawings()  # Предположим, метод возвращает список завершенных розыгрышей
    if not drawings:
        await callback_query.message.edit_text("Нет завершенных розыгрышей.")
        return

    await callback_query.message.edit_text(
        "Завершенные розыгрыши:",
        reply_markup=generate_drawings_list_keyboard(drawings)
    )

#TODO Доделать функционал
async def check_screenshots(callback_query: CallbackQuery):
    """Обрабатывает нажатие кнопки 'Проверить скриншоты'."""
    drawing_id = int(callback_query.data.split("_")[-1])
    applications = get_applications_awaiting_review(drawing_id)

    if not applications:
        await callback_query.message.edit_text("Нет заявок, ожидающих проверки скриншотов для этого розыгрыша.")
        return

    response = "Заявки, ожидающие проверки скриншотов:\n"
    for app in applications:
        response += f"ID заявки: {app['application_id']}, Пользователь: {app['user_id']}\n"

    await callback_query.message.edit_text(response)

async def check_payments(callback_query: CallbackQuery):
    """Обрабатывает нажатие кнопки 'Проверить оплаты'."""
    drawing_id = int(callback_query.data.split("_")[-1])
    applications = get_applications_awaiting_payment(drawing_id)

    if not applications:
        await callback_query.message.edit_text("Нет заявок, ожидающих проверки оплаты для этого розыгрыша.")
        return

    response = "Заявки, ожидающие проверки оплаты:\n"
    for app in applications:
        response += f"ID заявки: {app['application_id']}, Пользователь: {app['user_id']}\n"

    await callback_query.message.edit_text(response)
