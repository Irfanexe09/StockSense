"""
StockSense — Sales API endpoints.

Point-of-sale checkout and sales history.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.sale import (
    CheckoutRequest,
    SaleListResponse,
    SaleResponse,
)
from app.services import (
    CheckoutError,
    InsufficientStockError,
    checkout,
    count_sales,
    get_sale,
    list_sales,
)

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("/checkout", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def process_checkout(
    request: CheckoutRequest,
    db: Session = Depends(get_db),
) -> SaleResponse:
    """
    Process a point-of-sale checkout.

    Validates the cart, deducts stock via FIFO, and records the sale atomically.
    Returns the complete sale with receipt number and line items.
    """
    try:
        sale = checkout(db, request)
    except CheckoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return SaleResponse.model_validate(sale)


@router.get("/", response_model=list[SaleListResponse])
def list_recent_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[SaleListResponse]:
    """List recent sales ordered by newest first."""
    sales = list_sales(db, skip=skip, limit=limit)
    return [SaleListResponse.model_validate(s) for s in sales]


@router.get("/{sale_id}", response_model=SaleResponse)
def read_sale(
    sale_id: int,
    db: Session = Depends(get_db),
) -> SaleResponse:
    """Return a single sale with its line items."""
    sale = get_sale(db, sale_id)
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sale with id {sale_id} not found.",
        )
    return SaleResponse.model_validate(sale)
