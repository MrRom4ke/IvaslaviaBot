from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from v2.services.admin.app.api.deps import get_current_admin, get_db
from v2.services.admin.app.schemas.tickets import CreateOperatorTicketRequest, OperatorTicketResponse
from v2.services.admin.app.services.notification_service import notification_service
from v2.shared.db.models import Admin, Drawing, OperatorTicket, User
from v2.shared.domain.enums import TicketStatus

router = APIRouter(prefix="/operator-tickets", tags=["operator-tickets"])


class TicketDetailResponse(BaseModel):
    id: int
    user_id: int
    user_telegram_id: int
    user_full_name: str
    user_username: str | None
    drawing_id: int | None
    drawing_title: str | None
    status: str
    message: str | None
    created_at: str


class ReplyToTicketRequest(BaseModel):
    reply_message: str
    close_ticket: bool = False


@router.get("")
def list_tickets(
    status_filter: TicketStatus | None = None,
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
) -> list[TicketDetailResponse]:
    query = (
        db.query(OperatorTicket, User, Drawing)
        .join(User, OperatorTicket.user_id == User.id)
        .outerjoin(Drawing, OperatorTicket.drawing_id == Drawing.id)
    )

    if status_filter:
        query = query.filter(OperatorTicket.status == status_filter)

    rows = query.order_by(OperatorTicket.created_at.desc()).limit(100).all()

    return [
        TicketDetailResponse(
            id=ticket.id,
            user_id=user.id,
            user_telegram_id=user.telegram_id,
            user_full_name=user.full_name,
            user_username=user.username,
            drawing_id=ticket.drawing_id,
            drawing_title=drawing.title if drawing else None,
            status=ticket.status.value,
            message=ticket.message,
            created_at=ticket.created_at.isoformat(),
        )
        for ticket, user, drawing in rows
    ]


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


@router.post("/{ticket_id}/reply")
async def reply_to_ticket(
    ticket_id: int,
    payload: ReplyToTicketRequest,
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
) -> dict:
    """Ответить на тикет и отправить сообщение пользователю."""
    ticket = db.query(OperatorTicket).filter(OperatorTicket.id == ticket_id).one_or_none()
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    user = db.query(User).filter(User.id == ticket.user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Отправляем сообщение пользователю
    success = await notification_service.send_message(
        chat_id=user.telegram_id,
        text=f"💬 <b>Ответ от оператора:</b>\n\n{payload.reply_message}"
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message to user"
        )

    # Закрываем тикет если требуется
    if payload.close_ticket:
        ticket.status = TicketStatus.closed
        db.commit()

    return {"message": "Reply sent successfully", "ticket_closed": payload.close_ticket}


@router.patch("/{ticket_id}/status")
def update_ticket_status(
    ticket_id: int,
    new_status: TicketStatus,
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
) -> dict:
    """Изменить статус тикета."""
    ticket = db.query(OperatorTicket).filter(OperatorTicket.id == ticket_id).one_or_none()
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    ticket.status = new_status
    db.commit()

    return {"message": "Ticket status updated", "new_status": new_status.value}
