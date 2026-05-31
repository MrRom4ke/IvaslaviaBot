import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from v2.services.admin.app.core.security import get_password_hash
from v2.shared.db.models import Admin, Application, Drawing, User
from v2.shared.domain.enums import ApplicationStatus, DrawingStatus, DrawingType


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


@pytest.fixture
def test_user(db: Session) -> User:
    """Создает тестового пользователя."""
    user = User(
        telegram_id=123456789,
        full_name="Test User",
        username="testuser",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_drawing(db: Session) -> Drawing:
    """Создает тестовый розыгрыш."""
    drawing = Drawing(
        title="Test Drawing",
        description="Test Description",
        drawing_type=DrawingType.free,
        status=DrawingStatus.active,
        max_participants=100,
        winners_limit=1,
    )
    db.add(drawing)
    db.commit()
    db.refresh(drawing)
    return drawing


class TestApplications:
    """Тесты для заявок на участие."""

    def test_join_drawing(self, client: TestClient, db: Session, test_drawing: Drawing):
        """Тест создания заявки на участие."""
        response = client.post(
            "/applications/join",
            json={
                "telegram_id": 999888777,
                "full_name": "New User",
                "username": "newuser",
                "drawing_id": test_drawing.id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["drawing_id"] == test_drawing.id
        assert data["status"] == ApplicationStatus.pending

    def test_join_drawing_twice(self, client: TestClient, db: Session, test_user: User, test_drawing: Drawing):
        """Тест повторной заявки на тот же розыгрыш."""
        # Первая заявка
        response1 = client.post(
            "/applications/join",
            json={
                "telegram_id": test_user.telegram_id,
                "full_name": test_user.full_name,
                "username": test_user.username,
                "drawing_id": test_drawing.id,
            },
        )
        assert response1.status_code == 200
        app_id = response1.json()["id"]

        # Вторая заявка (должна вернуть существующую)
        response2 = client.post(
            "/applications/join",
            json={
                "telegram_id": test_user.telegram_id,
                "full_name": test_user.full_name,
                "username": test_user.username,
                "drawing_id": test_drawing.id,
            },
        )
        assert response2.status_code == 200
        assert response2.json()["id"] == app_id

    def test_list_applications(self, client: TestClient, db: Session, test_user: User, test_drawing: Drawing):
        """Тест получения списка заявок."""
        # Создаем заявку
        app = Application(
            user_id=test_user.id,
            drawing_id=test_drawing.id,
            status=ApplicationStatus.pending,
        )
        db.add(app)
        db.commit()

        response = client.get("/applications")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == test_user.id

    def test_list_my_applications(self, client: TestClient, db: Session, test_user: User, test_drawing: Drawing):
        """Тест получения заявок пользователя."""
        # Создаем заявку
        app = Application(
            user_id=test_user.id,
            drawing_id=test_drawing.id,
            status=ApplicationStatus.pending,
        )
        db.add(app)
        db.commit()

        response = client.get(f"/applications/my?telegram_id={test_user.telegram_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["drawing_id"] == test_drawing.id


class TestModeration:
    """Тесты модерации заявок."""

    def test_moderate_profile_approve_free(
        self, client: TestClient, db: Session, admin_token: str, test_user: User, test_drawing: Drawing
    ):
        """Тест одобрения профиля для бесплатного розыгрыша."""
        # Создаем заявку
        app = Application(
            user_id=test_user.id,
            drawing_id=test_drawing.id,
            status=ApplicationStatus.pending,
        )
        db.add(app)
        db.commit()

        response = client.post(
            f"/applications/{app.id}/moderate-profile",
            json={"approved": True, "reason": None},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ApplicationStatus.completed

    def test_moderate_profile_approve_paid(
        self, client: TestClient, db: Session, admin_token: str, test_user: User
    ):
        """Тест одобрения профиля для платного розыгрыша."""
        # Создаем платный розыгрыш
        drawing = Drawing(
            title="Paid Drawing",
            drawing_type=DrawingType.paid,
            status=DrawingStatus.active,
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()

        # Создаем заявку
        app = Application(
            user_id=test_user.id,
            drawing_id=drawing.id,
            status=ApplicationStatus.pending,
        )
        db.add(app)
        db.commit()

        response = client.post(
            f"/applications/{app.id}/moderate-profile",
            json={"approved": True, "reason": None},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ApplicationStatus.payment_pending

    def test_moderate_profile_reject(
        self, client: TestClient, db: Session, admin_token: str, test_user: User, test_drawing: Drawing
    ):
        """Тест отклонения профиля."""
        app = Application(
            user_id=test_user.id,
            drawing_id=test_drawing.id,
            status=ApplicationStatus.pending,
        )
        db.add(app)
        db.commit()

        response = client.post(
            f"/applications/{app.id}/moderate-profile",
            json={"approved": False, "reason": "Некорректный скриншот"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ApplicationStatus.rejected
        assert data["profile_attempts_used"] == 1
        assert "Некорректный скриншот" in data["blocked_reason"]

    def test_moderate_profile_reject_three_times(
        self, client: TestClient, db: Session, admin_token: str, test_user: User, test_drawing: Drawing
    ):
        """Тест блокировки после 3 отклонений профиля."""
        app = Application(
            user_id=test_user.id,
            drawing_id=test_drawing.id,
            status=ApplicationStatus.pending,
            profile_attempts_used=2,
        )
        db.add(app)
        db.commit()

        response = client.post(
            f"/applications/{app.id}/moderate-profile",
            json={"approved": False, "reason": "Третья попытка"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ApplicationStatus.rejected
        assert data["profile_attempts_used"] == 3

    def test_moderate_payment_approve(
        self, client: TestClient, db: Session, admin_token: str, test_user: User, test_drawing: Drawing
    ):
        """Тест одобрения оплаты."""
        app = Application(
            user_id=test_user.id,
            drawing_id=test_drawing.id,
            status=ApplicationStatus.payment_bill_loaded,
        )
        db.add(app)
        db.commit()

        response = client.post(
            f"/applications/{app.id}/moderate-payment",
            json={"approved": True, "reason": None},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ApplicationStatus.completed

    def test_moderate_payment_reject(
        self, client: TestClient, db: Session, admin_token: str, test_user: User, test_drawing: Drawing
    ):
        """Тест отклонения оплаты."""
        app = Application(
            user_id=test_user.id,
            drawing_id=test_drawing.id,
            status=ApplicationStatus.payment_bill_loaded,
        )
        db.add(app)
        db.commit()

        response = client.post(
            f"/applications/{app.id}/moderate-payment",
            json={"approved": False, "reason": "Неверная сумма"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ApplicationStatus.payment_pending
        assert data["payment_attempts_used"] == 1
