"""
StockSense — Inventory alerts API endpoints.

Aggregates low-stock products and expiring/expired batches for the dashboard.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.batch import AlertsSummaryResponse
from app.services import get_inventory_alerts

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=AlertsSummaryResponse)
def get_alerts_summary(
    expiring_within_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> AlertsSummaryResponse:
    """
    Get all active inventory warnings:
      1. Low-stock products (stock_quantity <= reorder_level)
      2. Expiring soon batches (within specified days, default 30)
      3. Expired batches
    """
    data = get_inventory_alerts(db, expiring_within_days=expiring_within_days)
    return AlertsSummaryResponse.model_validate(data)
