from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME
from app.game import GameManager
from app.models import TableConfig, User
from app.security import hash_password


def seed_default_admin(db: Session) -> None:
    if db.scalar(select(User).where(User.username == DEFAULT_ADMIN_USERNAME)) is not None:
        return
    db.add(
        User(
            username=DEFAULT_ADMIN_USERNAME,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            display_name="Platform Admin",
            country="Global",
            is_admin=True,
            chips=10_000_000,
        )
    )
    db.commit()


def seed_tables(db: Session, manager: GameManager) -> None:
    if db.scalar(select(TableConfig)) is None:
        rows: list[TableConfig] = []
        for idx in range(1, 121):
            boot = 50 if idx <= 40 else 200 if idx <= 80 else 500
            min_buyin = 2000 if idx <= 40 else 10000 if idx <= 80 else 30000
            rows.append(
                TableConfig(
                    name=f"Global Table {idx}",
                    max_players=6,
                    boot_amount=boot,
                    min_buyin=min_buyin,
                    max_buyin=min_buyin * 20,
                )
            )
        db.add_all(rows)
        db.commit()

    configs = db.scalars(select(TableConfig)).all()
    manager.seed_tables(
        [
            {
                "id": item.id,
                "name": item.name,
                "max_players": item.max_players,
                "boot_amount": item.boot_amount,
                "min_buyin": item.min_buyin,
                "max_buyin": item.max_buyin,
            }
            for item in configs
        ]
    )
