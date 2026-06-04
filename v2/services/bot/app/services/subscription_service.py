"""
Сервис для проверки подписки пользователя на обязательные каналы.
"""
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Сервис для проверки подписки на Telegram каналы."""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    async def check_subscription(self, user_id: int, channel_id: int) -> bool:
        """
        Проверить, подписан ли пользователь на канал.

        Args:
            user_id: Telegram ID пользователя
            channel_id: Telegram ID канала (с минусом для каналов/групп)

        Returns:
            True если пользователь подписан, False в противном случае
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.base_url}/getChatMember",
                    json={"chat_id": channel_id, "user_id": user_id},
                )
                response.raise_for_status()
                data = response.json()

                if not data.get("ok"):
                    logger.warning(
                        "Failed to check subscription for user %s in channel %s: %s",
                        user_id,
                        channel_id,
                        data.get("description"),
                    )
                    return False

                # Статусы, при которых считаем что пользователь подписан
                status = data.get("result", {}).get("status")
                return status in ("creator", "administrator", "member")

        except Exception as exc:
            logger.exception(
                "Error checking subscription for user %s in channel %s: %s",
                user_id,
                channel_id,
                exc,
            )
            return False

    async def get_missing_subscriptions(
        self, user_id: int, required_channels: list[dict]
    ) -> list[dict]:
        """
        Получить список каналов, на которые пользователь не подписан.

        Args:
            user_id: Telegram ID пользователя
            required_channels: Список обязательных каналов
                               [{"id": int, "channel_id": int, "channel_username": str, "channel_title": str}]

        Returns:
            Список каналов, на которые пользователь не подписан
        """
        missing = []

        for channel in required_channels:
            is_subscribed = await self.check_subscription(user_id, channel["channel_id"])
            if not is_subscribed:
                missing.append(channel)

        return missing
