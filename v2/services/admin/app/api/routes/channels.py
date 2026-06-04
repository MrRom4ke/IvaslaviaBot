from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from v2.services.admin.app.api.deps import get_current_admin, get_db
from v2.shared.db.models import Admin, Drawing, RequiredChannel

router = APIRouter(prefix="/drawings/{drawing_id}/channels", tags=["channels"])


class RequiredChannelCreate(BaseModel):
    channel_id: int
    channel_username: str | None = None
    channel_title: str


class RequiredChannelResponse(BaseModel):
    id: int
    drawing_id: int
    channel_id: int
    channel_username: str | None
    channel_title: str


@router.get("", response_model=list[RequiredChannelResponse])
def list_required_channels(
    drawing_id: int,
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
) -> list[RequiredChannelResponse]:
    """Получить список обязательных каналов для розыгрыша."""
    # Проверяем, что розыгрыш существует
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).one_or_none()
    if drawing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drawing not found")

    channels = db.query(RequiredChannel).filter(RequiredChannel.drawing_id == drawing_id).all()

    return [
        RequiredChannelResponse(
            id=ch.id,
            drawing_id=ch.drawing_id,
            channel_id=ch.channel_id,
            channel_username=ch.channel_username,
            channel_title=ch.channel_title,
        )
        for ch in channels
    ]


@router.post("", response_model=RequiredChannelResponse, status_code=status.HTTP_201_CREATED)
def add_required_channel(
    drawing_id: int,
    payload: RequiredChannelCreate,
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
) -> RequiredChannelResponse:
    """Добавить обязательный канал для розыгрыша."""
    # Проверяем, что розыгрыш существует
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).one_or_none()
    if drawing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drawing not found")

    channel = RequiredChannel(
        drawing_id=drawing_id,
        channel_id=payload.channel_id,
        channel_username=payload.channel_username,
        channel_title=payload.channel_title,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)

    return RequiredChannelResponse(
        id=channel.id,
        drawing_id=channel.drawing_id,
        channel_id=channel.channel_id,
        channel_username=channel.channel_username,
        channel_title=channel.channel_title,
    )


@router.delete("/{channel_id}")
def delete_required_channel(
    drawing_id: int,
    channel_id: int,
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
) -> dict:
    """Удалить обязательный канал."""
    channel = (
        db.query(RequiredChannel)
        .filter(RequiredChannel.id == channel_id, RequiredChannel.drawing_id == drawing_id)
        .one_or_none()
    )

    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

    db.delete(channel)
    db.commit()

    return {"message": "Channel deleted successfully"}
