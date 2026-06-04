import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from v2.shared.db.models import AdminAuditLog


class AuditService:
    """Сервис для записи аудит-логов действий администраторов."""

    @staticmethod
    def log_action(
        db: Session,
        admin_id: int,
        admin_username: str,
        action: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AdminAuditLog:
        """Записывает действие администратора в аудит-лог."""
        log_entry = AdminAuditLog(
            admin_id=admin_id,
            admin_username=admin_username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps(details, ensure_ascii=False) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
        )
        db.add(log_entry)
        db.commit()
        return log_entry

    @staticmethod
    def get_logs(
        db: Session,
        admin_id: int | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AdminAuditLog]:
        """Получает список аудит-логов с фильтрацией."""
        query = db.query(AdminAuditLog)

        if admin_id is not None:
            query = query.filter(AdminAuditLog.admin_id == admin_id)
        if action is not None:
            query = query.filter(AdminAuditLog.action == action)
        if entity_type is not None:
            query = query.filter(AdminAuditLog.entity_type == entity_type)

        query = query.order_by(AdminAuditLog.created_at.desc())
        query = query.limit(limit).offset(offset)

        return query.all()

    @staticmethod
    def count_logs(
        db: Session,
        admin_id: int | None = None,
        action: str | None = None,
        entity_type: str | None = None,
    ) -> int:
        """Подсчитывает количество логов с заданными фильтрами."""
        query = db.query(AdminAuditLog)

        if admin_id is not None:
            query = query.filter(AdminAuditLog.admin_id == admin_id)
        if action is not None:
            query = query.filter(AdminAuditLog.action == action)
        if entity_type is not None:
            query = query.filter(AdminAuditLog.entity_type == entity_type)

        return query.count()


audit_service = AuditService()
