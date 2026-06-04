"""
Сервис автоматизации для управления статусами розыгрышей и напоминаний.
"""
import asyncio
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from v2.shared.db.models import Application, Drawing
from v2.shared.domain.enums import ApplicationStatus, DrawingStatus

logger = logging.getLogger(__name__)


class AutomationService:
    """Сервис для автоматических задач."""

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.running = False

    async def start(self):
        """Запустить фоновые задачи."""
        self.running = True
        logger.info("Automation service started")

        # Запускаем периодическую проверку каждые 5 минут
        while self.running:
            try:
                await self.check_drawings_status()
            except Exception as exc:
                logger.exception("Error in automation service: %s", exc)

            # Ждём 5 минут до следующей проверки
            await asyncio.sleep(300)

    async def stop(self):
        """Остановить фоновые задачи."""
        self.running = False
        logger.info("Automation service stopped")

    async def check_drawings_status(self):
        """Проверить и обновить статусы розыгрышей."""
        db: Session = self.db_session_factory()
        try:
            now = datetime.utcnow()

            # Находим активные розыгрыши, у которых истекла дата окончания
            expired_drawings = (
                db.query(Drawing)
                .filter(
                    Drawing.status == DrawingStatus.active,
                    Drawing.end_at.isnot(None),
                    Drawing.end_at <= now,
                )
                .all()
            )

            for drawing in expired_drawings:
                # Проверяем, есть ли завершённые заявки
                completed_count = (
                    db.query(Application)
                    .filter(
                        Application.drawing_id == drawing.id,
                        Application.status == ApplicationStatus.completed,
                    )
                    .count()
                )

                if completed_count > 0:
                    # Есть участники - переводим в ready_to_draw
                    drawing.status = DrawingStatus.ready_to_draw
                    logger.info(
                        "Drawing #%s (%s) moved to ready_to_draw - %s completed applications",
                        drawing.id,
                        drawing.title,
                        completed_count,
                    )
                else:
                    # Нет участников - сразу завершаем
                    drawing.status = DrawingStatus.completed
                    logger.info(
                        "Drawing #%s (%s) completed with no participants",
                        drawing.id,
                        drawing.title,
                    )

            # Находим предстоящие розыгрыши, которые должны стать активными
            starting_drawings = (
                db.query(Drawing)
                .filter(
                    Drawing.status == DrawingStatus.upcoming,
                    Drawing.start_at.isnot(None),
                    Drawing.start_at <= now,
                )
                .all()
            )

            for drawing in starting_drawings:
                drawing.status = DrawingStatus.active
                logger.info(
                    "Drawing #%s (%s) activated",
                    drawing.id,
                    drawing.title,
                )

            if expired_drawings or starting_drawings:
                db.commit()
                logger.info(
                    "Updated %s drawings: %s expired, %s started",
                    len(expired_drawings) + len(starting_drawings),
                    len(expired_drawings),
                    len(starting_drawings),
                )

        except Exception as exc:
            logger.exception("Error checking drawings status: %s", exc)
            db.rollback()
        finally:
            db.close()

    async def get_pending_applications_count(self) -> int:
        """Получить количество заявок, ожидающих модерации."""
        db: Session = self.db_session_factory()
        try:
            count = (
                db.query(Application)
                .filter(Application.status == ApplicationStatus.pending)
                .count()
            )
            return count
        finally:
            db.close()
