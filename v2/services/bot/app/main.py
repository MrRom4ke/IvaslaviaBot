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

logging.basicConfig(level=logging.INFO)


class ParticipateState(StatesGroup):
    waiting_profile = State()
    waiting_payment = State()


dp = Dispatcher(storage=MemoryStorage())


def _drawings_keyboard(drawings: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{item['title']} ({item['drawing_type']})", callback_data=f"join_{item['id']}")]
        for item in drawings
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "IvaslaviaBot v2 запущен.\n"
        "Админские функции вынесены в веб-панель.\n"
        "Команды: /drawings, /operator, /my_applications."
    )


@dp.message(Command("drawings"))
async def cmd_drawings(message: Message) -> None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{settings.admin_api_base_url}/drawings", params={"status": "active"})
            response.raise_for_status()
            drawings = response.json()
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to fetch drawings: %s", exc)
        await message.answer("Не удалось получить список розыгрышей. Попробуйте позже.")
        return

    if not drawings:
        await message.answer("Сейчас нет активных розыгрышей.")
        return

    await message.answer("Выберите розыгрыш для участия:", reply_markup=_drawings_keyboard(drawings))


@dp.callback_query(lambda c: c.data and c.data.startswith("join_"))
async def join_drawing(callback: CallbackQuery, state: FSMContext) -> None:
    drawing_id = int(callback.data.split("_", maxsplit=1)[1])
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
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to join drawing: %s", exc)
        await callback.message.answer("Не удалось создать заявку. Попробуйте позже.")
        await callback.answer()
        return

    await state.update_data(application_id=app_data["id"], drawing_id=drawing_id)
    await state.set_state(ParticipateState.waiting_profile)
    await callback.message.answer(
        "Заявка создана. Отправьте скриншот профиля для проверки.\n"
        f"ID заявки: {app_data['id']}"
    )
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
            await client.post(
                f"{settings.admin_api_base_url}/applications/{application_id}/evidences",
                json=payload,
            )
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to upload profile evidence: %s", exc)
        await message.answer("Не удалось сохранить скриншот. Попробуйте снова.")
        return

    await message.answer(
        "Скриншот профиля отправлен на модерацию.\n"
        "Если розыгрыш платный, после одобрения профиля отправьте чек командой /payment."
    )
    await state.clear()


@dp.message(Command("payment"))
async def cmd_payment(message: Message, state: FSMContext) -> None:
    apps = await _fetch_my_apps(message.from_user.id)
    pending_payment = next((app for app in apps if app["status"] == "payment_pending"), None)
    if pending_payment is None:
        await message.answer("Нет заявок, ожидающих загрузку оплаты.")
        return
    await state.update_data(application_id=pending_payment["id"], drawing_id=pending_payment["drawing_id"])
    await state.set_state(ParticipateState.waiting_payment)
    await message.answer(f"Отправьте скриншот оплаты для заявки #{pending_payment['id']}.")


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
            await client.post(
                f"{settings.admin_api_base_url}/applications/{application_id}/evidences",
                json=payload,
            )
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to upload payment evidence: %s", exc)
        await message.answer("Не удалось сохранить чек. Попробуйте снова.")
        return

    await message.answer("Чек оплаты отправлен на модерацию.")
    await state.clear()


@dp.message(Command("operator"))
async def cmd_operator(message: Message) -> None:
    payload = {
        "telegram_id": message.from_user.id,
        "full_name": message.from_user.full_name,
        "username": message.from_user.username,
        "message": "Запрос оператора из Telegram-бота",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{settings.admin_api_base_url}/operator-tickets", json=payload)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to create operator ticket: %s", exc)
        await message.answer("Не удалось отправить запрос оператору. Попробуйте позже.")
        return

    await message.answer(
        f"Запрос оператору создан. Номер тикета: {data['ticket_id']}.\n"
        "Оператор свяжется с вами как можно скорее."
    )


@dp.message(Command("my_applications"))
async def cmd_my_applications(message: Message) -> None:
    apps = await _fetch_my_apps(message.from_user.id)
    if not apps:
        await message.answer("У вас пока нет заявок.")
        return

    lines = [
        f"#{app['id']} | drawing={app['drawing_id']} | status={app['status']} | "
        f"profile_attempts={app['profile_attempts_used']} | payment_attempts={app['payment_attempts_used']}"
        for app in apps
    ]
    await message.answer("Ваши заявки:\n" + "\n".join(lines[:20]))


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


async def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Set BOT_TOKEN in v2/.env")

    bot = Bot(token=settings.bot_token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
