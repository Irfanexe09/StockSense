"""
StockSense — Batch API endpoints.

CRUD operations and expiry filtering for product batches.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.batch import BatchCreate, BatchResponse, BatchUpdate
from app.services import (
    create_batch,
    delete_batch,
    get_batch,
    get_batches,
    get_product,
    update_batch,
)

router = APIRouter(prefix="/batches", tags=["batches"])


@router.get("/", response_model=list[BatchResponse])
def list_batches(
    product_id: int | None = None,
    expiring_within_days: int | None = Query(None, ge=1, le=365),
    expired_only: bool = False,
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[BatchResponse]:
    """
    List batches with optional filtering by product, expiry timeframe, and active status.
    """
    batches = get_batches(
        db=db,
        product_id=product_id,
        expiring_within_days=expiring_within_days,
        expired_only=expired_only,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )
    # Populate product details for each batch
    results: list[BatchResponse] = []
    for b in batches:
        resp = BatchResponse.model_validate(b)
        if b.product:
            resp.product_name = b.product.name
            resp.product_sku = b.product.sku
        results.append(resp)
    return results


@router.get("/{batch_id}", response_model=BatchResponse)
def read_batch(
    batch_id: int,
    db: Session = Depends(get_db),
) -> BatchResponse:
    """Return a single batch by ID."""
    batch = get_batch(db, batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with id {batch_id} not found.",
        )
    resp = BatchResponse.model_validate(batch)
    if batch.product:
        resp.product_name = batch.product.name
        resp.product_sku = batch.product.sku
    return resp


@router.post("/", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
def create_new_batch(
    data: BatchCreate,
    db: Session = Depends(get_db),
) -> BatchResponse:
    """
    Receive and record a new batch for a product.
    Increases the product's overall stock quantity automatically.
    """
    product = get_product(db, data.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {data.product_id} not found.",
        )

    batch = create_batch(db, data)
    resp = BatchResponse.model_validate(batch)
    resp.product_name = product.name
    resp.product_sku = product.sku
    return resp


@router.patch("/{batch_id}", response_model=BatchResponse)
def update_existing_batch(
    batch_id: int,
    data: BatchUpdate,
    db: Session = Depends(get_db),
) -> BatchResponse:
    """Update a batch (e.g. quantity correction, expiry date update)."""
    batch = get_batch(db, batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with id {batch_id} not found.",
        )
    updated = update_batch(db, batch, data)
    resp = BatchResponse.model_validate(updated)
    if updated.product:
        resp.product_name = updated.product.name
        resp.product_sku = updated.product.sku
    return resp


@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_batch(
    batch_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete a batch and adjust the product's stock_quantity."""
    batch = get_batch(db, batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with id {batch_id} not found.",
        )
    delete_batch(db, batch)
