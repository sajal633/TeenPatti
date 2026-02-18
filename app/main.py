from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import APP_NAME, APP_VERSION, STATIC_DIR, TEMPLATE_FILE
from app.database import Base, SessionLocal, engine
from app.routers import admin, auth, game, lobby, ludo, profile, twentynine
from app.services.bootstrap import seed_default_admin, seed_tables
from app.services.runtime import manager


def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME, version=APP_VERSION)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.include_router(auth.router)
    app.include_router(profile.router)
    app.include_router(lobby.router)
    app.include_router(game.router)
    app.include_router(game.ws_router)
    app.include_router(admin.router)
    app.include_router(twentynine.router)
    app.include_router(ludo.router)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(TEMPLATE_FILE)

    @app.on_event("startup")
    def startup() -> None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_default_admin(db)
            seed_tables(db, manager)
        finally:
            db.close()

    return app


app = create_app()
