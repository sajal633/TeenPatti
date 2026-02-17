from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import User
from app.schemas import ActionRequest, JoinTableRequest
from app.services.realtime import ws_manager
from app.services.runtime import manager

router = APIRouter(prefix="/api/game", tags=["game"])
ws_router = APIRouter(tags=["ws"])


@router.post("/join")
async def join_table(
    payload: JoinTableRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    if user.chips < payload.buyin:
        raise HTTPException(400, "Not enough chips")
    try:
        state = manager.join_table(payload.table_id, str(user.id), user.display_name, payload.buyin)
    except KeyError as exc:
        raise HTTPException(404, "Table not found") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    await ws_manager.broadcast(payload.table_id, {"type": "state", "state": state})
    return state


@router.post("/action")
async def action(payload: ActionRequest, user: User = Depends(get_current_user)) -> dict:
    try:
        state = manager.act(str(user.id), payload.action, payload.amount)
    except KeyError as exc:
        raise HTTPException(404, "Table session not found") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    await ws_manager.broadcast(state["table_id"], {"type": "state", "state": state})
    return state


@router.get("/table/{table_id}")
def table_state(table_id: int, user: User = Depends(get_current_user)) -> dict:
    try:
        return manager.get_table_state(table_id, for_player=str(user.id))
    except KeyError as exc:
        raise HTTPException(404, "Table not found") from exc


@ws_router.websocket("/ws/table/{table_id}")
async def table_socket(ws: WebSocket, table_id: int) -> None:
    await ws_manager.connect(table_id, ws)
    try:
        while True:
            _ = await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(table_id, ws)
