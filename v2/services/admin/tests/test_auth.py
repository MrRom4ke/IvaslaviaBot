import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from v2.services.admin.app.core.security import get_password_hash
from v2.shared.db.models import Admin


class TestAuth:
    """Тесты авторизации и аутентификации."""

    def test_register_admin(self, client: TestClient):
        """Тест регистрации нового администратора."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testadmin",
                "password": "testpass123",
                "full_name": "Test Admin",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testadmin"
        assert data["full_name"] == "Test Admin"
        assert data["is_active"] is True
        assert "id" in data

    def test_register_duplicate_username(self, client: TestClient, db: Session):
        """Тест регистрации с существующим username."""
        # Создаем первого админа
        admin = Admin(
            username="existing",
            hashed_password=get_password_hash("password"),
            full_name="Existing Admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()

        # Пытаемся создать второго с тем же username
        response = client.post(
            "/auth/register",
            json={
                "username": "existing",
                "password": "newpass123",
                "full_name": "New Admin",
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_login_success(self, client: TestClient, db: Session):
        """Тест успешного входа."""
        # Создаем админа
        admin = Admin(
            username="logintest",
            hashed_password=get_password_hash("correctpass"),
            full_name="Login Test",
            is_active=True,
        )
        db.add(admin)
        db.commit()

        # Логинимся
        response = client.post(
            "/auth/login",
            json={
                "username": "logintest",
                "password": "correctpass",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, db: Session):
        """Тест входа с неверным паролем."""
        admin = Admin(
            username="logintest",
            hashed_password=get_password_hash("correctpass"),
            full_name="Login Test",
            is_active=True,
        )
        db.add(admin)
        db.commit()

        response = client.post(
            "/auth/login",
            json={
                "username": "logintest",
                "password": "wrongpass",
            },
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Тест входа несуществующего пользователя."""
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "anypass",
            },
        )
        assert response.status_code == 401

    def test_login_inactive_admin(self, client: TestClient, db: Session):
        """Тест входа неактивного администратора."""
        admin = Admin(
            username="inactive",
            hashed_password=get_password_hash("password"),
            full_name="Inactive Admin",
            is_active=False,
        )
        db.add(admin)
        db.commit()

        response = client.post(
            "/auth/login",
            json={
                "username": "inactive",
                "password": "password",
            },
        )
        assert response.status_code == 403

    def test_protected_endpoint_without_token(self, client: TestClient):
        """Тест доступа к защищенному эндпоинту без токена."""
        response = client.post(
            "/drawings",
            json={
                "title": "Test Drawing",
                "drawing_type": "free",
                "status": "active",
            },
        )
        assert response.status_code == 403

    def test_protected_endpoint_with_token(self, client: TestClient, db: Session):
        """Тест доступа к защищенному эндпоинту с токеном."""
        # Создаем админа и получаем токен
        admin = Admin(
            username="authorized",
            hashed_password=get_password_hash("password"),
            full_name="Authorized Admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()

        login_response = client.post(
            "/auth/login",
            json={"username": "authorized", "password": "password"},
        )
        token = login_response.json()["access_token"]

        # Используем токен для доступа к защищенному эндпоинту
        response = client.post(
            "/drawings",
            json={
                "title": "Test Drawing",
                "drawing_type": "free",
                "status": "active",
                "max_participants": 100,
                "winners_limit": 1,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Test Drawing"
