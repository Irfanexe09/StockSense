"""
StockSense — Health check endpoint.

Provides a simple way to verify the API server is running.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Return the current health status of the API."""
    return {
        "status": "healthy",
        "service": "StockSense API",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
