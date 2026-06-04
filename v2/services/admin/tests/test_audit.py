import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from v2.services.admin.app.core.security import get_password_hash
from v2.shared.db.models import Admin, AdminAuditLog, Drawing
from v2.shared.domain.enums import DrawingStatus, DrawingType


@pytest.fixture
def admin_token(client: TestClient, db: Session) -> tuple[str, Admin]:
    """Создает админа и возвращает его токен и объект."""
    admin = Admin(
        username="testadmin",
        hashed_password=get_password_hash("password"),
        full_name="Test Admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()

    response = client.post("/auth/login", json={"username": "testadmin", "password": "password"})
    return response.json()["access_token"], admin


class TestAuditLogs:
    """Тесты системы аудит-логов."""

    def test_audit_log_created_on_drawing_creation(self, client: TestClient, db: Session, admin_token: tuple[str, Admin]):
        """Тест создания аудит-лога при создании розыгрыша."""
        token, admin = admin_token

        payload = {
            "title": "New Drawing",
            "description": "Test description",
            "drawing_type": "free",
            "status": "active",
            "max_participants": 100,
            "winners_limit": 1,
        }

        response = client.post(
            "/drawings",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Проверяем, что лог создан
        log = db.query(AdminAuditLog).filter(
            AdminAuditLog.admin_id == admin.id,
            AdminAuditLog.action == "create_drawing",
        ).first()
        assert log is not None
        assert log.entity_type == "drawing"
        assert log.admin_username == "testadmin"

        # Проверяем детали
        if log.details:
            details = json.loads(log.details)
            assert details["title"] == "New Drawing"

    def test_audit_log_created_on_drawing_update(self, client: TestClient, db: Session, admin_token: tuple[str, Admin]):
        """Тест создания аудит-лога при обновлении розыгрыша."""
        token, admin = admin_token

        drawing = Drawing(
            title="Original Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.active,
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()

        payload = {
            "title": "Updated Drawing",
            "status": "completed",
        }

        response = client.patch(
            f"/drawings/{drawing.id}",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Проверяем, что лог создан
        log = db.query(AdminAuditLog).filter(
            AdminAuditLog.admin_id == admin.id,
            AdminAuditLog.action == "update_drawing",
        ).first()
        assert log is not None
        assert log.entity_type == "drawing"
        assert log.entity_id == drawing.id

    def test_audit_log_created_on_drawing_deletion(self, client: TestClient, db: Session, admin_token: tuple[str, Admin]):
        """Тест создания аудит-лога при удалении розыгрыша."""
        token, admin = admin_token

        drawing = Drawing(
            title="To Delete",
            drawing_type=DrawingType.free,
            status=DrawingStatus.active,
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()
        drawing_id = drawing.id

        response = client.delete(
            f"/drawings/{drawing_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Проверяем, что лог создан
        log = db.query(AdminAuditLog).filter(
            AdminAuditLog.admin_id == admin.id,
            AdminAuditLog.action == "delete_drawing",
        ).first()
        assert log is not None
        assert log.entity_type == "drawing"
        assert log.entity_id == drawing_id

    def test_get_audit_logs(self, client: TestClient, db: Session, admin_token: tuple[str, Admin]):
        """Тест получения списка аудит-логов."""
        token, admin = admin_token

        # Создаем несколько логов вручную
        for i in range(5):
            log = AdminAuditLog(
                admin_id=admin.id,
                admin_username=admin.username,
                action=f"test_action_{i}",
                entity_type="test",
                entity_id=i,
                details=json.dumps({"test": f"data_{i}"}),
            )
            db.add(log)
        db.commit()

        response = client.get(
            "/audit-logs?page=1&page_size=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5
        assert data["page"] == 1

    def test_get_audit_logs_with_filters(self, client: TestClient, db: Session, admin_token: tuple[str, Admin]):
        """Тест получения аудит-логов с фильтрами."""
        token, admin = admin_token

        # Создаем логи с разными действиями
        actions = ["create_drawing", "update_drawing", "delete_drawing"]
        for action in actions:
            log = AdminAuditLog(
                admin_id=admin.id,
                admin_username=admin.username,
                action=action,
                entity_type="drawing",
            )
            db.add(log)
        db.commit()

        # Фильтруем по действию
        response = client.get(
            "/audit-logs?action=create_drawing",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["action"] == "create_drawing"

    def test_get_audit_logs_pagination(self, client: TestClient, db: Session, admin_token: tuple[str, Admin]):
        """Тест пагинации аудит-логов."""
        token, admin = admin_token

        # Создаем 25 логов
        for i in range(25):
            log = AdminAuditLog(
                admin_id=admin.id,
                admin_username=admin.username,
                action=f"action_{i}",
                entity_type="test",
            )
            db.add(log)
        db.commit()

        # Первая страница
        response1 = client.get(
            "/audit-logs?page=1&page_size=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["items"]) == 10
        assert data1["total"] == 25

        # Вторая страница
        response2 = client.get(
            "/audit-logs?page=2&page_size=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) == 10

        # Третья страница
        response3 = client.get(
            "/audit-logs?page=3&page_size=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response3.status_code == 200
        data3 = response3.json()
        assert len(data3["items"]) == 5

    def test_audit_logs_readonly(self, client: TestClient, db: Session, admin_token: tuple[str, Admin]):
        """Тест что аудит-логи доступны только для чтения."""
        token, admin = admin_token

        log = AdminAuditLog(
            admin_id=admin.id,
            admin_username=admin.username,
            action="test_action",
            entity_type="test",
        )
        db.add(log)
        db.commit()

        # Попытка удалить лог (эндпоинт не существует)
        response = client.delete(
            f"/audit-logs/{log.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

        # Попытка обновить лог (эндпоинт не существует)
        response = client.patch(
            f"/audit-logs/{log.id}",
            json={"action": "modified"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
