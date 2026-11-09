"""
StockSense — FastAPI application entry point.

Creates the FastAPI app instance, registers middleware,
and mounts API routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""

    application = FastAPI(
        title=settings.app_name,
        description="Inventory management platform for small retail shops.",
        version="0.1.0",
    )

    # --- CORS middleware ---
    # Allows the Next.js frontend (port 3000) to call this API (port 8000).
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- API routers ---
    application.include_router(api_router, prefix="/api/v1")

    return application


app = create_app()
