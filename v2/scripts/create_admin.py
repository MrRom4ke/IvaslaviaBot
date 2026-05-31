"""
Скрипт для создания первого admin-пользователя.
Запуск: python -m v2.scripts.create_admin
"""
import sys
from getpass import getpass

from v2.services.admin.app.core.security import get_password_hash
from v2.shared.db.models import Admin
from v2.shared.db.session import SessionLocal


def create_admin() -> None:
    print("=== Создание admin-пользователя ===")
    username = input("Username: ").strip()
    if not username:
        print("Username не может быть пустым")
        sys.exit(1)

    full_name = input("Full name: ").strip()
    if not full_name:
        print("Full name не может быть пустым")
        sys.exit(1)

    password = getpass("Password: ")
    password_confirm = getpass("Confirm password: ")

    if password != password_confirm:
        print("Пароли не совпадают")
        sys.exit(1)

    if len(password) < 6:
        print("Пароль должен быть не менее 6 символов")
        sys.exit(1)

    db = SessionLocal()
    try:
        existing = db.query(Admin).filter(Admin.username == username).one_or_none()
        if existing:
            print(f"Admin с username '{username}' уже существует")
            sys.exit(1)

        admin = Admin(
            username=username,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"\n✓ Admin создан успешно:")
        print(f"  ID: {admin.id}")
        print(f"  Username: {admin.username}")
        print(f"  Full name: {admin.full_name}")
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
