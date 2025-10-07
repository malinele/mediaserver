"""FastAPI application factory."""
from __future__ import annotations

from fastapi import FastAPI

from .api.routes import router
from .state import AppState

state = AppState()


def create_app() -> FastAPI:
    app = FastAPI(title="Media Controller", version="0.1.0")
    app.include_router(router)

    @app.get("/")
    async def index() -> dict[str, str]:
        return {"message": "media controller online"}

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await state.shutdown()

    return app


app = create_app()
