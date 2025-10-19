from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram import Bot
import os

from core.db.applications_crud import update_application_status, get_application_by_user_and_drawing, \
    create_application, get_participants_by_status, increase_payment_attempts
from config import ADMIN_ID
from core.keyboards.admin_inline import create_screenshot_review_keyboard, create_payment_review_keyboard
from core.keyboards.app_inline import create_back_only_keyboard
from core.utils.menu_utils import update_or_send_callback_message


async def handle_screenshot(message: Message, state: FSMContext, bot: Bot):
    """Обрабатывает скриншот пользователя и сохраняет его в папку."""
    # Проверяем, что сообщение содержит изображение
    if not message.photo:
        await message.answer("Пожалуйста, отправьте одно изображение.")
        return

    # Получаем данные о выбранном розыгрыше из контекста состояния
    data = await state.get_data()
    drawing_id = data.get("selected_drawing_id")

    if not drawing_id:
        await message.answer("Произошла ошибка, розыгрыш не найден. Попробуйте снова.")
        return

    # Проверяем, есть ли существующая заявка пользователя на этот розыгрыш
    application = get_application_by_user_and_drawing(message.from_user.id, drawing_id)

    if application:
        if application["status"] == "rejected":
            # Если статус "rejected", обновляем скриншот и статус
            update_application_status(application["application_id"], status="pending")
    else:
        # Создаем новую заявку, если ее еще нет
        create_application(message.from_user.id, drawing_id)

    # Получаем фотографию в наилучшем качестве
    photo = message.photo[-1]

    # Определяем путь для сохранения изображения
    user_id = message.from_user.id
    file_path = f"images/application/{user_id}_{drawing_id}.jpg"

    # Убедимся, что папка существует
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Скачиваем файл с помощью объекта бота
    file = await bot.get_file(photo.file_id)
    await bot.download_file(file.file_path, destination=file_path)

    # Отправляем сообщение об успешной загрузке
    await message.answer("Ваш скриншот был успешно сохранен и ожидает проверки.")
    await state.clear()  # Завершаем состояние после обработки


async def show_screenshot_review(callback_query: CallbackQuery, bot: Bot, state: FSMContext, participant_index: int = 0):
    """Показывает скриншот участника и предоставляет кнопки для управления."""
    # Сохраняем контекст предыдущего меню
    await state.update_data(previous_menu="drawing_info")

    # Получаем ID розыгрыша и участников
    drawing_id = int(callback_query.data.split("_")[2])
    participants = get_participants_by_status(drawing_id, 'pending')
    total_participants = len(participants)

    # Если нет участников
    if not participants:
        await update_or_send_callback_message(
            callback_query=callback_query,
            text="Нет участников, ожидающих проверки скриншотов.",
            reply_markup=create_back_only_keyboard(drawing_id)
        )
        await callback_query.answer()
        return

    # Если текущий индекс выходит за границы, отображаем первого участника
    if participant_index < 0 or participant_index >= total_participants:
        participant_index = 0

    # Получаем текущего участника
    participant = participants[participant_index]
    telegram_id = participant['telegram_id']
    photo_path = os.path.abspath(f"images/application/{telegram_id}_{drawing_id}.jpg")

    # Проверяем существование файла
    if not os.path.exists(photo_path):
        await callback_query.message.edit_text(
            f"Скриншот для участника {participant_index + 1} отсутствует. Пожалуйста, проверьте данные.",
            reply_markup=create_back_only_keyboard(drawing_id)
        )
        await callback_query.answer()
        return

    # Отправляем скриншот и кнопки управления
    photo = FSInputFile(photo_path)
    await callback_query.message.delete()  # Удаляем предыдущее сообщение
    await bot.send_photo(
        chat_id=callback_query.message.chat.id,
        photo=photo,
        caption=(
            f"Участник {participant_index + 1} из {total_participants}:\n"
            f"Telegram ID: [{telegram_id}](tg://user?id={telegram_id})\n"
        ),
        parse_mode="Markdown",
        reply_markup=create_screenshot_review_keyboard(drawing_id, participant_index, total_participants)
    )
    await callback_query.answer()


async def handle_payment_screen(message: Message, state: FSMContext, bot: Bot):
    """Обрабатывает скриншот оплаты пользователя и сохраняет его в папку."""
    # Проверяем, что сообщение содержит изображение
    if not message.photo:
        await message.answer("Пожалуйста, отправьте одно изображение.")
        return

    # Получаем данные о выбранном розыгрыше из контекста состояния
    data = await state.get_data()
    drawing_id = data.get("selected_drawing_id")

    if not drawing_id:
        await message.answer("Произошла ошибка, розыгрыш не найден. Попробуйте снова.")
        return

    # Получаем фотографию в наилучшем качестве
    photo = message.photo[-1]

    # Определяем путь для сохранения изображения
    user_id = message.from_user.id
    file_path = f"images/payment/{user_id}_{drawing_id}.jpg"

    # Убедимся, что папка существует
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Скачиваем файл с помощью объекта бота
    file = await bot.get_file(photo.file_id)
    await bot.download_file(file.file_path, destination=file_path)

    # Отправляем сообщение об успешной загрузке
    await message.answer("Ваш скриншот оплаты был успешно сохранен и ожидает проверки.")

    # Обновляем статус заявки
    application = get_application_by_user_and_drawing(message.from_user.id, drawing_id)
    if application and application["status"] == "payment_pending":
        update_application_status(application["application_id"], status="payment_bill_loaded")

    await state.clear()  # Завершаем состояние после обработки


