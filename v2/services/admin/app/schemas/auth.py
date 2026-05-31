from datetime import datetime

from pydantic import BaseModel


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminCreateRequest(BaseModel):
    username: str
    password: str
    full_name: str


class AdminResponse(BaseModel):
    id: int
    username: str
    full_name: str
    is_active: bool
    created_at: datetime
