import asyncio
import logging

import httpx
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from v2.services.bot.app.core.config import settings
from v2.services.bot.app.services.file_storage import file_storage
from v2.services.bot.app.services.subscription_service import SubscriptionService

logging.basicConfig(level=logging.INFO)


class ParticipateState(StatesGroup):
    waiting_profile = State()
    waiting_payment = State()


dp = Dispatcher(storage=MemoryStorage())

# Инициализация сервиса проверки подписок
subscription_service = SubscriptionService(bot_token=settings.bot_token)


# Главное меню с inline-кнопками
def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Создает inline-клавиатуру главного меню."""
    keyboard = [
        [InlineKeyboardButton(text="🎲 Участвовать в розыгрыше", callback_data="menu_drawings")],
        [InlineKeyboardButton(text="📋 Мои заявки", callback_data="menu_my_apps")],
        [InlineKeyboardButton(text="👤 Вызвать оператора", callback_data="menu_operator")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_to_menu_button() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_main")]
    ])


def _drawings_keyboard(drawings: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=item['title'], callback_data=f"join_{item['id']}")]
        for item in drawings
    ]
    # Добавляем кнопку "Назад"
    rows.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Приветственное сообщение с главным меню."""
    welcome_text = (
        "👋 <b>Добро пожаловать в IvaslaviaBot!</b>\n"
        "🎉 Здесь вы можете участвовать в розыгрышах и выигрывать призы!"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=main_menu_keyboard())


# Обработка кнопки "Главное меню"
@dp.callback_query(lambda c: c.data == "menu_main")
async def callback_main_menu(callback: CallbackQuery) -> None:
    """Возврат в главное меню."""
    welcome_text = (
        "👋 <b>Добро пожаловать в IvaslaviaBot!</b>\n"
        "🎉 Здесь вы можете участвовать в розыгрышах и выигрывать призы!"
    )
    await callback.message.edit_text(welcome_text, parse_mode="HTML", reply_markup=main_menu_keyboard())
    await callback.answer()


# Обработка кнопки "Участвовать в розыгрыше"
@dp.callback_query(lambda c: c.data == "menu_drawings")
@dp.message(Command("drawings"))
async def cmd_drawings(message_or_callback) -> None:
    """Показать список активных розыгрышей."""
    # Определяем, это сообщение или callback
    is_callback = isinstance(message_or_callback, CallbackQuery)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{settings.admin_api_base_url}/drawings", params={"status": "active"})
            response.raise_for_status()
            drawings = response.json()
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to fetch drawings: %s", exc)
        text = "❌ Не удалось получить список розыгрышей. Попробуйте позже."
        if is_callback:
            await message_or_callback.message.edit_text(text, reply_markup=back_to_menu_button())
            await message_or_callback.answer()
        else:
            await message_or_callback.answer(text, reply_markup=back_to_menu_button())
        return

    if not drawings:
        text = "😔 Сейчас нет активных розыгрышей.\n\nПроверьте позже!"
        if is_callback:
            await message_or_callback.message.edit_text(text, reply_markup=back_to_menu_button())
            await message_or_callback.answer()
        else:
            await message_or_callback.answer(text, reply_markup=back_to_menu_button())
        return

    text = "🎲 <b>Выберите розыгрыш для участия:</b>"
    if is_callback:
        await message_or_callback.message.edit_text(text, parse_mode="HTML", reply_markup=_drawings_keyboard(drawings))
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(text, parse_mode="HTML", reply_markup=_drawings_keyboard(drawings))


