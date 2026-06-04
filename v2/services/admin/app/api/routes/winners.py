import random

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from v2.services.admin.app.api.deps import get_current_admin, get_db
from v2.services.admin.app.schemas.winners import SelectWinnersResponse, WinnerInfo
from v2.services.admin.app.services.notification_service import notification_service
from v2.shared.db.models import Admin, Application, ApplicationEvidence, Drawing, User, Winner
from v2.shared.domain.enums import ApplicationStatus, DrawingStatus, EvidenceType

router = APIRouter(prefix="/drawings", tags=["winners"])


class ParticipantInfo(BaseModel):
    application_id: int
    user_id: int
    telegram_id: int
    full_name: str
    username: str | None
    status: ApplicationStatus
    profile_photo_url: str | None


class ManualSelectWinnersRequest(BaseModel):
    application_ids: list[int]


@router.get("/{drawing_id}/winners", response_model=list[WinnerInfo])
def get_winners(
    drawing_id: int,
    db: Session = Depends(get_db),
) -> list[WinnerInfo]:
    """
    Получить список победителей розыгрыша.
    Публичный эндпоинт (не требует авторизации).
    """
    winners = (
        db.query(Winner, User)
        .join(User, Winner.user_id == User.id)
        .filter(Winner.drawing_id == drawing_id)
        .all()
    )

    return [
        WinnerInfo(
            user_id=user.id,
            telegram_id=user.telegram_id,
            full_name=user.full_name,
            username=user.username,
            selected_at=winner.selected_at,
        )
        for winner, user in winners
    ]


@router.post("/{drawing_id}/select-winners", response_model=SelectWinnersResponse)
async def select_winners(
    drawing_id: int,
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
) -> SelectWinnersResponse:
    """
    Выбор победителей для розыгрыша (случайный выбор).
    Требования:
    - Статус розыгрыша должен быть ready_to_draw
    - Выбираются только из заявок со статусом completed
    - Случайный выбор до winners_limit
    """
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).one_or_none()
    if drawing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drawing not found")

    if drawing.status != DrawingStatus.ready_to_draw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Drawing must be in ready_to_draw status, current: {drawing.status}",
        )

    # Проверка, что победители еще не выбраны
    existing_winners_count = db.query(Winner).filter(Winner.drawing_id == drawing_id).count()
    if existing_winners_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Winners already selected for this drawing ({existing_winners_count} winners)",
        )

    # Получение всех completed заявок
    completed_applications = (
        db.query(Application)
        .filter(
            Application.drawing_id == drawing_id,
            Application.status == ApplicationStatus.completed,
        )
        .all()
    )

    if not completed_applications:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No completed applications found for this drawing",
        )

    # Случайный выбор победителей
    winners_limit = min(drawing.winners_limit, len(completed_applications))
    selected_applications = random.sample(completed_applications, winners_limit)

    # Получаем ID победителей для отправки уведомлений
    winner_user_ids = {app.user_id for app in selected_applications}

    # Создание записей Winner
    winners_info = []
    for app in selected_applications:
        user = db.query(User).filter(User.id == app.user_id).one()
        winner = Winner(
            drawing_id=drawing_id,
            user_id=app.user_id,
        )
        db.add(winner)
        winners_info.append(
            WinnerInfo(
                user_id=user.id,
                telegram_id=user.telegram_id,
                full_name=user.full_name,
                username=user.username,
                selected_at=winner.selected_at,
            )
        )

    # Обновление статуса розыгрыша
    drawing.status = DrawingStatus.completed
    db.commit()

    # Отправляем уведомления всем участникам
    for app in completed_applications:
        user = db.query(User).filter(User.id == app.user_id).one()
        won = app.user_id in winner_user_ids

        if won:
            await notification_service.notify_winner(
                telegram_id=user.telegram_id,
                drawing_title=drawing.title,
                drawing_description=drawing.description,
            )
        else:
            await notification_service.notify_drawing_completed(
                telegram_id=user.telegram_id,
                drawing_title=drawing.title,
                won=False,
            )

    return SelectWinnersResponse(
        drawing_id=drawing_id,
        winners=winners_info,
        total_selected=len(winners_info),
    )


