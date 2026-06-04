"""
Сервис для отправки уведомлений пользователям через Telegram бота.
"""
import logging
from typing import Optional

import httpx

from v2.services.admin.app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений через Telegram бота."""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    async def send_message(self, chat_id: int, text: str) -> bool:
        """
        Отправить текстовое сообщение пользователю.

        Args:
            chat_id: Telegram ID пользователя
            text: Текст сообщения

        Returns:
            True если сообщение отправлено успешно, False в противном случае
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                )
                response.raise_for_status()
                return True
        except Exception as exc:
            logger.exception("Failed to send notification to %s: %s", chat_id, exc)
            return False

    async def notify_profile_approved(
        self, telegram_id: int, drawing_title: str, is_paid: bool
    ) -> bool:
        """Уведомление об одобрении профиля."""
        if is_paid:
            text = (
                f"✅ <b>Ваш профиль одобрен!</b>\n\n"
                f"Розыгрыш: {drawing_title}\n\n"
                f"Теперь необходимо загрузить чек оплаты.\n"
                f"Используйте команду /payment для загрузки чека."
            )
        else:
            text = (
                f"✅ <b>Ваш профиль одобрен!</b>\n\n"
                f"Розыгрыш: {drawing_title}\n\n"
                f"Вы успешно участвуете в розыгрыше. Ожидайте результатов!"
            )
        return await self.send_message(telegram_id, text)

    async def notify_profile_rejected(
        self, telegram_id: int, drawing_title: str, reason: Optional[str], attempts_left: int
    ) -> bool:
        """Уведомление об отклонении профиля."""
        text = (
            f"❌ <b>Ваш профиль отклонён</b>\n\n"
            f"Розыгрыш: {drawing_title}\n\n"
        )

        if reason:
            text += f"Причина: {reason}\n\n"

        if attempts_left > 0:
            text += (
                f"У вас осталось попыток: {attempts_left}\n"
                f"Пожалуйста, загрузите новый скриншот профиля через /drawings"
            )
        else:
            text += (
                "Вы исчерпали все попытки загрузки профиля.\n"
                "Обратитесь к оператору через /operator если считаете, что произошла ошибка."
            )

        return await self.send_message(telegram_id, text)

    async def notify_payment_approved(self, telegram_id: int, drawing_title: str) -> bool:
        """Уведомление об одобрении оплаты."""
        text = (
            f"✅ <b>Оплата подтверждена!</b>\n\n"
            f"Розыгрыш: {drawing_title}\n\n"
            f"Вы успешно участвуете в розыгрыше. Ожидайте результатов!"
        )
        return await self.send_message(telegram_id, text)

    async def notify_payment_rejected(
        self, telegram_id: int, drawing_title: str, reason: Optional[str], attempts_left: int
    ) -> bool:
        """Уведомление об отклонении оплаты."""
        text = (
            f"❌ <b>Оплата отклонена</b>\n\n"
            f"Розыгрыш: {drawing_title}\n\n"
        )

        if reason:
            text += f"Причина: {reason}\n\n"

        if attempts_left > 0:
            text += (
                f"У вас осталось попыток: {attempts_left}\n"
                f"Пожалуйста, загрузите новый чек оплаты через /payment"
            )
        else:
            text += (
                "Вы исчерпали все попытки загрузки чека.\n"
                "Обратитесь к оператору через /operator если считаете, что произошла ошибка."
            )

        return await self.send_message(telegram_id, text)

    async def notify_winner(
        self, telegram_id: int, drawing_title: str, drawing_description: Optional[str]
    ) -> bool:
        """Уведомление победителю."""
        text = (
            f"🎉 <b>Поздравляем! Вы победили!</b>\n\n"
            f"Розыгрыш: {drawing_title}\n\n"
        )

        if drawing_description:
            text += f"{drawing_description}\n\n"

        text += "С вами свяжутся для получения приза."

        return await self.send_message(telegram_id, text)

    async def notify_drawing_completed(
        self, telegram_id: int, drawing_title: str, won: bool
    ) -> bool:
        """Уведомление о завершении розыгрыша."""
        if won:
            return await self.notify_winner(telegram_id, drawing_title, None)

        text = (
            f"📊 <b>Розыгрыш завершён</b>\n\n"
            f"Розыгрыш: {drawing_title}\n\n"
            f"К сожалению, в этот раз вы не победили.\n"
            f"Следите за новыми розыгрышами через /drawings"
        )
        return await self.send_message(telegram_id, text)


# Singleton instance
notification_service = NotificationService(bot_token=settings.bot_token)