@dp.callback_query(lambda c: c.data and c.data.startswith("check_sub_"))
async def check_subscription(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки 'Проверить подписку'."""
    drawing_id = int(callback.data.split("_", maxsplit=2)[2])

    # Проверяем подписки снова
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            channels_response = await client.get(
                f"{settings.admin_api_base_url}/drawings/{drawing_id}/channels"
            )
            if channels_response.status_code == 200:
                required_channels = channels_response.json()

                if required_channels:
                    missing_channels = await subscription_service.get_missing_subscriptions(
                        user_id=callback.from_user.id,
                        required_channels=required_channels
                    )

                    if missing_channels:
                        # Всё ещё не подписан
                        text = "❌ Вы всё ещё не подписаны на все обязательные каналы:\n\n"
                        for ch in missing_channels:
                            text += f"• {ch['channel_title']}\n"

                        await callback.answer(text, show_alert=True)
                        return

        # Все подписки есть - вызываем join_drawing
        await callback.answer("✅ Все подписки подтверждены!")
        # Меняем callback data на join_ чтобы переиспользовать логику
        callback.data = f"join_{drawing_id}"
        await join_drawing(callback, state)

    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to check subscriptions: %s", exc)
        await callback.answer("Ошибка проверки подписок. Попробуйте позже.", show_alert=True)


@dp.callback_query(lambda c: c.data and c.data.startswith("join_"))
async def join_drawing(callback: CallbackQuery, state: FSMContext) -> None:
    drawing_id = int(callback.data.split("_", maxsplit=1)[1])

    # Проверяем обязательные подписки
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Получаем список обязательных каналов для розыгрыша
            channels_response = await client.get(
                f"{settings.admin_api_base_url}/drawings/{drawing_id}/channels"
            )
            if channels_response.status_code == 200:
                required_channels = channels_response.json()

                if required_channels:
                    # Проверяем подписки
                    missing_channels = await subscription_service.get_missing_subscriptions(
                        user_id=callback.from_user.id,
                        required_channels=required_channels
                    )

                    if missing_channels:
                        # Формируем сообщение с кнопками для подписки
                        text = "⚠️ Для участия в розыгрыше необходимо подписаться на следующие каналы:\n\n"
                        buttons = []

                        for ch in missing_channels:
                            if ch.get("channel_username"):
                                text += f"• {ch['channel_title']} (@{ch['channel_username']})\n"
                                buttons.append([
                                    InlineKeyboardButton(
                                        text=f"Подписаться на {ch['channel_title']}",
                                        url=f"https://t.me/{ch['channel_username']}"
                                    )
                                ])
                            else:
                                text += f"• {ch['channel_title']}\n"

                        # Добавляем кнопку "Проверить подписку"
                        buttons.append([
                            InlineKeyboardButton(
                                text="✅ Проверить подписку",
                                callback_data=f"check_sub_{drawing_id}"
                            )
                        ])

                        await callback.message.answer(
                            text,
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                        )
                        await callback.answer()
                        return
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to check subscriptions: %s", exc)
        # Продолжаем без проверки, если не удалось получить каналы

    # Создаём заявку или получаем существующую
    payload = {
        "telegram_id": callback.from_user.id,
        "full_name": callback.from_user.full_name,
        "username": callback.from_user.username,
        "drawing_id": drawing_id,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{settings.admin_api_base_url}/applications/join", json=payload)
            response.raise_for_status()
            app_data = response.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 400:
            error_detail = exc.response.json().get("detail", "Не удалось создать заявку.")
            await callback.message.answer(f"❌ {error_detail}")
        else:
            logging.exception("Failed to join drawing: %s", exc)
            await callback.message.answer("Не удалось создать заявку. Попробуйте позже.")
        await callback.answer()
        return
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to join drawing: %s", exc)
        await callback.message.answer("Не удалось создать заявку. Попробуйте позже.")
        await callback.answer()
        return

    # Получаем информацию о розыгрыше
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            drawing_response = await client.get(
                f"{settings.admin_api_base_url}/drawings/{drawing_id}"
            )
            drawing_data = drawing_response.json() if drawing_response.status_code == 200 else None
    except Exception:
        drawing_data = None

    drawing_title = drawing_data["title"] if drawing_data else f"розыгрыш #{drawing_id}"
    is_paid = drawing_data and drawing_data.get("drawing_type") == "paid"

    # Обрабатываем разные статусы заявки
    app_status = app_data.get("status")

    if app_status == "draft" or app_status == "rejected":
        # Новая заявка или отклоненная - можно загружать профиль
        await state.update_data(application_id=app_data["id"], drawing_id=drawing_id)
        await state.set_state(ParticipateState.waiting_profile)
        await callback.message.answer(
            "✅ Заявка создана.\n"
            "📸 Отправьте скриншот профиля для проверки."
        )
    elif app_status == "pending":
        # Профиль на модерации
        await callback.message.answer(
            "⏳ Ваша заявка уже отправлена на проверку.\n"
            "Дождитесь результата модерации."
        )
    elif app_status == "approved" or app_status == "payment_pending":
        # Профиль одобрен, нужна оплата (для платных) или завершено (для бесплатных)
        if is_paid:
            from v2.services.admin.app.core.config import settings as admin_settings
            payment_details = admin_settings.payment_details or "свяжитесь с администратором"
            await callback.message.answer(
                f"✅ Ваш профиль одобрен!\n"
                f"Розыгрыш: {drawing_title}\n\n"
                f"💳 Следующий шаг - оплата участия.\n"
                f"Реквизиты для перевода: {payment_details}\n\n"
                f"После оплаты загрузите чек через команду /payment"
            )
        else:
            await callback.message.answer(
                f"✅ Ваш профиль одобрен!\n"
                f"Розыгрыш: {drawing_title}\n"
                f"Вы успешно участвуете в розыгрыше. Ожидайте результатов!"
            )
    elif app_status == "payment_bill_loaded":
        # Чек на модерации
        await callback.message.answer(
            f"⏳ Ваш чек оплаты уже отправлен на проверку для розыгрыша {drawing_title}.\n"
            "Дождитесь результата модерации."
        )
    elif app_status == "payment_confirmed" or app_status == "completed":
        # Оплата подтверждена
        await callback.message.answer(
            f"✅ Оплата подтверждена!\n"
            f"Розыгрыш: {drawing_title}\n"
            f"Вы успешно участвуете в розыгрыше. Ожидайте результатов!"
        )
    elif app_status == "payment_rejected":
        # Превышен лимит попыток оплаты
        await callback.message.answer(
            f"🚫 Превышен лимит попыток загрузки чека для розыгрыша {drawing_title}.\n"
            "Обратитесь к оператору через /operator."
        )
    else:
        # Неизвестный статус
        await callback.message.answer("❌ Неизвестный статус заявки. Обратитесь к администратору.")

    await callback.answer()


@dp.message(ParticipateState.waiting_profile)
async def upload_profile(message: Message, state: FSMContext, bot: Bot) -> None:
    if not message.photo:
        await message.answer("Отправьте именно фото со скриншотом профиля.")
        return

    data = await state.get_data()
    application_id = data.get("application_id")
    drawing_id = data.get("drawing_id")
    if application_id is None or drawing_id is None:
        await message.answer("Контекст заявки потерян. Начните заново через /drawings.")
        await state.clear()
        return

    photo = message.photo[-1]

    try:
        # Скачиваем и сохраняем файл
        file_key = await file_storage.download_telegram_file(
            bot=bot,
            file_id=photo.file_id,
            user_id=message.from_user.id,
            drawing_id=drawing_id,
            evidence_type="profile",
        )
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to download file: %s", exc)
        await message.answer("Не удалось сохранить файл. Попробуйте снова.")
        return

    payload = {
        "evidence_type": "profile",
        "file_key": file_key,
        "mime_type": "image/jpeg",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{settings.admin_api_base_url}/applications/{application_id}/evidences",
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 400:
            error_detail = exc.response.json().get("detail", "Не удалось загрузить скриншот.")
            await message.answer(f"❌ {error_detail}")
        else:
            logging.exception("Failed to upload profile evidence: %s", exc)
            await message.answer("Не удалось сохранить скриншот. Попробуйте снова.")
        return
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to upload profile evidence: %s", exc)
        await message.answer("Не удалось сохранить скриншот. Попробуйте снова.")
        return

    await message.answer(
        "✅ Скриншот профиля отправлен на модерацию.\n"
        "⏳ Ожидайте результата проверки."
    )
    await state.clear()


@dp.message(Command("payment"))
async def cmd_payment(message: Message, state: FSMContext) -> None:
    apps = await _fetch_my_apps(message.from_user.id)
    pending_payment = next((app for app in apps if app["status"] == "payment_pending"), None)
    if pending_payment is None:
        await message.answer("Нет заявок, ожидающих загрузку оплаты.")
        return

    # Используем название розыгрыша из данных заявки
    drawing_title = pending_payment.get("drawing_title") or f"розыгрыша #{pending_payment['drawing_id']}"

    await state.update_data(application_id=pending_payment["id"], drawing_id=pending_payment["drawing_id"])
    await state.set_state(ParticipateState.waiting_payment)
    await message.answer(f"Отправьте скриншот оплаты для конкурса '{drawing_title}'.")


@dp.message(ParticipateState.waiting_payment)
async def upload_payment(message: Message, state: FSMContext, bot: Bot) -> None:
    if not message.photo:
        await message.answer("Отправьте именно фото со скриншотом оплаты.")
        return

    data = await state.get_data()
    application_id = data.get("application_id")
    drawing_id = data.get("drawing_id")
    if application_id is None or drawing_id is None:
        await message.answer("Контекст заявки потерян. Повторите через /payment.")
        await state.clear()
        return

    photo = message.photo[-1]

    try:
        # Скачиваем и сохраняем файл
        file_key = await file_storage.download_telegram_file(
            bot=bot,
            file_id=photo.file_id,
            user_id=message.from_user.id,
            drawing_id=drawing_id,
            evidence_type="payment",
        )
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to download file: %s", exc)
        await message.answer("Не удалось сохранить файл. Попробуйте снова.")
        return

    payload = {
        "evidence_type": "payment",
        "file_key": file_key,
        "mime_type": "image/jpeg",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{settings.admin_api_base_url}/applications/{application_id}/evidences",
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 400:
            error_detail = exc.response.json().get("detail", "Не удалось загрузить чек.")
            await message.answer(f"❌ {error_detail}")
        else:
            logging.exception("Failed to upload payment evidence: %s", exc)
            await message.answer("Не удалось сохранить чек. Попробуйте снова.")
        return
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to upload payment evidence: %s", exc)
        await message.answer("Не удалось сохранить чек. Попробуйте снова.")
        return

    await message.answer("✅ Чек оплаты отправлен на модерацию.\n⏳ Ожидайте результата проверки.")
    await state.clear()


@dp.callback_query(lambda c: c.data == "menu_operator")
@dp.message(Command("operator"))
async def cmd_operator(message_or_callback) -> None:
    """Создание тикета для связи с оператором."""
    is_callback = isinstance(message_or_callback, CallbackQuery)

    user_id = message_or_callback.from_user.id
    full_name = message_or_callback.from_user.full_name
    username = message_or_callback.from_user.username

    # Проверяем наличие недавних отклонённых заявок
    rejected_app = None
    rejection_context = None

    try:
        apps = await _fetch_my_apps(user_id)
        # Ищем последнюю отклонённую заявку (профиль или оплата)
        for app in apps:
            if app.get("status") in ["rejected_profile", "rejected_payment", "payment_rejected"]:
                rejected_app = app
                # Пытаемся распарсить blocked_reason как JSON с контекстом отклонения
                if app.get("blocked_reason"):
                    try:
                        import json
                        rejection_context = json.loads(app["blocked_reason"])
                    except (json.JSONDecodeError, ValueError):
                        # Если не JSON, используем как обычный текст
                        rejection_context = {"reason": app["blocked_reason"]}
                break
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to fetch user applications: %s", exc)

    payload = {
        "telegram_id": user_id,
        "full_name": full_name,
        "username": username,
        "message": "Запрос оператора из Telegram-бота",
    }

    # Добавляем контекст отклонения, если есть
    if rejected_app and rejection_context:
        payload["application_id"] = rejected_app["id"]
        payload["drawing_id"] = rejected_app["drawing_id"]
        payload["rejection_reason"] = rejection_context.get("reason")
        payload["rejected_file_key"] = rejection_context.get("rejected_file_key")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{settings.admin_api_base_url}/operator-tickets", json=payload)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to create operator ticket: %s", exc)
        text = "❌ Не удалось отправить запрос оператору. Попробуйте позже."
        if is_callback:
            await message_or_callback.message.edit_text(text, reply_markup=back_to_menu_button())
            await message_or_callback.answer()
        else:
            await message_or_callback.answer(text, reply_markup=back_to_menu_button())
        return

    context_info = ""
    if rejected_app:
        context_info = "\n\n📎 К тикету автоматически прикреплена информация о последнем отклонении."

    text = (
        f"✅ <b>Запрос оператору создан!</b>\n\n"
        f"📝 Номер тикета: #{data['ticket_id']}\n"
        f"👤 Оператор свяжется с вами как можно скорее.{context_info}"
    )
    if is_callback:
        await message_or_callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_menu_button())
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(text, parse_mode="HTML", reply_markup=back_to_menu_button())


@dp.callback_query(lambda c: c.data == "menu_my_apps")
@dp.message(Command("my_applications"))
async def cmd_my_applications(message_or_callback) -> None:
    """Показать список заявок пользователя."""
    is_callback = isinstance(message_or_callback, CallbackQuery)
    user_id = message_or_callback.from_user.id

    apps = await _fetch_my_apps(user_id)
    if not apps:
        text = "📭 У вас пока нет заявок.\n\nНачните участие в розыгрыше!"
        if is_callback:
            await message_or_callback.message.edit_text(text, reply_markup=back_to_menu_button())
            await message_or_callback.answer()
        else:
            await message_or_callback.answer(text, reply_markup=back_to_menu_button())
        return

    # Красиво форматируем заявки
    text = "📋 <b>Ваши заявки:</b>\n\n"

    status_emoji = {
        "pending": "⏳",
        "approved": "✅",
        "rejected_profile": "❌",
        "rejected_payment": "❌",
        "payment_pending": "💳",
        "payment_bill_loaded": "🔍",
        "payment_rejected": "🚫",
        "payment_confirmed": "✅",
        "completed": "🎉",
        "blocked": "🚫",
    }

    for app in apps[:10]:  # Показываем максимум 10 последних
        status = app.get('status', 'unknown')
        emoji = status_emoji.get(status, "❓")
        text += (
            f"{emoji} <b>Заявка #{app['id']}</b>\n"
            f"   Розыгрыш: #{app['drawing_id']}\n"
            f"   Статус: {status}\n"
        )
        # Показываем попытки оплаты если есть
        if app.get('payment_attempts_used', 0) > 0:
            text += f"   Попытки оплаты: {app['payment_attempts_used']}/3\n"
        # Показываем причину отклонения, если есть
        if app.get('blocked_reason'):
            try:
                import json
                reason_data = json.loads(app['blocked_reason'])
                reason_text = reason_data.get('reason', app['blocked_reason'])
            except (json.JSONDecodeError, ValueError):
                reason_text = app['blocked_reason']
            text += f"   Причина: {reason_text[:50]}...\n" if len(reason_text) > 50 else f"   Причина: {reason_text}\n"
        text += "\n"

    if len(apps) > 10:
        text += f"<i>...и ещё {len(apps) - 10} заявок</i>"

    if is_callback:
        await message_or_callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_menu_button())
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(text, parse_mode="HTML", reply_markup=back_to_menu_button())


async def _fetch_my_apps(telegram_id: int) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{settings.admin_api_base_url}/applications/my",
                params={"telegram_id": telegram_id},
            )
            response.raise_for_status()
            return response.json()
    except Exception:  # noqa: BLE001
        return []


@dp.message(Command("winners"))
async def cmd_winners(message: Message) -> None:
    """Показать победителей розыгрыша."""
    # Ожидаем формат: /winners <drawing_id>
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Используйте формат: /winners <ID_розыгрыша>\n"
            "Например: /winners 1"
        )
        return

    try:
        drawing_id = int(parts[1])
    except ValueError:
        await message.answer("Неверный ID розыгрыша. Используйте число.")
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Получаем информацию о розыгрыше
            drawing_response = await client.get(f"{settings.admin_api_base_url}/drawings")
            if drawing_response.status_code == 200:
                drawings = drawing_response.json()
                drawing = next((d for d in drawings if d["id"] == drawing_id), None)

                if not drawing:
                    await message.answer(f"Розыгрыш #{drawing_id} не найден.")
                    return

            # Получаем победителей
            winners_response = await client.get(f"{settings.admin_api_base_url}/drawings/{drawing_id}/winners")

            if winners_response.status_code == 404:
                await message.answer(f"Розыгрыш #{drawing_id} не найден.")
                return

            winners_response.raise_for_status()
            winners = winners_response.json()

        if not winners:
            await message.answer(
                f"🏆 Розыгрыш: {drawing.get('title', f'#{drawing_id}')}\n\n"
                "Победители ещё не определены."
            )
            return

        # Формируем сообщение с победителями
        text = f"🏆 Победители розыгрыша:\n{drawing.get('title', f'#{drawing_id}')}\n\n"

        for i, winner in enumerate(winners, 1):
            username_text = f" (@{winner['username']})" if winner.get('username') else ""
            text += f"{i}. {winner['full_name']}{username_text}\n"

        text += f"\n📅 Итоги подведены: {winners[0]['selected_at'][:10] if winners else ''}"

        await message.answer(text)

    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to fetch winners: %s", exc)
        await message.answer("Не удалось получить список победителей. Попробуйте позже.")


async def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Set BOT_TOKEN in v2/.env")

    bot = Bot(token=settings.bot_token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
