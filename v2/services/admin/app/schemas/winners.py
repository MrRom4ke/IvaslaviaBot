from datetime import datetime

from pydantic import BaseModel


class SelectWinnersRequest(BaseModel):
    drawing_id: int


class WinnerInfo(BaseModel):
    user_id: int
    telegram_id: int
    full_name: str
    username: str | None
    selected_at: datetime


class SelectWinnersResponse(BaseModel):
    drawing_id: int
    winners: list[WinnerInfo]
    total_selected: int
