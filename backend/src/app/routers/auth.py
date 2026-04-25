"""Auth endpoints — /api/auth/register /login /me."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from src.app.dependencies import get_current_user
from src.services.auth import (
    create_access_token,
    ensure_user_is_active,
    hash_password,
    verify_password,
)
from src.shared.config import get_base_settings
from src.shared.db import get_db
from src.shared.enums import UserRole, UserStatus

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    from src.shared.models.user import User

    username = payload.username.strip()
    email = payload.email.lower().strip()
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    exists = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if exists:
        raise HTTPException(status_code=409, detail="Username or email already exists")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(payload.password),
        role=UserRole.USER.value,
        status=UserStatus.ACTIVE.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        subject=str(user.id), role=user.role,
        secret_key=get_base_settings().APP_AUTH_SECRET_KEY,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id, "username": user.username, "email": user.email,
            "role": user.role, "status": user.status,
        },
    }


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    from src.shared.models.user import User

    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        ensure_user_is_active(user.status)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    user.last_login_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    token = create_access_token(
        subject=str(user.id), role=user.role,
        secret_key=get_base_settings().APP_AUTH_SECRET_KEY,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id, "username": user.username, "email": user.email,
            "role": user.role, "status": user.status,
        },
    }


@router.get("/me")
def auth_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "status": current_user.status,
    }
