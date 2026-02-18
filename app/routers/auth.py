from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import SessionToken, User
from app.schemas import LoginRequest, RegisterRequest
from app.security import hash_password, new_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(409, "Username already taken")
    db.add(
        User(
            username=payload.username,
            password_hash=hash_password(payload.password),
            display_name=payload.display_name,
            country=payload.country,
        )
    )
    db.commit()
    return {"message": "Registered successfully"}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    token_value = new_token()
    db.add(SessionToken(token=token_value, user_id=user.id))
    db.commit()
    return {"token": token_value, "is_admin": user.is_admin}
