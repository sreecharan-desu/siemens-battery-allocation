"""Catch-all so rewritten /api/<path> keeps routing into FastAPI."""

from battery_allocation.api.app import create_app

app = create_app()

__all__ = ["app"]
