from datetime import datetime

from pydantic import BaseModel


class CreateOperatorTicketRequest(BaseModel):
    telegram_id: int
    full_name: str
    username: str | None = None
    drawing_id: int | None = None
    message: str | None = None


class OperatorTicketResponse(BaseModel):
    ticket_id: int
    status: str
    created_at: datetime
