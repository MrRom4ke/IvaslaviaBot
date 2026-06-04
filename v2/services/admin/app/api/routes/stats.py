from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from v2.services.admin.app.api.deps import get_current_admin, get_db
from v2.shared.db.models import Admin, Application
from v2.shared.domain.enums import ApplicationStatus

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
def stats_overview() -> dict:
    return {"note": "TODO: implement statistics"}


@router.get("/pending-count")
def get_pending_applications_count(
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
) -> dict:
    """Получить количество заявок, ожидающих модерации."""
    pending_profile = (
        db.query(func.count(Application.id))
        .filter(Application.status == ApplicationStatus.pending)
        .scalar()
    )

    pending_payment = (
        db.query(func.count(Application.id))
        .filter(Application.status == ApplicationStatus.payment_bill_loaded)
        .scalar()
    )

    return {
        "pending_profile": pending_profile or 0,
        "pending_payment": pending_payment or 0,
        "total_pending": (pending_profile or 0) + (pending_payment or 0),
    }
