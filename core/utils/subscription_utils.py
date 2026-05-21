import logging
import os
import re

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

from config import config

logger = logging.getLogger(__name__)

_SUBSCRIBED_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.CREATOR,
}


def _parse_channel_entry(raw: str) -> dict | None:
    """
    Формат: chat_id_or_username|Название|https://t.me/... (ссылка опциональна)
    Пример: ivaslavskov|Основной канал
    """
    raw = raw.strip()
    if not raw:
        return None

    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 2:
        return None

    chat_id = parts[0]
    title = parts[1]
    url = parts[2] if len(parts) > 2 else None

    if not chat_id.startswith("@") and not re.fullmatch(r"-?\d+", chat_id):
        chat_id = f"@{chat_id}" if not chat_id.startswith("@") else chat_id

    if not url:
        username = chat_id.lstrip("@")
        if username and not username.startswith("-"):
            url = f"https://t.me/{username}"
        else:
            url = None

    return {"chat_id": chat_id, "title": title, "url": url}


def load_subscription_channels() -> list[dict]:
    """Загружает список обязательных каналов из env или config.ini."""
    raw = os.getenv("SUBSCRIPTION_CHANNELS", "").strip()
    if not raw and config.has_section("subscription"):
        raw = config.get("subscription", "channels", fallback="").strip()

    if not raw:
        return []

    channels = []
    for entry in re.split(r"[\n,]+", raw):
        channel = _parse_channel_entry(entry)
        if channel:
            channels.append(channel)
    return channels


REQUIRED_CHANNELS = load_subscription_channels()


async def is_user_subscribed(bot: Bot, user_id: int, chat_id: str) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    except TelegramBadRequest as e:
        logger.warning("Не удалось проверить подписку %s для %s: %s", chat_id, user_id, e)
        return False

    if member.status in _SUBSCRIBED_STATUSES:
        return True

    if member.status == ChatMemberStatus.RESTRICTED:
        return getattr(member, "is_member", False)

    return False


async def get_missing_subscriptions(bot: Bot, user_id: int) -> list[dict]:
    """Каналы, на которые пользователь ещё не подписан."""
    if not REQUIRED_CHANNELS:
        return []

    missing = []
    for channel in REQUIRED_CHANNELS:
        if not await is_user_subscribed(bot, user_id, channel["chat_id"]):
            missing.append(channel)
    return missing


async def has_required_subscriptions(bot: Bot, user_id: int) -> bool:
    missing = await get_missing_subscriptions(bot, user_id)
    return len(missing) == 0
