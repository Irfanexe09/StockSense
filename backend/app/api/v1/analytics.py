"""
StockSense — Analytics API endpoints.

Aggregated metrics for sales revenue, order volumes, trends,
top product performance, category share, and inventory valuation.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analytics import InventoryAnalyticsResponse, SalesAnalyticsResponse
from app.services import get_inventory_analytics, get_sales_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/sales", response_model=SalesAnalyticsResponse)
def get_sales_metrics(
    preset: str = Query("30d", description="Date preset: today, 7d, 30d, 90d, all, custom"),
    start_date: date | None = Query(None, description="Start date (required for custom preset)"),
    end_date: date | None = Query(None, description="End date (required for custom preset)"),
    db: Session = Depends(get_db),
) -> SalesAnalyticsResponse:
    """
    Returns aggregated sales performance KPIs, daily trends, top-selling items,
    and category breakdowns for the specified date range.
    """
    try:
        return get_sales_analytics(
            db, preset=preset, start_date=start_date, end_date=end_date
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get("/inventory", response_model=InventoryAnalyticsResponse)
def get_inventory_metrics(
    db: Session = Depends(get_db),
) -> InventoryAnalyticsResponse:
    """
    Returns current inventory valuation, gross margin spread,
    low-stock deficit requirements, and expiry risk exposure.
    """
    return get_inventory_analytics(db)