@router.get("/{drawing_id}/participants", response_model=list[ParticipantInfo])
def get_participants(
    drawing_id: int,
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
) -> list[ParticipantInfo]:
    """
    Получить список всех участников розыгрыша со статусом completed.
    Используется для ручного выбора победителей.
    """
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).one_or_none()
    if drawing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drawing not found")

    participants = (
        db.query(Application, User)
        .join(User, Application.user_id == User.id)
        .filter(
            Application.drawing_id == drawing_id,
            Application.status == ApplicationStatus.completed,
        )
        .all()
    )

    result = []
    for app, user in participants:
        # Получаем последнее фото профиля для этой заявки
        profile_evidence = (
            db.query(ApplicationEvidence)
            .filter(
                ApplicationEvidence.application_id == app.id,
                ApplicationEvidence.evidence_type == EvidenceType.profile,
            )
            .order_by(ApplicationEvidence.created_at.desc())
            .first()
        )

        profile_photo_url = None
        if profile_evidence:
            profile_photo_url = f"/storage/files/{profile_evidence.file_key}"

        result.append(
            ParticipantInfo(
                application_id=app.id,
                user_id=user.id,
                telegram_id=user.telegram_id,
                full_name=user.full_name,
                username=user.username,
                status=app.status,
                profile_photo_url=profile_photo_url,
            )
        )

    return result


@router.post("/{drawing_id}/select-winners-manual", response_model=SelectWinnersResponse)
async def select_winners_manual(
    drawing_id: int,
    payload: ManualSelectWinnersRequest,
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
) -> SelectWinnersResponse:
    """
    Ручной выбор победителей для розыгрыша.
    Требования:
    - Статус розыгрыша должен быть ready_to_draw
    - Количество выбранных заявок должно соответствовать winners_limit
    """
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).one_or_none()
    if drawing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drawing not found")

    if drawing.status != DrawingStatus.ready_to_draw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Drawing must be in ready_to_draw status, current: {drawing.status}",
        )

    # Проверка, что победители еще не выбраны
    existing_winners_count = db.query(Winner).filter(Winner.drawing_id == drawing_id).count()
    if existing_winners_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Winners already selected for this drawing ({existing_winners_count} winners)",
        )

    # Проверка количества выбранных заявок
    if len(payload.application_ids) != drawing.winners_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Must select exactly {drawing.winners_limit} winners, got {len(payload.application_ids)}",
        )

    # Проверка, что все заявки существуют и имеют статус completed
    selected_applications = (
        db.query(Application)
        .filter(
            Application.id.in_(payload.application_ids),
            Application.drawing_id == drawing_id,
            Application.status == ApplicationStatus.completed,
        )
        .all()
    )

    if len(selected_applications) != len(payload.application_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some applications are invalid or not completed",
        )

    # Получаем все completed заявки для отправки уведомлений
    all_completed_applications = (
        db.query(Application)
        .filter(
            Application.drawing_id == drawing_id,
            Application.status == ApplicationStatus.completed,
        )
        .all()
    )

    # Получаем ID победителей
    winner_user_ids = {app.user_id for app in selected_applications}

    # Создание записей Winner
    winners_info = []
    for app in selected_applications:
        user = db.query(User).filter(User.id == app.user_id).one()
        winner = Winner(
            drawing_id=drawing_id,
            user_id=app.user_id,
        )
        db.add(winner)
        winners_info.append(
            WinnerInfo(
                user_id=user.id,
                telegram_id=user.telegram_id,
                full_name=user.full_name,
                username=user.username,
                selected_at=winner.selected_at,
            )
        )

    # Обновление статуса розыгрыша
    drawing.status = DrawingStatus.completed
    db.commit()

    # Отправляем уведомления всем участникам
    for app in all_completed_applications:
        user = db.query(User).filter(User.id == app.user_id).one()
        won = app.user_id in winner_user_ids

        if won:
            await notification_service.notify_winner(
                telegram_id=user.telegram_id,
                drawing_title=drawing.title,
                drawing_description=drawing.description,
            )
        else:
            await notification_service.notify_drawing_completed(
                telegram_id=user.telegram_id,
                drawing_title=drawing.title,
                won=False,
            )

    return SelectWinnersResponse(
        drawing_id=drawing_id,
        winners=winners_info,
        total_selected=len(winners_info),
    )
