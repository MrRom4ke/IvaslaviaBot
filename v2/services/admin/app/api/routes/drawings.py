from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from v2.services.admin.app.api.deps import get_db
from v2.services.admin.app.schemas.drawings import DrawingCreateRequest, DrawingResponse, DrawingUpdateRequest
from v2.shared.db.models import Application, Drawing
from v2.shared.domain.enums import ApplicationStatus, DrawingStatus

router = APIRouter(prefix="/drawings", tags=["drawings"])


@router.get("", response_model=list[DrawingResponse])
def list_drawings(status: DrawingStatus | None = None, db: Session = Depends(get_db)) -> list[DrawingResponse]:
    query = db.query(Drawing)
    if status is not None:
        query = query.filter(Drawing.status == status)
    rows = query.order_by(Drawing.created_at.desc()).all()
    return [
        DrawingResponse(
            id=row.id,
            title=row.title,
            description=row.description,
            drawing_type=row.drawing_type,
            status=row.status,
            max_participants=row.max_participants,
            winners_limit=row.winners_limit,
            start_at=row.start_at,
            end_at=row.end_at,
        )
        for row in rows
    ]


@router.post("", response_model=DrawingResponse)
def create_drawing(payload: DrawingCreateRequest, db: Session = Depends(get_db)) -> DrawingResponse:
    drawing = Drawing(
        title=payload.title,
        description=payload.description,
        drawing_type=payload.drawing_type,
        status=payload.status,
        max_participants=payload.max_participants,
        winners_limit=payload.winners_limit,
        start_at=payload.start_at,
        end_at=payload.end_at,
    )
    db.add(drawing)
    db.commit()
    db.refresh(drawing)
    return DrawingResponse(
        id=drawing.id,
        title=drawing.title,
        description=drawing.description,
        drawing_type=drawing.drawing_type,
        status=drawing.status,
        max_participants=drawing.max_participants,
        winners_limit=drawing.winners_limit,
        start_at=drawing.start_at,
        end_at=drawing.end_at,
    )


@router.patch("/{drawing_id}", response_model=DrawingResponse)
def update_drawing(drawing_id: int, payload: DrawingUpdateRequest, db: Session = Depends(get_db)) -> DrawingResponse:
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).one_or_none()
    if drawing is None:
        raise HTTPException(status_code=404, detail="Drawing not found")

    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(drawing, field_name, value)

    db.commit()
    db.refresh(drawing)
    return DrawingResponse(
        id=drawing.id,
        title=drawing.title,
        description=drawing.description,
        drawing_type=drawing.drawing_type,
        status=drawing.status,
        max_participants=drawing.max_participants,
        winners_limit=drawing.winners_limit,
        start_at=drawing.start_at,
        end_at=drawing.end_at,
    )


@router.delete("/{drawing_id}")
def delete_drawing(drawing_id: int, db: Session = Depends(get_db)) -> dict:
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).one_or_none()
    if drawing is None:
        raise HTTPException(status_code=404, detail="Drawing not found")

    db.delete(drawing)
    db.commit()
    return {"message": "Drawing deleted successfully"}


@router.get("/{drawing_id}/stats")
def get_drawing_stats(drawing_id: int, db: Session = Depends(get_db)) -> dict:
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).one_or_none()
    if drawing is None:
        raise HTTPException(status_code=404, detail="Drawing not found")

    # Подсчитываем количество заявок по статусам
    total_participants = db.query(func.count(Application.id)).filter(Application.drawing_id == drawing_id).scalar()

    pending = db.query(func.count(Application.id)).filter(
        Application.drawing_id == drawing_id,
        Application.status == ApplicationStatus.pending
    ).scalar()

    approved = db.query(func.count(Application.id)).filter(
        Application.drawing_id == drawing_id,
        Application.status == ApplicationStatus.approved
    ).scalar()

    rejected = db.query(func.count(Application.id)).filter(
        Application.drawing_id == drawing_id,
        Application.status == ApplicationStatus.rejected
    ).scalar()

    payment_pending = db.query(func.count(Application.id)).filter(
        Application.drawing_id == drawing_id,
        Application.status == ApplicationStatus.payment_pending
    ).scalar()

    payment_bill_loaded = db.query(func.count(Application.id)).filter(
        Application.drawing_id == drawing_id,
        Application.status == ApplicationStatus.payment_bill_loaded
    ).scalar()

    payment_confirmed = db.query(func.count(Application.id)).filter(
        Application.drawing_id == drawing_id,
        Application.status == ApplicationStatus.payment_confirmed
    ).scalar()

    payment_rejected = db.query(func.count(Application.id)).filter(
        Application.drawing_id == drawing_id,
        Application.status == ApplicationStatus.payment_rejected
    ).scalar()

    completed = db.query(func.count(Application.id)).filter(
        Application.drawing_id == drawing_id,
        Application.status == ApplicationStatus.completed
    ).scalar()

    return {
        "drawing_id": drawing_id,
        "total_participants": total_participants or 0,
        "max_participants": drawing.max_participants,
        "pending": pending or 0,
        "approved": approved or 0,
        "rejected": rejected or 0,
        "payment_pending": payment_pending or 0,
        "payment_bill_loaded": payment_bill_loaded or 0,
        "payment_confirmed": payment_confirmed or 0,
        "payment_rejected": payment_rejected or 0,
        "completed": completed or 0,
    }
