"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from battery_allocation.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Battery Allocation API",
        description="Battery health assessment and dynamic allocation for light EV stations",
        version="1.0.0",
    )
    app.include_router(router)
    return app
