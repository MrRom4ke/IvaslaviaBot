from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from v2.services.admin.app.api.deps import get_db
from v2.services.admin.app.core.security import create_access_token, get_password_hash, verify_password
from v2.services.admin.app.schemas.auth import AdminCreateRequest, AdminLoginRequest, AdminLoginResponse, AdminResponse
from v2.shared.db.models import Admin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AdminLoginResponse)
def login(payload: AdminLoginRequest, db: Session = Depends(get_db)) -> AdminLoginResponse:
    admin = db.query(Admin).filter(Admin.username == payload.username).one_or_none()
    if admin is None or not verify_password(payload.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive",
        )

    access_token = create_access_token(data={"sub": admin.username})
    return AdminLoginResponse(access_token=access_token)


@router.post("/register", response_model=AdminResponse)
def register(payload: AdminCreateRequest, db: Session = Depends(get_db)) -> AdminResponse:
    existing = db.query(Admin).filter(Admin.username == payload.username).one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    admin = Admin(
        username=payload.username,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    return AdminResponse(
        id=admin.id,
        username=admin.username,
        full_name=admin.full_name,
        is_active=admin.is_active,
        created_at=admin.created_at,
    )
