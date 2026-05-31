from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from v2.services.admin.app.api.deps import get_db
from v2.services.admin.app.schemas.tickets import CreateOperatorTicketRequest, OperatorTicketResponse
from v2.shared.db.models import OperatorTicket, User
from v2.shared.domain.enums import TicketStatus

router = APIRouter(prefix="/operator-tickets", tags=["operator-tickets"])


@router.get("")
def list_tickets(db: Session = Depends(get_db)) -> dict:
    rows = db.query(OperatorTicket).order_by(OperatorTicket.created_at.desc()).limit(100).all()
    return {
        "items": [
            {
                "id": row.id,
                "user_id": row.user_id,
                "drawing_id": row.drawing_id,
                "status": row.status.value,
                "message": row.message,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }


@router.post("", response_model=OperatorTicketResponse)
def create_ticket(payload: CreateOperatorTicketRequest, db: Session = Depends(get_db)) -> OperatorTicketResponse:
    user = db.query(User).filter(User.telegram_id == payload.telegram_id).one_or_none()
    if user is None:
        user = User(
            telegram_id=payload.telegram_id,
            full_name=payload.full_name,
            username=payload.username,
        )
        db.add(user)
        db.flush()

    ticket = OperatorTicket(
        user_id=user.id,
        drawing_id=payload.drawing_id,
        status=TicketStatus.open,
        message=payload.message,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return OperatorTicketResponse(
        ticket_id=ticket.id,
        status=ticket.status.value,
        created_at=ticket.created_at,
    )
