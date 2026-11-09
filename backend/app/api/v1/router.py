"""
StockSense — v1 API router.

Aggregates all v1 endpoint routers into a single router
that is mounted at /api/v1 in main.py.
"""

from fastapi import APIRouter

from app.api.v1.categories import router as categories_router
from app.api.v1.health import router as health_router
from app.api.v1.products import router as products_router

api_router = APIRouter()

# --- Health check ---
api_router.include_router(health_router, tags=["health"])

# --- Categories ---
api_router.include_router(categories_router)

# --- Products ---
api_router.include_router(products_router)
