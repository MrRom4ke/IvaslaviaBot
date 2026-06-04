from datetime import datetime

from pydantic import BaseModel


class AdminAuditLogResponse(BaseModel):
    id: int
    admin_id: int
    admin_username: str
    action: str
    entity_type: str | None
    entity_id: int | None
    details: str | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogsListResponse(BaseModel):
    items: list[AdminAuditLogResponse]
    total: int
    page: int
    page_size: int
