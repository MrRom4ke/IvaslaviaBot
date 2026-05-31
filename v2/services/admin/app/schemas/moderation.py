from datetime import datetime

from pydantic import BaseModel

from v2.shared.domain.enums import ApplicationStatus, EvidenceType


class ModerationQueueItem(BaseModel):
    application_id: int
    user_id: int
    drawing_id: int
    drawing_title: str
    telegram_id: int
    full_name: str
    username: str | None
    application_status: ApplicationStatus
    evidence_type: EvidenceType
    evidence_id: int
    file_key: str
    evidence_created_at: datetime
    profile_attempts_used: int
    payment_attempts_used: int


class ModerationQueueResponse(BaseModel):
    items: list[ModerationQueueItem]
    total: int
