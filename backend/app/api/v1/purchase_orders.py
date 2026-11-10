"""
StockSense — Purchase Order API endpoints.

Endpoints for managing purchase orders, status transitions, and inventory receiving.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderListResponse,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    ReceiptResponse,
    ReceiveOrderRequest,
)
from app.services import (
    PurchaseOrderError,
    cancel_purchase_order,
    create_purchase_order,
    get_purchase_order,
    list_purchase_orders,
    receive_purchase_order_items,
    submit_purchase_order,
    update_purchase_order,
)

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


def _enrich_po_response(po) -> PurchaseOrderResponse:
    return PurchaseOrderResponse.model_validate(po)


@router.get("/", response_model=list[PurchaseOrderListResponse])
def get_all_purchase_orders(
    supplier_id: int | None = None,
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[PurchaseOrderListResponse]:
    """List purchase orders with optional filtering by supplier or status."""
    pos = list_purchase_orders(
        db,
        supplier_id=supplier_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    return [PurchaseOrderListResponse.model_validate(po) for po in pos]


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
def get_single_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
) -> PurchaseOrderResponse:
    """Get a purchase order by ID including line items and receipts."""
    po = get_purchase_order(db, po_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with id {po_id} not found.",
        )
    return _enrich_po_response(po)


@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def create_new_purchase_order(
    data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
) -> PurchaseOrderResponse:
    """Create a new purchase order in DRAFT or ORDERED status."""
    try:
        po = create_purchase_order(db, data)
    except PurchaseOrderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return _enrich_po_response(po)


@router.patch("/{po_id}", response_model=PurchaseOrderResponse)
def update_existing_purchase_order(
    po_id: int,
    data: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
) -> PurchaseOrderResponse:
    """Update a purchase order (allowed only in DRAFT status)."""
    po = get_purchase_order(db, po_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with id {po_id} not found.",
        )
    try:
        updated = update_purchase_order(db, po, data)
    except PurchaseOrderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return _enrich_po_response(updated)


@router.post("/{po_id}/order", response_model=PurchaseOrderResponse)
def place_order(
    po_id: int,
    db: Session = Depends(get_db),
) -> PurchaseOrderResponse:
    """Submit a DRAFT purchase order, changing status to ORDERED."""
    po = get_purchase_order(db, po_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with id {po_id} not found.",
        )
    try:
        ordered = submit_purchase_order(db, po)
    except PurchaseOrderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return _enrich_po_response(ordered)


@router.post("/{po_id}/cancel", response_model=PurchaseOrderResponse)
def cancel_order(
    po_id: int,
    db: Session = Depends(get_db),
) -> PurchaseOrderResponse:
    """Cancel a purchase order (allowed only if no items have been received)."""
    po = get_purchase_order(db, po_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with id {po_id} not found.",
        )
    try:
        cancelled = cancel_purchase_order(db, po)
    except PurchaseOrderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return _enrich_po_response(cancelled)


@router.post("/{po_id}/receive", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
def receive_items(
    po_id: int,
    request: ReceiveOrderRequest,
    db: Session = Depends(get_db),
) -> ReceiptResponse:
    """
    Receive items against an ORDERED or PARTIALLY_RECEIVED purchase order.
    Creates new inventory batches and updates product stock quantities atomically.
    """
    po = get_purchase_order(db, po_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with id {po_id} not found.",
        )
    try:
        receipt = receive_purchase_order_items(db, po, request)
    except PurchaseOrderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return ReceiptResponse.model_validate(receipt)
