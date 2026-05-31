from datetime import datetime

from pydantic import BaseModel

from v2.shared.domain.enums import DrawingStatus, DrawingType


class DrawingCreateRequest(BaseModel):
    title: str
    description: str | None = None
    drawing_type: DrawingType
    max_participants: int = 0
    winners_limit: int = 1
    start_at: datetime | None = None
    end_at: datetime | None = None
    status: DrawingStatus = DrawingStatus.upcoming


class DrawingUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    drawing_type: DrawingType | None = None
    max_participants: int | None = None
    winners_limit: int | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    status: DrawingStatus | None = None


class DrawingResponse(BaseModel):
    id: int
    title: str
    description: str | None
    drawing_type: DrawingType
    status: DrawingStatus
    max_participants: int
    winners_limit: int
    start_at: datetime | None
    end_at: datetime | None

