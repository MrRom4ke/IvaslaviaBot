from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session, aliased

from v2.services.admin.app.api.deps import get_current_admin, get_db
from v2.services.admin.app.schemas.moderation import ModerationQueueItem, ModerationQueueResponse
from v2.shared.db.models import Admin, Application, ApplicationEvidence, Drawing, User
from v2.shared.domain.enums import ApplicationStatus, EvidenceType

router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.get("/queue", response_model=ModerationQueueResponse)
def get_moderation_queue(
    evidence_type: EvidenceType | None = Query(None, description="Фильтр по типу evidence (profile/payment)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
) -> ModerationQueueResponse:
    """
    Очередь модерации: заявки с последним evidence, требующие проверки.
    Сортировка по created_at последнего evidence (старые первыми).
    """
    # Подзапрос: последний evidence для каждой заявки
    latest_evidence_subq = (
        db.query(
            ApplicationEvidence.application_id,
            func.max(ApplicationEvidence.id).label("latest_evidence_id"),
        )
        .group_by(ApplicationEvidence.application_id)
        .subquery()
    )

    # Основной запрос
    query = (
        db.query(
            Application.id.label("application_id"),
            Application.user_id,
            Application.drawing_id,
            Drawing.title.label("drawing_title"),
            User.telegram_id,
            User.full_name,
            User.username,
            Application.status.label("application_status"),
            ApplicationEvidence.evidence_type,
            ApplicationEvidence.id.label("evidence_id"),
            ApplicationEvidence.file_key,
            ApplicationEvidence.created_at.label("evidence_created_at"),
            Application.profile_attempts_used,
            Application.payment_attempts_used,
        )
        .join(latest_evidence_subq, Application.id == latest_evidence_subq.c.application_id)
        .join(ApplicationEvidence, ApplicationEvidence.id == latest_evidence_subq.c.latest_evidence_id)
        .join(User, Application.user_id == User.id)
        .join(Drawing, Application.drawing_id == Drawing.id)
        .filter(
            Application.status.in_([
                ApplicationStatus.pending,
                ApplicationStatus.payment_bill_loaded,
            ])
        )
    )

    # Фильтр по типу evidence
    if evidence_type is not None:
        query = query.filter(ApplicationEvidence.evidence_type == evidence_type)

    # Подсчет общего количества
    total = query.count()

    # Сортировка и пагинация
    rows = query.order_by(ApplicationEvidence.created_at.asc()).offset(offset).limit(limit).all()

    items = [
        ModerationQueueItem(
            application_id=row.application_id,
            user_id=row.user_id,
            drawing_id=row.drawing_id,
            drawing_title=row.drawing_title,
            telegram_id=row.telegram_id,
            full_name=row.full_name,
            username=row.username,
            application_status=row.application_status,
            evidence_type=row.evidence_type,
            evidence_id=row.evidence_id,
            file_key=row.file_key,
            evidence_created_at=row.evidence_created_at,
            profile_attempts_used=row.profile_attempts_used,
            payment_attempts_used=row.payment_attempts_used,
        )
        for row in rows
    ]

    return ModerationQueueResponse(items=items, total=total)
