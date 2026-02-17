from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user
from app.models import User
from app.schemas import TwentyNineAddBotsRequest, TwentyNineBidRequest, TwentyNineCreateTableRequest, TwentyNinePlayRequest
from app.services.runtime import twentynine_manager

router = APIRouter(prefix="/api/twentynine", tags=["twentynine"])


@router.get("/tables")
def list_tables() -> list[dict]:
    return twentynine_manager.list_tables()


@router.post("/tables")
def create_table(payload: TwentyNineCreateTableRequest, _: User = Depends(get_current_user)) -> dict:
    return twentynine_manager.create_table(payload.name)


@router.post("/join/{table_id}")
def join_table(table_id: int, user: User = Depends(get_current_user)) -> dict:
    try:
        return twentynine_manager.join_table(table_id, str(user.id), user.display_name)
    except KeyError as exc:
        raise HTTPException(404, "Table not found") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/start/{table_id}")
def start_hand(table_id: int, _: User = Depends(get_current_user)) -> dict:
    try:
        return twentynine_manager.start_hand(table_id)
    except KeyError as exc:
        raise HTTPException(404, "Table not found") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/bid")
def place_bid(payload: TwentyNineBidRequest, user: User = Depends(get_current_user)) -> dict:
    try:
        return twentynine_manager.bid(str(user.id), payload.amount, payload.trump_suit)
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/play")
def play_card(payload: TwentyNinePlayRequest, user: User = Depends(get_current_user)) -> dict:
    try:
        return twentynine_manager.play_card(str(user.id), payload.card)
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/bots/{table_id}")
def add_bots(table_id: int, payload: TwentyNineAddBotsRequest, _: User = Depends(get_current_user)) -> dict:
    try:
        return twentynine_manager.add_bots(table_id, payload.count)
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/state/{table_id}")
def get_state(table_id: int, user: User = Depends(get_current_user)) -> dict:
    try:
        return twentynine_manager.get_state(table_id, str(user.id))
    except KeyError as exc:
        raise HTTPException(404, "Table not found") from exc
