from __future__ import annotations

from fastapi import APIRouter

from app.services.runtime import manager

router = APIRouter(prefix="/api/lobby", tags=["lobby"])


@router.get("/tables")
def list_tables() -> list[dict]:
    return manager.list_tables()
