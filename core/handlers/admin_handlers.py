import os
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile

from core.db.applications_crud import update_application_status, \
    increase_attempts, delete_application, get_application_by_user_and_drawing, get_participants_by_status
from core.db.drawings_crud import create_new_drawing, update_drawings_status, update_drawing_end_date, \
    get_completed_drawings, get_drawings_by_status, set_winners_count_in_db, get_winners, get_winners_count, \
    set_drawing_status, get_drawing_by_id
from core.db.winners_crud import add_winner
from core.handlers.application_handlers import show_screenshot_review
from core.handlers.drawing_handlers import show_drawing_summary
from core.keyboards.admin_inline import generate_admin_menu_keyboard, cancel_button_keyboard, \
    generate_winner_selection_keyboard
from core.keyboards.app_inline import create_back_only_keyboard
from core.keyboards.drawing_inline import generate_drawings_list_keyboard, generate_drawings_keyboard, \
    generate_complete_drawing_keyboard, generate_completed_drawings_list_keyboard, generate_cancel_drawing_keyboard, \
    generate_single_drawing_keyboard
from core.utils.menu_utils import update_or_send_message, update_or_send_callback_message
from core.utils.stateform import ApplicationForm, NewDrawingState, ExtendDrawingState
from core.keyboards.inline import admin_keyboard
from config import ADMIN_ID


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
    draws_status_dict = update_drawings_status()
    upcoming_count = draws_status_dict['upcoming']
    active_count = draws_status_dict['active']
    ready_to_draw_count = draws_status_dict['ready_to_draw']
    completed = draws_status_dict['completed']

    await update_or_send_message(
        message=message,
        text=(
            f"Админ-панель:\n\n"
            f"Предстоящие розыгрыши:          {upcoming_count}\n"
            f"Активные розыгрыши:                 {active_count}\n"
            f"В ожидании розыгрыши:             {ready_to_draw_count}\n"
            f"Завершенные розыгрыши:          {completed}\n\n"
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

    # elif query.data == "end_draw":
    #     # Получаем список активных и предстоящих розыгрышей
    #     drawings = get_drawings_by_status(['ready_to_draw'])
    #     if not drawings:
    #         await query.message.answer("На данный момент нет активных или предстоящих розыгрышей.")
    #         return
    #     # Отправляем инлайн-клавиатуру с розыгрышами
    #     await update_or_send_callback_message(
    #         callback_query=query,
    #         text="Выберите розыгрыш который хотите завершить:",
    #         reply_markup=generate_drawings_keyboard(drawings)
    #     )

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

        await state.update_data(end_date=end_date)
        await state.set_state(NewDrawingState.max_participants)  # Переход к следующему состоянию
        await message.answer("Введите максимальное количество участников (число от 1 до 1000):", reply_markup=cancel_button_keyboard())
    except ValueError:
        await message.answer("Некорректный формат даты. Попробуйте снова (dd.mm.yyyy):", reply_markup=cancel_button_keyboard())

# Шаг 5: Ввод максимального количества участников
async def set_drawing_max_participants(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде.")
        await state.clear()
        return

    try:
        max_participants = int(message.text)
        if max_participants < 1 or max_participants > 1000:
            await message.answer("Количество участников должно быть от 1 до 1000. Попробуйте снова:", reply_markup=cancel_button_keyboard())
            return

        data = await state.get_data()
        
        # Сохраняем данные и создаем новый розыгрыш
        create_new_drawing(
            title=data["title"],
            description=data["description"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            max_participants=max_participants,
            status="upcoming"
        )

        await message.answer("Новый розыгрыш успешно создан!")
        await state.clear()  # Завершение состояния после создания
    except ValueError:
        await message.answer("Некорректный формат числа. Попробуйте снова:", reply_markup=cancel_button_keyboard())

async def cancel_creation(callback_query: CallbackQuery, state: FSMContext, bot: Bot):
    """Отменяет процесс создания розыгрыша и очищает состояние."""
    await state.clear()
    await show_admin_panel(callback_query.message, state)

async def show_active_draws(callback_query: CallbackQuery, state: FSMContext):
    """Отображает список активных и ожидающих розыгрышей (в т.ч. для продления)."""
    await state.update_data(previous_menu="active_draws")
    update_drawings_status()

    drawings = get_drawings_by_status(['upcoming', 'active', 'ready_to_draw'])
    if not drawings:
        await callback_query.message.edit_text(
            "Нет активных розыгрышей.",
            reply_markup=generate_drawings_list_keyboard([], show_back_button=True)
        )
        return

    await update_or_send_callback_message(
        callback_query=callback_query,
        text="Розыгрыши (активные и ожидающие завершения):",
        reply_markup=generate_drawings_list_keyboard(drawings, show_back_button=True)
    )


async def start_extend_drawing(callback_query: CallbackQuery, state: FSMContext):
    """Запускает продление розыгрыша — ввод новой даты окончания."""
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("Нет доступа.", show_alert=True)
        return

    drawing_id = int(callback_query.data.split("_")[-1])
    drawing = get_drawing_by_id(drawing_id)
    if not drawing:
        await callback_query.answer("Розыгрыш не найден.", show_alert=True)
        return

    if drawing["status"] == "completed":
        await callback_query.answer("Завершённый розыгрыш продлить нельзя.", show_alert=True)
        return

    await state.update_data(extend_drawing_id=drawing_id)
    await state.set_state(ExtendDrawingState.waiting_end_date)
    current_end = datetime.strptime(drawing["end_date"], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
    await callback_query.message.answer(
        f"Розыгрыш: {drawing['title']}\n"
        f"Текущая дата окончания: {current_end}\n\n"
        f"Введите новую дату окончания (dd.mm.yyyy), позже сегодняшнего дня:",
        reply_markup=cancel_button_keyboard(),
    )
    await callback_query.answer()


async def set_extend_drawing_end_date(message: Message, state: FSMContext):
    """Сохраняет новую дату окончания и возвращает розыгрыш в active при необходимости."""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде.")
        await state.clear()
        return

    data = await state.get_data()
    drawing_id = data.get("extend_drawing_id")
    if not drawing_id:
        await message.answer("Сессия продления истекла. Откройте розыгрыш снова через /admin.")
        await state.clear()
        return

    drawing = get_drawing_by_id(drawing_id)
    if not drawing:
        await message.answer("Розыгрыш не найден.")
        await state.clear()
        return

    try:
        new_end_date = datetime.strptime(message.text.strip(), "%d.%m.%Y").replace(
            hour=23, minute=59, second=59
        )
    except ValueError:
        await message.answer(
            "Некорректный формат даты. Попробуйте снова (dd.mm.yyyy):",
            reply_markup=cancel_button_keyboard(),
        )
        return

    if drawing["start_date"]:
        start_date = datetime.strptime(drawing["start_date"], "%Y-%m-%d %H:%M:%S")
        if new_end_date <= start_date:
            await message.answer(
                "Дата окончания должна быть позже даты начала. Попробуйте снова:",
                reply_markup=cancel_button_keyboard(),
            )
            return

    if new_end_date <= datetime.now():
        await message.answer(
            "Дата окончания должна быть в будущем. Попробуйте снова:",
            reply_markup=cancel_button_keyboard(),
        )
        return

    update_drawing_end_date(drawing_id, new_end_date)
    update_drawings_status()
    drawing = get_drawing_by_id(drawing_id)

    status_labels = {
        "active": "активный",
        "upcoming": "предстоящий",
        "ready_to_draw": "ожидает розыгрыша",
        "completed": "завершён",
    }
    status_text = status_labels.get(drawing["status"], drawing["status"])

    await message.answer(
        f"Розыгрыш «{drawing['title']}» продлён до {new_end_date.strftime('%d.%m.%Y')}.\n"
        f"Статус в БД: {status_text}."
    )
    await state.clear()

async def show_completed_draws(callback_query: CallbackQuery):
    """Отображает список завершенных розыгрышей."""
    print("Отображение всех завершенных розыгрышей")
    drawings = get_completed_drawings()  # Предположим, метод возвращает список завершенных розыгрышей
    if not drawings:
        await callback_query.message.edit_text(
            "Нет завершенных розыгрышей.",
            reply_markup=generate_drawings_list_keyboard([], show_back_button=True)
        )
        return

    await callback_query.message.edit_text(
        "Завершенные розыгрыши:",
        reply_markup=generate_completed_drawings_list_keyboard(drawings, show_back_button=True)
    )


async def approve_screenshot(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    """Обрабатывает одобрение скриншота и обновляет статус заявки на 'approved'."""
    drawing_id, participant_index = map(int, callback_query.data.split("_")[2:])
    participant = get_participants_by_status(drawing_id, 'pending')[participant_index]
    update_application_status(participant['application_id'], status="payment_pending")
    await bot.send_message(
        participant['telegram_id'],
        "Ваша заявка одобрена",
        reply_markup=generate_single_drawing_keyboard(drawing_id),
    )
    await show_screenshot_review(callback_query, callback_query.bot, state, participant_index)
    await callback_query.answer()

async def reject_screenshot(callback_query: CallbackQuery, state: FSMContext):
    """Обрабатывает отклонение скриншота и обновляет статус заявки на 'rejected'."""
    drawing_id, participant_index = map(int, callback_query.data.split("_")[2:])
    participants = get_participants_by_status(drawing_id, 'pending')

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
        # Аннулируем заявку (меняем статус на completed) и удаляем фотографию
        photo_path = os.path.abspath(f"images/application/{telegram_id}_{drawing_id}.jpg")
        update_application_status(application_id, status="completed")

        # Удаляем фотографию, если она существует
        if os.path.exists(photo_path):
            os.remove(photo_path)

        await callback_query.bot.send_message(
            chat_id=telegram_id,
            text="Ваша заявка была аннулирована, так как вы не выполнили условия конкурса."
        )

        # Проверяем, есть ли еще участники
        remaining_participants = get_participants_by_status(drawing_id, 'pending')
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


async def set_winners_count(query: CallbackQuery):
    """Устанавливает количество победителей для розыгрыша."""
    try:
        # Шаг 1: Выводим исходные данные
        print(f"Received callback_data: {query.data}")

        # Шаг 2: Разделяем данные
        parts = query.data.split("_")
        print(f"Split callback_data: {parts}")

        # Проверяем корректность длины
        if len(parts) < 4:
            raise ValueError("Некорректный формат callback_data")

        # Извлекаем данные
        drawing_id = int(parts[-2])  # Предпоследний элемент — drawing_id
        count = int(parts[-1])  # Последний элемент — count
        print(f"Parsed drawing_id: {drawing_id}, count: {count}")

        # Шаг 3: Обновляем количество победителей в БД
        set_winners_count_in_db(drawing_id, count)
        print(f"Winners count set to: {count} for drawing_id: {drawing_id}")

        # Шаг 4: Отвечаем и обновляем интерфейс
        await query.answer(f"Количество победителей установлено: {count}.")

        # 🚀 **Передаём drawing_id напрямую, чтобы избежать ошибки!**
        await show_drawing_summary(query, None, drawing_id=drawing_id)

    except ValueError as e:
        print(f"ValueError: {e}")
        await query.answer(f"Ошибка данных: {e}. Попробуйте снова.", show_alert=True)

    except Exception as e:
        print(f"Unexpected error: {e}")
        await query.answer(f"Произошла непредвиденная ошибка: {e}.", show_alert=True)


async def select_winners(callback_query: CallbackQuery, bot: Bot, state: FSMContext, participant_index: int = 0):
    """Начинает процесс выбора победителей."""
    await state.update_data(previous_menu="drawing_info")

    # Получаем ID розыгрыша
    drawing_id = int(callback_query.data.split("_")[-1])

    # ✅ Получаем участников и победителей
    participants = get_participants_by_status(drawing_id, status="payment_confirmed")
    print(f"DEBUG: Participants (drawing {drawing_id}): {participants}")

    winners = get_winners(drawing_id)
    winner_user_ids = {w['user_id'] for w in winners}

    # ✅ Исключаем уже выбранных победителей из пагинации
    remaining_participants = [p for p in participants if p['user_id'] not in winner_user_ids]

    total_participants = len(remaining_participants)
    winner_count = get_winners_count(drawing_id)

    print(f'Всего участников: {total_participants}, Нужно выбрать: {winner_count}, Уже выбрано: {len(winners)}')

    # ✅ Если участников не осталось — все победители выбраны либо никого нельзя выбрать
    if total_participants == 0:
        # Формируем список победителей для отображения
        winners_lines = []
        for i, w in enumerate(winners):
            alias = w.get('telegram_alias')
            if alias:
                winners_lines.append(f"{i + 1}. [@{alias}](tg://user?id={w['telegram_id']})")
            else:
                winners_lines.append(f"{i + 1}. [{w['telegram_id']}](tg://user?id={w['telegram_id']})")
        
        winners_list = "\n".join(winners_lines) if winners_lines else "—"
        
        message_text = (
            f"✅ Все доступные участники уже выбраны победителями. Завершите розыгрыш.\n\n"
            f"🏆 **Победители:**\n{winners_list}"
        )
        
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=message_text,
            reply_markup=generate_complete_drawing_keyboard(drawing_id),
            parse_mode="Markdown"
        )
        return

    # Проверяем, выбрано ли нужное количество победителей
    if len(winners) == winner_count:
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text="✅ Все победители выбраны! Завершите розыгрыш.",
            reply_markup=generate_complete_drawing_keyboard(drawing_id)
        )
        return

    # Проверяем корректность participant_index
    if participant_index < 0 or participant_index >= total_participants:
        participant_index = 0

    # Получаем текущего участника из оставшихся
    participant = remaining_participants[participant_index]
    print(f'{participant_index=}')
    print(f'{participant=}')
    user_id = participant["user_id"]
    telegram_id = participant["telegram_id"]
    photo_path = os.path.abspath(f"images/application/{telegram_id}_{drawing_id}.jpg")

    # ✅ Удаляем старое сообщение перед отправкой нового (Только если есть участники)
    try:
        await callback_query.message.delete()
    except TelegramBadRequest:
        print("⚠️ Ошибка: Сообщение уже удалено.")

    # ✅ Отправляем новое сообщение с фото
    photo = FSInputFile(photo_path) if os.path.exists(photo_path) else None
    # Формируем отображение имени участника: alias если есть, иначе tg id
    participant_alias = participant.get("telegram_alias")
    participant_display = (
        f"[@{participant_alias}](tg://user?id={telegram_id})"
        if participant_alias else f"[{telegram_id}](tg://user?id={telegram_id})"
    )

    winners_lines = []
    for i, w in enumerate(winners):
        alias = w.get('telegram_alias')
        if alias:
            winners_lines.append(f"{i + 1}. [@{alias}](tg://user?id={w['telegram_id']})")
        else:
            winners_lines.append(f"{i + 1}. [{w['telegram_id']}](tg://user?id={w['telegram_id']})")

    message_text = (
        f"🎯 **Выбор победителей**\n\n"
        f"📌 Участник {participant_index + 1} из {total_participants}\n"
        f"👤 Пользователь: {participant_display}\n\n"
        "🏆 **Победители:**\n" + ("\n".join(winners_lines) if winners_lines else "—")
    )

    if photo:
        await bot.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=photo,
            caption=message_text,
            parse_mode="Markdown",
            reply_markup=generate_winner_selection_keyboard(drawing_id, participant_index, total_participants, user_id)
        )
    else:
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=f"⚠️ Фото участника отсутствует.\n\n{message_text}",
            parse_mode="Markdown",
            reply_markup=generate_winner_selection_keyboard(drawing_id, participant_index, total_participants, user_id)
        )

    await callback_query.answer()


async def next_participant(query: CallbackQuery, state: FSMContext):
    """Переход к следующему участнику."""
    print(f"Received callback_data (next): {query.data}")

    parts = query.data.split("_")
    if len(parts) < 4:
        print("❌ Ошибка: Некорректный формат callback_data")
        await query.answer("Ошибка: Некорректные данные.", show_alert=True)
        return

    _, _, participant_index, drawing_id = parts
    drawing_id = int(drawing_id)
    participant_index = int(participant_index) + 1  # Увеличиваем индекс
    print(f'{participant_index=}')

    await select_winners(query, query.message.bot, state, participant_index)


async def prev_participant(query: CallbackQuery, state: FSMContext):
    """Переход к предыдущему участнику."""
    print(f"Received callback_data (prev): {query.data}")

    parts = query.data.split("_")
    if len(parts) < 4:
        print("❌ Ошибка: Некорректный формат callback_data")
        await query.answer("Ошибка: Некорректные данные.", show_alert=True)
        return

    _, _, participant_index, drawing_id = parts
    drawing_id = int(drawing_id)
    participant_index = int(participant_index) - 1  # Уменьшаем индекс

    await select_winners(query, query.message.bot, state, participant_index)


async def set_winner(query: CallbackQuery, bot: Bot, state: FSMContext):
    """Делает текущего участника победителем."""

    print(f"🔍 DEBUG: set_winner - НАЧАЛО ФУНКЦИИ - ПЕРВАЯ СТРОКА")
    print(f"🔍 DEBUG: set_winner - НАЧАЛО ФУНКЦИИ")
    print(f"Received callback_data: {query.data}")  # Отладка

    parts = query.data.split("_")
    print(f"Split callback_data: {parts}")

    if len(parts) < 4:
        print("Ошибка: Недостаточно данных в callback_data")
        await query.answer("Ошибка обработки запроса.", show_alert=True)
        return

    _, _, user_id, drawing_id = parts
    drawing_id = int(drawing_id)
    user_id = int(user_id)  # Теперь работаем с user_id
    
    print(f"🔍 DEBUG: user_id={user_id}, drawing_id={drawing_id}")

    # Получаем участника по user_id
    print(f"🔍 DEBUG: Вызываем get_participants_by_status")
    participants = get_participants_by_status(drawing_id, status="payment_confirmed")
    print(f"🔍 DEBUG: Получены участники: {participants}")
    
    participant = next((p for p in participants if p["user_id"] == user_id), None)
    print(f"🔍 DEBUG: Найденный участник: {participant}")

    if not participant:
        print(f"❌ Ошибка: Не найден участник с user_id={user_id}")
        await query.answer("Ошибка: участник не найден.", show_alert=True)
        return

    # Получаем информацию о розыгрыше для уведомления
    print(f"🔍 DEBUG: Вызываем get_drawing_by_id")
    drawing = get_drawing_by_id(drawing_id)
    print(f"🔍 DEBUG: Получена информация о розыгрыше: {drawing}")
    
    drawing_title = drawing['title'] if drawing else "розыгрыше"
    print(f"🔍 DEBUG: Название розыгрыша: {drawing_title}")
    
    # Сначала пытаемся добавить победителя в БД. Сообщение отправляем ТОЛЬКО при успешной вставке,
    # чтобы избежать дублей при повторных нажатиях.
    try:
        add_winner(drawing_id, participant)
        await query.answer("✅ Участник добавлен в победители.")

        # Отправляем уведомление победителю только после успешного добавления
        winner_telegram_id = participant['telegram_id']
        winner_message = (
            f"🎉 Поздравляем! Вы стали победителем в розыгрыше «{drawing_title}»! 🏆\n\n"
            f"Мы свяжемся с вами для получения приза."
        )

        print(f"🔍 DEBUG: Попытка отправки уведомления победителю {winner_telegram_id}")
        print(f"🔍 DEBUG: Сообщение: {winner_message}")

        try:
            await bot.send_message(chat_id=winner_telegram_id, text=winner_message)
            print(f"✅ Уведомление отправлено победителю {winner_telegram_id}")
        except Exception as e:
            print(f"⚠️ Не удалось отправить уведомление победителю {winner_telegram_id}: {e}")
            print(f"🔍 DEBUG: Тип ошибки: {type(e).__name__}")
            print(f"🔍 DEBUG: Детали ошибки: {str(e)}")

    except ValueError as e:
        # Уже добавлен в победители — уведомление НЕ отправляем повторно
        print(f"Ошибка: {e}")
        await query.answer(f"⚠️ {e}", show_alert=True)

    # Переход к следующему шагу выбора победителей
    print(f"🔍 DEBUG: set_winner - КОНЕЦ ФУНКЦИИ, вызываем select_winners")
    await select_winners(query, bot, state)

async def complete_drawing(query: CallbackQuery):
    """Завершает розыгрыш."""
    drawing_id = int(query.data.split("_")[-1])

    # Получаем информацию о розыгрыше
    drawing = get_drawing_by_id(drawing_id)
    drawing_title = drawing['title'] if drawing else "розыгрыше"

    # Получаем всех победителей
    winners = get_winners(drawing_id)
    print(f"🔍 DEBUG: Найдено победителей: {len(winners)}")
    for winner in winners:
        print(f"🔍 DEBUG: Победитель: {winner}")

    # Получаем всех участников со статусом "payment_confirmed"
    all_participants = get_participants_by_status(drawing_id, status="payment_confirmed")
    winner_telegram_ids = {winner['telegram_id'] for winner in winners}
    print(f"🔍 DEBUG: Всего участников: {len(all_participants)}")
    print(f"🔍 DEBUG: ID победителей: {winner_telegram_ids}")

    # Уведомления победителям при завершении НЕ отправляем, чтобы не дублировать с сообщением из set_winner

    # Отправляем уведомления участникам, которые не стали победителями
    for participant in all_participants:
        if participant['telegram_id'] not in winner_telegram_ids:
            try:
                participant_message = f"📢 Розыгрыш «{drawing_title}» завершен!\n\nК сожалению, вы не стали победителем в этом розыгрыше. Не расстраивайтесь, участвуйте в следующих розыгрышах! 🍀"
                print(f"🔍 DEBUG: Отправка уведомления участнику {participant['telegram_id']}")
                print(f"🔍 DEBUG: Сообщение: {participant_message}")
                
                await query.bot.send_message(
                    chat_id=participant['telegram_id'],
                    text=participant_message
                )
                print(f"✅ Уведомление о завершении отправлено участнику {participant['telegram_id']}")
            except Exception as e:
                print(f"⚠️ Не удалось отправить уведомление участнику {participant['telegram_id']}: {e}")
                print(f"🔍 DEBUG: Тип ошибки: {type(e).__name__}")
                print(f"🔍 DEBUG: Детали ошибки: {str(e)}")

    # Обновляем статус розыгрыша
    set_drawing_status(drawing_id, "completed")

    await query.message.edit_text("Розыгрыш успешно завершен!")
