"""
StockSense — v1 API router.

Aggregates all v1 endpoint routers into a single router
that is mounted at /api/v1 in main.py.
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router

api_router = APIRouter()

# --- Health check ---
api_router.include_router(health_router, tags=["health"])
