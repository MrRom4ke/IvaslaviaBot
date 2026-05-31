from datetime import datetime

from pydantic import BaseModel

from v2.shared.domain.enums import ApplicationStatus, EvidenceType


class JoinApplicationRequest(BaseModel):
    telegram_id: int
    full_name: str
    username: str | None = None
    drawing_id: int


class UploadEvidenceRequest(BaseModel):
    evidence_type: EvidenceType
    file_key: str
    mime_type: str | None = None


class ModerateApplicationRequest(BaseModel):
    approved: bool
    reason: str | None = None


class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    drawing_id: int
    status: ApplicationStatus
    profile_attempts_used: int
    payment_attempts_used: int
    blocked_reason: str | None
    created_at: datetime
    updated_at: datetime

