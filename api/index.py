"""Vercel Python entrypoint for the Battery Allocation FastAPI app."""

from battery_allocation.api.app import create_app

app = create_app()

__all__ = ["app"]
