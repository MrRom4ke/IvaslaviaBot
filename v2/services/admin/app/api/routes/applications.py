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
from v2.shared.db.models import Application, ApplicationEvidence, Drawing, OperatorTicket, User
from v2.shared.domain.enums import ApplicationStatus, EvidenceType, TicketStatus

router = APIRouter(prefix="/applications", tags=["applications"])


def _to_response(application: Application) -> ApplicationResponse:
    return ApplicationResponse(
        id=application.id,
        user_id=application.user_id,
        drawing_id=application.drawing_id,
        status=application.status,
        profile_attempts_used=application.profile_attempts_used,
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
    query = db.query(Application)
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
    rows = db.query(Application).filter(Application.user_id == user.id).order_by(Application.created_at.desc()).all()
    return [_to_response(row) for row in rows]


@router.post("/join", response_model=ApplicationResponse)
def join_drawing(payload: JoinApplicationRequest, db: Session = Depends(get_db)) -> ApplicationResponse:
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
    if existing is not None:
        return _to_response(existing)

    app = Application(
        user_id=user.id,
        drawing_id=drawing.id,
        status=ApplicationStatus.pending,
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
def moderate_profile(
    application_id: int, payload: ModerateApplicationRequest, db: Session = Depends(get_db)
) -> ApplicationResponse:
    application = db.query(Application).filter(Application.id == application_id).one_or_none()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    drawing = db.query(Drawing).filter(Drawing.id == application.drawing_id).one_or_none()
    if drawing is None:
        raise HTTPException(status_code=404, detail="Drawing not found")

    apply_profile_moderation(application, drawing, payload.approved, payload.reason)

    if application.profile_attempts_used >= 3:
        ticket = OperatorTicket(
            user_id=application.user_id,
            drawing_id=application.drawing_id,
            status=TicketStatus.open,
            message=application.blocked_reason or "Блокировка по профилю после 3 попыток",
        )
        db.add(ticket)

    db.commit()
    db.refresh(application)
    return _to_response(application)


@router.post("/{application_id}/moderate-payment", response_model=ApplicationResponse)
def moderate_payment(
    application_id: int, payload: ModerateApplicationRequest, db: Session = Depends(get_db)
) -> ApplicationResponse:
    application = db.query(Application).filter(Application.id == application_id).one_or_none()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    apply_payment_moderation(application, payload.approved, payload.reason)

    if application.payment_attempts_used >= 3:
        ticket = OperatorTicket(
            user_id=application.user_id,
            drawing_id=application.drawing_id,
            status=TicketStatus.open,
            message=application.blocked_reason or "Блокировка по оплате после 3 попыток",
        )
        db.add(ticket)

    db.commit()
    db.refresh(application)
    return _to_response(application)
