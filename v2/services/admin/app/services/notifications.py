import logging

import httpx

from v2.services.admin.app.core.config import settings

logger = logging.getLogger(__name__)


class TelegramNotificationService:
    """Сервис для отправки уведомлений пользователям через Telegram Bot API."""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    async def send_message(self, telegram_id: int, text: str) -> bool:
        """
        Отправляет сообщение пользователю.

        Returns:
            True если сообщение отправлено успешно, False в случае ошибки
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": telegram_id,
                        "text": text,
                        "parse_mode": "HTML",
                    },
                )
                response.raise_for_status()
                return True
        except Exception as exc:
            logger.exception("Failed to send Telegram message to %s: %s", telegram_id, exc)
            return False

    async def notify_profile_approved(self, telegram_id: int, drawing_title: str, is_paid: bool) -> bool:
        """Уведомление об одобрении профиля."""
        if is_paid:
            text = (
                f"✅ <b>Профиль одобрен</b>\n\n"
                f"Розыгрыш: {drawing_title}\n\n"
                f"Теперь отправьте скриншот оплаты командой /payment"
            )
        else:
            text = (
                f"✅ <b>Заявка одобрена</b>\n\n"
                f"Розыгрыш: {drawing_title}\n\n"
                f"Вы участвуете в розыгрыше! Ожидайте результатов."
            )
        return await self.send_message(telegram_id, text)

    async def notify_profile_rejected(
        self, telegram_id: int, drawing_title: str, reason: str | None, attempts_left: int
    ) -> bool:
        """Уведомление об отклонении профиля."""
        reason_text = f"\n\nПричина: {reason}" if reason else ""
        if attempts_left > 0:
            text = (
                f"❌ <b>Профиль отклонен</b>\n\n"
                f"Розыгрыш: {drawing_title}{reason_text}\n\n"
                f"Осталось попыток: {attempts_left}\n"
                f"Отправьте новый скриншот профиля."
            )
        else:
            text = (
                f"🚫 <b>Заявка заблокирована</b>\n\n"
                f"Розыгрыш: {drawing_title}{reason_text}\n\n"
                f"Превышен лимит попыток загрузки профиля.\n"
                f"Обратитесь к оператору: /operator"
            )
        return await self.send_message(telegram_id, text)

    async def notify_payment_approved(self, telegram_id: int, drawing_title: str) -> bool:
        """Уведомление об одобрении оплаты."""
        text = (
            f"✅ <b>Оплата подтверждена</b>\n\n"
            f"Розыгрыш: {drawing_title}\n\n"
            f"Вы участвуете в розыгрыше! Ожидайте результатов."
        )
        return await self.send_message(telegram_id, text)

    async def notify_payment_rejected(
        self, telegram_id: int, drawing_title: str, reason: str | None, attempts_left: int
    ) -> bool:
        """Уведомление об отклонении оплаты."""
        reason_text = f"\n\nПричина: {reason}" if reason else ""
        if attempts_left > 0:
            text = (
                f"❌ <b>Оплата отклонена</b>\n\n"
                f"Розыгрыш: {drawing_title}{reason_text}\n\n"
                f"Осталось попыток: {attempts_left}\n"
                f"Отправьте новый скриншот оплаты командой /payment"
            )
        else:
            text = (
                f"🚫 <b>Заявка заблокирована</b>\n\n"
                f"Розыгрыш: {drawing_title}{reason_text}\n\n"
                f"Превышен лимит попыток загрузки чека.\n"
                f"Обратитесь к оператору: /operator"
            )
        return await self.send_message(telegram_id, text)


# Singleton instance
def get_notification_service() -> TelegramNotificationService:
    """Получить экземпляр сервиса уведомлений."""
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not configured")
    return TelegramNotificationService(settings.bot_token)
