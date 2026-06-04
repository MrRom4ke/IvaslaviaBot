import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from v2.services.admin.app.services.automation_service import AutomationService
from v2.shared.db.models import Drawing, User, Application
from v2.shared.domain.enums import DrawingStatus, DrawingType, ApplicationStatus


class TestAutomationService:
    """Тесты сервиса автоматизации."""

    @pytest.fixture
    def automation_service(self, db: Session):
        """Создает экземпляр сервиса автоматизации."""
        def session_factory():
            return db
        return AutomationService(db_session_factory=session_factory)

    @pytest.mark.asyncio
    async def test_auto_start_upcoming_drawings(self, db: Session, automation_service: AutomationService):
        """Тест автоматического запуска предстоящих розыгрышей."""
        # Создаем розыгрыш, который должен начаться
        past_time = datetime.utcnow() - timedelta(minutes=5)
        drawing = Drawing(
            title="Auto Start Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.upcoming,
            start_at=past_time,
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()
        drawing_id = drawing.id

        # Запускаем автоматизацию
        await automation_service.check_drawings_status()

        # Проверяем, что статус изменился (получаем объект заново)
        updated_drawing = db.query(Drawing).filter(Drawing.id == drawing_id).one()
        assert updated_drawing.status == DrawingStatus.active

    @pytest.mark.asyncio
    async def test_auto_end_expired_drawings(self, db: Session, automation_service: AutomationService):
        """Тест автоматического завершения истекших розыгрышей."""
        # Создаем розыгрыш, который должен завершиться
        past_time = datetime.utcnow() - timedelta(minutes=5)
        drawing = Drawing(
            title="Auto End Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.active,
            end_at=past_time,
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()
        drawing_id = drawing.id

        # Создаём хотя бы одну завершенную заявку
        user = User(
            telegram_id=100000,
            full_name="Test User",
            username="testuser",
        )
        db.add(user)
        db.flush()

        app = Application(
            user_id=user.id,
            drawing_id=drawing_id,
            status=ApplicationStatus.completed,
        )
        db.add(app)
        db.commit()

        # Запускаем автоматизацию
        await automation_service.check_drawings_status()

        # Проверяем, что статус изменился
        updated_drawing = db.query(Drawing).filter(Drawing.id == drawing_id).one()
        assert updated_drawing.status == DrawingStatus.ready_to_draw

    @pytest.mark.asyncio
    async def test_no_auto_start_for_future_drawings(self, db: Session, automation_service: AutomationService):
        """Тест что будущие розыгрыши не запускаются автоматически."""
        future_time = datetime.utcnow() + timedelta(hours=1)
        drawing = Drawing(
            title="Future Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.upcoming,
            start_at=future_time,
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()
        drawing_id = drawing.id

        await automation_service.check_drawings_status()

        updated_drawing = db.query(Drawing).filter(Drawing.id == drawing_id).one()
        assert updated_drawing.status == DrawingStatus.upcoming

    @pytest.mark.asyncio
    async def test_no_auto_end_for_active_drawings(self, db: Session, automation_service: AutomationService):
        """Тест что активные розыгрыши без end_at не завершаются."""
        drawing = Drawing(
            title="Active Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.active,
            end_at=None,  # Нет времени окончания
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()
        drawing_id = drawing.id

        await automation_service.check_drawings_status()

        updated_drawing = db.query(Drawing).filter(Drawing.id == drawing_id).one()
        assert updated_drawing.status == DrawingStatus.active

    @pytest.mark.asyncio
    async def test_auto_end_expired_drawing_no_participants(self, db: Session, automation_service: AutomationService):
        """Тест что розыгрыш без участников завершается со статусом completed."""
        past_time = datetime.utcnow() - timedelta(minutes=5)
        drawing = Drawing(
            title="Empty Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.active,
            end_at=past_time,
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()
        drawing_id = drawing.id

        await automation_service.check_drawings_status()

        updated_drawing = db.query(Drawing).filter(Drawing.id == drawing_id).one()
        assert updated_drawing.status == DrawingStatus.completed

    @pytest.mark.asyncio
    async def test_get_pending_applications_count(self, db: Session, automation_service: AutomationService):
        """Тест подсчёта заявок в ожидании."""
        drawing = Drawing(
            title="Test Drawing",
            drawing_type=DrawingType.free,
            status=DrawingStatus.active,
            max_participants=100,
            winners_limit=1,
        )
        db.add(drawing)
        db.commit()

        # Создаем несколько заявок
        for i in range(3):
            user = User(
                telegram_id=300000 + i,
                full_name=f"User {i}",
                username=f"user{i}",
            )
            db.add(user)
            db.flush()

            app = Application(
                user_id=user.id,
                drawing_id=drawing.id,
                status=ApplicationStatus.pending,
            )
            db.add(app)
        db.commit()

        count = await automation_service.get_pending_applications_count()
        assert count == 3
