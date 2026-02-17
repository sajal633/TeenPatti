from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import User
from app.schemas import ProfileUpdateRequest

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/me")
def get_me(user: User = Depends(get_current_user)) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "country": user.country,
        "avatar_url": user.avatar_url,
        "chips": user.chips,
        "is_admin": user.is_admin,
    }


@router.put("/me")
def update_me(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    user.display_name = payload.display_name
    user.country = payload.country
    user.avatar_url = payload.avatar_url
    db.add(user)
    db.commit()
    return {"message": "Profile updated"}
