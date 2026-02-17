from __future__ import annotations

from typing import Generator

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import SessionToken, User


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(db: Session = Depends(get_db), authorization: str | None = Header(default=None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing auth token")
    token_value = authorization.replace("Bearer ", "", 1)
    token = db.get(SessionToken, token_value)
    if token is None:
        raise HTTPException(401, "Invalid token")
    user = db.get(User, token.user_id)
    if user is None:
        raise HTTPException(401, "User not found")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, "Admin access required")
    return user
