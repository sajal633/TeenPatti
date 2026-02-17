from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db, require_admin
from app.models import AuditLog, User
from app.schemas import AddBotsRequest
from app.services.realtime import ws_manager
from app.services.runtime import manager

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> dict:
    total_users = len(db.scalars(select(User)).all())
    total_tables = len(manager.tables)
    active_tables = len([t for t in manager.tables.values() if t.hand_active])
    return {"total_users": total_users, "total_tables": total_tables, "active_tables": active_tables}


@router.post("/bots")
async def add_bots(
    payload: AddBotsRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> dict:
    try:
        manager.add_bot_players(payload.table_id, payload.count)
    except KeyError as exc:
        raise HTTPException(404, "Table not found") from exc

    db.add(
        AuditLog(
            actor_user_id=admin_user.id,
            action="add_bots",
            payload=f"table={payload.table_id},count={payload.count}",
        )
    )
    db.commit()
    state = manager.get_table_state(payload.table_id, for_player=str(admin_user.id))
    await ws_manager.broadcast(payload.table_id, {"type": "state", "state": state})
    return {"message": "Bots added", "state": state}