async def show_payment_review(callback_query: CallbackQuery, bot: Bot, state: FSMContext, participant_index: int = 0):
    """Показывает скриншот оплаты участника и предоставляет кнопки для управления."""
    await state.update_data(previous_menu="drawing_info")

    # Получаем ID розыгрыша и участников
    drawing_id = int(callback_query.data.split("_")[2])
    participants = get_participants_by_status(drawing_id, 'payment_bill_loaded')
    total_participants = len(participants)

    # Если нет участников
    if not participants:
        await update_or_send_callback_message(
            callback_query=callback_query,
            text="Нет участников, ожидающих проверки оплаты.",
            reply_markup=create_back_only_keyboard(drawing_id)
        )
        await callback_query.answer()
        return

    # Если текущий индекс выходит за границы, отображаем первого участника
    if participant_index < 0 or participant_index >= total_participants:
        participant_index = 0

    # Получаем текущего участника
    participant = participants[participant_index]
    telegram_id = participant['telegram_id']
    photo_path = os.path.abspath(f"images/payment/{telegram_id}_{drawing_id}.jpg")

    # Проверяем существование файла
    if not os.path.exists(photo_path):
        await callback_query.message.edit_text(
            f"Скриншот оплаты для участника {participant_index + 1} отсутствует. Пожалуйста, проверьте данные.",
            reply_markup=create_back_only_keyboard(drawing_id)
        )
        await callback_query.answer()
        return

    # Отправляем скриншот и кнопки управления
    photo = FSInputFile(photo_path)
    await callback_query.message.delete()
    await bot.send_photo(
        chat_id=callback_query.message.chat.id,
        photo=photo,
        caption=(
            f"Участник {participant_index + 1} из {total_participants}:\n"
            f"Telegram ID: [{telegram_id}](tg://user?id={telegram_id})\n"
        ),
        parse_mode="Markdown",
        reply_markup=create_payment_review_keyboard(drawing_id, participant_index, total_participants)
    )
    await callback_query.answer()

async def approve_payment(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    """Обрабатывает одобрение оплаты и обновляет статус заявки на 'payment_confirmed'."""
    drawing_id, participant_index = map(int, callback_query.data.split("_")[2:])
    participants = get_participants_by_status(drawing_id, 'payment_bill_loaded')

    if not participants:
        await callback_query.answer("Нет участников для проверки оплаты.", show_alert=True)
        return

    participant = participants[participant_index]
    update_application_status(participant['application_id'], status="payment_confirmed")
    await bot.send_message(
        chat_id=participant['telegram_id'],
        text="Ваша оплата подтверждена. Спасибо за участие! Ожидайте завершения розыгрыша."
    )

    # Переходим к следующему участнику или обновляем текущего
    await show_payment_review(callback_query, bot, state, participant_index)
    await callback_query.answer()

async def reject_payment(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    """Обрабатывает отклонение оплаты и обновляет статус заявки на 'payment_reject'."""
    drawing_id, participant_index = map(int, callback_query.data.split("_")[2:])
    participants = get_participants_by_status(drawing_id, 'payment_bill_loaded')

    if not participants:
        await callback_query.answer("Нет участников для проверки оплаты.", show_alert=True)
        return

    participant = participants[participant_index]
    application = get_application_by_user_and_drawing(participant['telegram_id'], drawing_id)
    if application: # Проверяем, что заявка найдена
        current_attempts_payment = application.get('attempts_payment', 0)
    else:
        current_attempts_payment = 0 # Если заявка не найдена, устанавливаем 0 попыток

    increase_payment_attempts(participant['application_id'])
    new_attempts_payment = current_attempts_payment + 1

    if new_attempts_payment >= 3:
        update_application_status(participant['application_id'], status="payment_reject")
        await bot.send_message(
            chat_id=participant['telegram_id'],
            text=f"Вы достигли максимального количества попыток подтверждения оплаты. Пожалуйста, обратитесь к [организатору](tg://user?id={ADMIN_ID}).",
            parse_mode="Markdown"
        )
    else:
        update_application_status(participant['application_id'], status="payment_pending") # Возвращаем статус на payment_pending
        await bot.send_message(
            chat_id=participant['telegram_id'],
            text=f"Ваша оплата была отклонена. У вас осталось {3 - new_attempts_payment} попыток. Пожалуйста, отправьте скриншот повторно, или свяжитесь с [организатором](tg://user?id={ADMIN_ID}) для уточнения причин.",
            parse_mode="Markdown"
        )

    # Переходим к следующему участнику или обновляем текущего
    await show_payment_review(callback_query, bot, state, participant_index)
    await callback_query.answer()

async def next_payment(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    """Переход к следующему скриншоту оплаты участника."""
    drawing_id, participant_index = map(int, callback_query.data.split("_")[2:])
    await show_payment_review(callback_query, bot, state, participant_index + 1)
    await callback_query.answer()

async def prev_payment(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    """Переход к предыдущему скриншоту оплаты участника."""
    drawing_id, participant_index = map(int, callback_query.data.split("_")[2:])
    await show_payment_review(callback_query, bot, state, participant_index - 1)
    await callback_query.answer()