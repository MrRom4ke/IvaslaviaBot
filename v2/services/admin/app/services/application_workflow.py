from v2.shared.db.models import Application, Drawing
from v2.shared.domain.enums import ApplicationStatus, DrawingType


def apply_profile_moderation(application: Application, drawing: Drawing, approved: bool, reason: str | None) -> None:
    if approved:
        if drawing.drawing_type == DrawingType.free:
            application.status = ApplicationStatus.completed
        else:
            application.status = ApplicationStatus.payment_pending
        application.blocked_reason = None
        return

    application.profile_attempts_used += 1
    if application.profile_attempts_used >= 3:
        application.status = ApplicationStatus.rejected
        application.blocked_reason = reason or "Превышен лимит попыток загрузки профиля"
    else:
        application.status = ApplicationStatus.rejected
        application.blocked_reason = reason or "Скриншот профиля отклонен"


def apply_payment_moderation(application: Application, approved: bool, reason: str | None) -> None:
    if approved:
        application.status = ApplicationStatus.completed
        application.blocked_reason = None
        return

    application.payment_attempts_used += 1
    if application.payment_attempts_used >= 3:
        application.status = ApplicationStatus.payment_rejected
        application.blocked_reason = reason or "Превышен лимит попыток загрузки чека оплаты"
    else:
        application.status = ApplicationStatus.payment_pending
        application.blocked_reason = reason or "Чек оплаты отклонен"

