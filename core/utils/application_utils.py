APPLICATION_STATUS_LABELS = {
    "pending": "ожидает проверки скриншота",
    "approved": "скриншот одобрен, ожидает оплату",
    "rejected": "скриншот отклонён",
    "payment_pending": "ожидает оплату",
    "payment_bill_loaded": "чек на проверке",
    "payment_confirmed": "оплата подтверждена",
    "payment_reject": "оплата отклонена",
    "completed": "заявка аннулирована",
}

DRAWING_STATUS_LABELS = {
    "upcoming": "предстоящий",
    "active": "активный",
    "ready_to_draw": "ожидает розыгрыша",
    "completed": "завершён",
}


def format_application_status(status: str) -> str:
    return APPLICATION_STATUS_LABELS.get(status, status)


def format_drawing_status(status: str) -> str:
    return DRAWING_STATUS_LABELS.get(status, status)


def format_participations_block(participations: list[dict]) -> str:
    if not participations:
        return "Участие в розыгрышах: нет заявок."

    lines = ["Участие в розыгрышах:"]
    for i, item in enumerate(participations, start=1):
        app_status = format_application_status(item["application_status"])
        draw_status = format_drawing_status(item["drawing_status"])
        lines.append(
            f"{i}. «{item['drawing_title']}»\n"
            f"   Статус заявки: {app_status}\n"
            f"   Статус розыгрыша: {draw_status}"
        )
    return "\n".join(lines)


def build_operator_admin_message(
    telegram_id: int,
    full_name: str | None,
    username: str | None,
    participations: list[dict],
) -> str:
    name = full_name or "—"
    if username:
        contact = f"@{username.lstrip('@')}"
    else:
        contact = "—"

    participations_text = format_participations_block(participations)

    return (
        f"Запрос к Оператору:\n"
        f"Имя: {name}\n"
        f"Username: {contact} ([ID {telegram_id}](tg://user?id={telegram_id}))\n\n"
        f"{participations_text}"
    )
