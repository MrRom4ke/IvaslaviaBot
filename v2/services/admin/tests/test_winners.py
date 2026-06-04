import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from v2.services.admin.app.core.security import get_password_hash
from v2.shared.db.models import Admin, Application, ApplicationEvidence, Drawing, User
from v2.shared.domain.enums import ApplicationStatus, DrawingStatus, DrawingType, EvidenceType


@pytest.fixture
def admin_token(client: TestClient, db: Session) -> str:
    """Создает админа и возвращает его токен."""
    admin = Admin(
        username="testadmin",
        hashed_password=get_password_hash("password"),
        full_name="Test Admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()

    response = client.post("/auth/login", json={"username": "testadmin", "password": "password"})
    return response.json()["access_token"]


class TestWinners:
    """Тесты выбора победителей."""

    def test_select_winners_success(self, client: TestClient, db: Session, admin_token: str):
        """Тест успешного выбора победителей."""
        # Создаем розыгрыш
        drawing = Drawing(
            title="Test Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.ready_to_draw,
            max_participants=100,
            winners_limit=2,
        )
        db.add(drawing)
        db.commit()

        # Создаем пользователей и заявки
        for i in range(5):
            user = User(
                telegram_id=100000 + i,
                full_name=f"User {i}",
                username=f"user{i}",
            )
            db.add(user)
            db.flush()

            app = Application(
                user_id=user.id,
                drawing_id=drawing.id,
                status=ApplicationStatus.completed,
            )
            db.add(app)

        db.commit()

        # Выбираем победителей
        response = client.post(
            f"/drawings/{drawing.id}/select-winners",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["drawing_id"] == drawing.id
        assert data["total_selected"] == 2
        assert len(data["winners"]) == 2

        # Проверяем, что статус розыгрыша изменился
        db.refresh(drawing)
        assert drawing.status == DrawingStatus.completed

    def test_select_winners_wrong_status(self, client: TestClient, db: Session, admin_token: str):
        """Тест выбора победителей для розыгрыша с неверным статусом."""
        drawing = Drawing(
            title="Active Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.active,  # Неверный статус
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()

        response = client.post(
            f"/drawings/{drawing.id}/select-winners",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert "ready_to_draw" in response.json()["detail"]

    def test_select_winners_no_completed_applications(self, client: TestClient, db: Session, admin_token: str):
        """Тест выбора победителей без завершенных заявок."""
        drawing = Drawing(
            title="Empty Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.ready_to_draw,
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()

        response = client.post(
            f"/drawings/{drawing.id}/select-winners",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert "No completed applications" in response.json()["detail"]

    def test_select_winners_already_selected(self, client: TestClient, db: Session, admin_token: str):
        """Тест повторного выбора победителей."""
        # Создаем розыгрыш
        drawing = Drawing(
            title="Test Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.ready_to_draw,
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()

        # Создаем пользователя и заявку
        user = User(telegram_id=123456, full_name="User", username="user")
        db.add(user)
        db.flush()

        app = Application(
            user_id=user.id,
            drawing_id=drawing.id,
            status=ApplicationStatus.completed,
        )
        db.add(app)
        db.commit()

        # Первый выбор победителей
        response1 = client.post(
            f"/drawings/{drawing.id}/select-winners",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response1.status_code == 200

        # Возвращаем статус обратно для теста
        drawing.status = DrawingStatus.ready_to_draw
        db.commit()

        # Второй выбор (должен вернуть ошибку)
        response2 = client.post(
            f"/drawings/{drawing.id}/select-winners",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response2.status_code == 400
        assert "already selected" in response2.json()["detail"]

    def test_select_winners_limit_more_than_applications(self, client: TestClient, db: Session, admin_token: str):
        """Тест выбора победителей когда лимит больше количества заявок."""
        drawing = Drawing(
            title="Small Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.ready_to_draw,
            max_participants=100,
            winners_limit=10,  # Лимит больше чем заявок
        )
        db.add(drawing)
        db.commit()

        # Создаем только 3 заявки
        for i in range(3):
            user = User(
                telegram_id=200000 + i,
                full_name=f"User {i}",
                username=f"user{i}",
            )
            db.add(user)
            db.flush()

            app = Application(
                user_id=user.id,
                drawing_id=drawing.id,
                status=ApplicationStatus.completed,
            )
            db.add(app)

        db.commit()

        response = client.post(
            f"/drawings/{drawing.id}/select-winners",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # Должно выбрать только 3 победителя (все доступные)
        assert data["total_selected"] == 3

    def test_get_winners(self, client: TestClient, db: Session, admin_token: str):
        """Тест получения списка победителей."""
        # Создаем розыгрыш
        drawing = Drawing(
            title="Test Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.ready_to_draw,
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()

        # Создаем пользователя и заявку
        user = User(telegram_id=999999, full_name="Winner User", username="winner")
        db.add(user)
        db.flush()

        app = Application(
            user_id=user.id,
            drawing_id=drawing.id,
            status=ApplicationStatus.completed,
        )
        db.add(app)
        db.commit()

        # Выбираем победителей
        client.post(
            f"/drawings/{drawing.id}/select-winners",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Получаем список победителей (публичный эндпоинт)
        response = client.get(f"/drawings/{drawing.id}/winners")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["telegram_id"] == 999999
        assert data[0]["full_name"] == "Winner User"

    def test_get_participants_with_profile_photo(self, client: TestClient, db: Session, admin_token: str):
        """Участники для ручного выбора содержат URL фото профиля."""
        drawing = Drawing(
            title="Manual Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.ready_to_draw,
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()

        user = User(telegram_id=555555, full_name="Participant", username="participant")
        db.add(user)
        db.flush()

        app = Application(
            user_id=user.id,
            drawing_id=drawing.id,
            status=ApplicationStatus.completed,
        )
        db.add(app)
        db.flush()

        db.add(
            ApplicationEvidence(
                application_id=app.id,
                evidence_type=EvidenceType.profile,
                file_key="profiles/test_photo.jpg",
            )
        )
        db.commit()

        response = client.get(
            f"/drawings/{drawing.id}/participants",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["profile_photo_url"] == "/storage/files/profiles/test_photo.jpg"

    def test_get_winners_empty(self, client: TestClient, db: Session):
        """Тест получения пустого списка победителей."""
        drawing = Drawing(
            title="No Winners Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.active,
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()

        response = client.get(f"/drawings/{drawing.id}/winners")
        assert response.status_code == 200
        assert response.json() == []
