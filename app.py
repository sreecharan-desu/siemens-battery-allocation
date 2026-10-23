"""ASGI entry for Vercel FastAPI runtime."""

from battery_allocation.api.app import create_app

app = create_app()
