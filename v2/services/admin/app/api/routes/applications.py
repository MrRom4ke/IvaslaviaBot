from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from v2.services.admin.app.api.deps import get_db
from v2.services.admin.app.schemas.applications import (
    ApplicationResponse,
    JoinApplicationRequest,
    ModerateApplicationRequest,
    UploadEvidenceRequest,
)
from v2.services.admin.app.services.application_workflow import apply_payment_moderation, apply_profile_moderation
from v2.services.admin.app.services.notification_service import notification_service
from v2.shared.db.models import Application, ApplicationEvidence, Drawing, OperatorTicket, User
from v2.shared.domain.enums import ApplicationStatus, EvidenceType, TicketStatus

router = APIRouter(prefix="/applications", tags=["applications"])


def _to_response(application: Application) -> ApplicationResponse:
    drawing_title = None
    if application.drawing:
        drawing_title = application.drawing.title

    return ApplicationResponse(
        id=application.id,
        user_id=application.user_id,
        drawing_id=application.drawing_id,
        drawing_title=drawing_title,
        status=application.status,
        payment_attempts_used=application.payment_attempts_used,
        blocked_reason=application.blocked_reason,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


@router.get("", response_model=list[ApplicationResponse])
def list_applications(
    status: ApplicationStatus | None = None,
    drawing_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[ApplicationResponse]:
    query = db.query(Application).join(Drawing, Application.drawing_id == Drawing.id)
    if status is not None:
        query = query.filter(Application.status == status)
    if drawing_id is not None:
        query = query.filter(Application.drawing_id == drawing_id)
    rows = query.order_by(Application.created_at.desc()).all()
    return [_to_response(row) for row in rows]


@router.get("/my", response_model=list[ApplicationResponse])
def list_my_applications(telegram_id: int, db: Session = Depends(get_db)) -> list[ApplicationResponse]:
    user = db.query(User).filter(User.telegram_id == telegram_id).one_or_none()
    if user is None:
        return []
    rows = db.query(Application).join(Drawing, Application.drawing_id == Drawing.id).filter(Application.user_id == user.id).order_by(Application.created_at.desc()).all()
    return [_to_response(row) for row in rows]


@router.post("/join", response_model=ApplicationResponse)
def join_drawing(payload: JoinApplicationRequest, db: Session = Depends(get_db)) -> ApplicationResponse:
    logger = logging.getLogger(__name__)
    logger.info(f"JOIN REQUEST: telegram_id={payload.telegram_id}, drawing_id={payload.drawing_id}")

    drawing = db.query(Drawing).filter(Drawing.id == payload.drawing_id).one_or_none()
    if drawing is None:
        raise HTTPException(status_code=404, detail="Drawing not found")

    user = db.query(User).filter(User.telegram_id == payload.telegram_id).one_or_none()
    if user is None:
        user = User(
            telegram_id=payload.telegram_id,
            full_name=payload.full_name,
            username=payload.username,
        )
        db.add(user)
        db.flush()

    existing = (
        db.query(Application)
        .filter(Application.user_id == user.id, Application.drawing_id == payload.drawing_id)
        .one_or_none()
    )
    logger.info(f"JOIN: user_id={user.id}, drawing_id={payload.drawing_id}, existing={existing.id if existing else None}, status={existing.status if existing else None}")
    if existing is not None:
        # Возвращаем существующую заявку независимо от статуса
        # Бот сам решит, что показать пользователю
        return _to_response(existing)

    app = Application(
        user_id=user.id,
        drawing_id=drawing.id,
        status=ApplicationStatus.draft,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return _to_response(app)


@router.post("/{application_id}/evidences", response_model=ApplicationResponse)
def upload_evidence(application_id: int, payload: UploadEvidenceRequest, db: Session = Depends(get_db)) -> ApplicationResponse:
    application = db.query(Application).filter(Application.id == application_id).one_or_none()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    # Проверяем, можно ли загружать скриншот для текущего статуса заявки
    # Если превышен лимит попыток оплаты - блокируем всё
    if application.status == ApplicationStatus.payment_rejected:
        raise HTTPException(
            status_code=400,
            detail="Превышен лимит попыток загрузки чека. Обратитесь к оператору через /operator."
        )

    if payload.evidence_type == EvidenceType.profile:
        if application.status == ApplicationStatus.pending:
            raise HTTPException(
                status_code=400,
                detail="Ваша заявка уже отправлена на проверку. Дождитесь результата модерации."
            )
        if application.status == ApplicationStatus.approved:
            raise HTTPException(
                status_code=400,
                detail="Ваш профиль уже одобрен."
            )
        # Статус draft и rejected разрешены для загрузки скриншота
    elif payload.evidence_type == EvidenceType.payment:
        if application.status == ApplicationStatus.payment_bill_loaded:
            raise HTTPException(
                status_code=400,
                detail="Ваш чек уже отправлен на проверку. Дождитесь результата модерации."
            )
        if application.status == ApplicationStatus.payment_confirmed:
            raise HTTPException(
                status_code=400,
                detail="Ваша оплата уже подтверждена."
            )

    evidence = ApplicationEvidence(
        application_id=application.id,
        evidence_type=payload.evidence_type,
        file_key=payload.file_key,
        mime_type=payload.mime_type,
    )
    db.add(evidence)

    if payload.evidence_type == EvidenceType.profile:
        application.status = ApplicationStatus.pending
    else:
        if application.status in (ApplicationStatus.payment_pending, ApplicationStatus.payment_rejected):
            application.status = ApplicationStatus.payment_bill_loaded

    db.commit()
    db.refresh(application)
    return _to_response(application)


@router.post("/{application_id}/moderate-profile", response_model=ApplicationResponse)
async def moderate_profile(
    application_id: int, payload: ModerateApplicationRequest, db: Session = Depends(get_db)
) -> ApplicationResponse:
    application = db.query(Application).filter(Application.id == application_id).one_or_none()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    drawing = db.query(Drawing).filter(Drawing.id == application.drawing_id).one_or_none()
    if drawing is None:
        raise HTTPException(status_code=404, detail="Drawing not found")

    user = db.query(User).filter(User.id == application.user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Получаем последний скриншот профиля для сохранения в контексте отклонения
    rejected_file_key = None
    if not payload.approved:
        latest_evidence = (
            db.query(ApplicationEvidence)
            .filter(
                ApplicationEvidence.application_id == application.id,
                ApplicationEvidence.evidence_type == EvidenceType.profile
            )
            .order_by(ApplicationEvidence.created_at.desc())
            .first()
        )
        if latest_evidence:
            rejected_file_key = latest_evidence.file_key

    # Применяем модерацию
    apply_profile_moderation(application, drawing, payload.approved, payload.reason)

    # Сохраняем контекст отклонения для использования в тикете поддержки
    if not payload.approved and rejected_file_key:
        # Сохраним в blocked_reason JSON с информацией для тикета
        import json
        application.blocked_reason = json.dumps({
            "reason": payload.reason or "Скриншот профиля отклонён",
            "rejected_file_key": rejected_file_key,
            "rejected_at": datetime.utcnow().isoformat()
        })

    db.commit()
    db.refresh(application)

    # Отправляем уведомление пользователю
    if payload.approved:
        await notification_service.notify_profile_approved(
            telegram_id=user.telegram_id,
            drawing_title=drawing.title,
            is_paid=(drawing.drawing_type.value == "paid"),
        )
    else:
        await notification_service.notify_profile_rejected(
            telegram_id=user.telegram_id,
            drawing_title=drawing.title,
            reason=payload.reason,
        )

    return _to_response(application)


@router.post("/{application_id}/moderate-payment", response_model=ApplicationResponse)
async def moderate_payment(
    application_id: int, payload: ModerateApplicationRequest, db: Session = Depends(get_db)
) -> ApplicationResponse:
    application = db.query(Application).filter(Application.id == application_id).one_or_none()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    drawing = db.query(Drawing).filter(Drawing.id == application.drawing_id).one_or_none()
    if drawing is None:
        raise HTTPException(status_code=404, detail="Drawing not found")

    user = db.query(User).filter(User.id == application.user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Получаем последний скриншот оплаты для сохранения в контексте отклонения
    rejected_file_key = None
    if not payload.approved:
        latest_evidence = (
            db.query(ApplicationEvidence)
            .filter(
                ApplicationEvidence.application_id == application.id,
                ApplicationEvidence.evidence_type == EvidenceType.payment
            )
            .order_by(ApplicationEvidence.created_at.desc())
            .first()
        )
        if latest_evidence:
            rejected_file_key = latest_evidence.file_key

    # Применяем модерацию
    apply_payment_moderation(application, payload.approved, payload.reason)

    # Если превышен лимит попыток - сохраняем контекст для тикета
    if not payload.approved and application.payment_attempts_used >= 3 and rejected_file_key:
        import json
        application.blocked_reason = json.dumps({
            "reason": payload.reason or "Превышен лимит попыток загрузки чека оплаты",
            "rejected_file_key": rejected_file_key,
            "rejected_at": datetime.utcnow().isoformat()
        })

    db.commit()
    db.refresh(application)

    # Отправляем уведомление пользователю
    if payload.approved:
        await notification_service.notify_payment_approved(
            telegram_id=user.telegram_id,
            drawing_title=drawing.title,
        )
    else:
        attempts_left = 3 - application.payment_attempts_used
        await notification_service.notify_payment_rejected(
            telegram_id=user.telegram_id,
            drawing_title=drawing.title,
            reason=payload.reason,
            attempts_left=attempts_left,
        )

    return _to_response(application)
