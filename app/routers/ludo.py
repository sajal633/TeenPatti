from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user
from app.models import User
from app.schemas import LudoAddBotsRequest, LudoCreateTableRequest, LudoMoveRequest
from app.services.runtime import ludo_manager

router = APIRouter(prefix="/api/ludo", tags=["ludo"])


@router.get("/tables")
def list_tables() -> list[dict]:
    return ludo_manager.list_tables()


@router.post("/tables")
def create_table(payload: LudoCreateTableRequest, _: User = Depends(get_current_user)) -> dict:
    return ludo_manager.create_table(payload.name)


@router.post("/join/{table_id}")
def join_table(table_id: int, user: User = Depends(get_current_user)) -> dict:
    try:
        return ludo_manager.join_table(table_id, str(user.id), user.display_name)
    except KeyError as exc:
        raise HTTPException(404, "Table not found") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/start/{table_id}")
def start_game(table_id: int, _: User = Depends(get_current_user)) -> dict:
    try:
        return ludo_manager.start_game(table_id)
    except KeyError as exc:
        raise HTTPException(404, "Table not found") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/roll")
def roll_dice(user: User = Depends(get_current_user)) -> dict:
    try:
        return ludo_manager.roll_dice(str(user.id))
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/move")
def move_token(payload: LudoMoveRequest, user: User = Depends(get_current_user)) -> dict:
    try:
        return ludo_manager.move_token(str(user.id), payload.token_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/bots/{table_id}")
def add_bots(table_id: int, payload: LudoAddBotsRequest, _: User = Depends(get_current_user)) -> dict:
    try:
        return ludo_manager.add_bots(table_id, payload.count)
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/state/{table_id}")
def state(table_id: int, user: User = Depends(get_current_user)) -> dict:
    try:
        return ludo_manager.get_state(table_id, str(user.id))
    except KeyError as exc:
        raise HTTPException(404, "Table not found") from exc
