from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from v2.services.admin.app.api.deps import get_current_admin, get_db
from v2.services.admin.app.schemas.audit import AdminAuditLogResponse, AuditLogsListResponse
from v2.services.admin.app.services.audit_service import audit_service
from v2.shared.db.models import Admin

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=AuditLogsListResponse)
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    admin_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
) -> AuditLogsListResponse:
    """Получить список аудит-логов (только для чтения, редактирование запрещено)."""
    offset = (page - 1) * page_size

    logs = audit_service.get_logs(
        db=db,
        admin_id=admin_id,
        action=action,
        entity_type=entity_type,
        limit=page_size,
        offset=offset,
    )

    total = audit_service.count_logs(
        db=db,
        admin_id=admin_id,
        action=action,
        entity_type=entity_type,
    )

    return AuditLogsListResponse(
        items=[AdminAuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )
