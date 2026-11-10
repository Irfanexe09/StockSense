"""
StockSense — Supplier API endpoints.

CRUD operations for suppliers and vendor management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate
from app.services import (
    create_supplier,
    delete_supplier,
    get_supplier,
    list_suppliers,
    update_supplier,
)

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("/", response_model=list[SupplierResponse])
def get_all_suppliers(
    active_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[SupplierResponse]:
    """List suppliers with optional active-only filter."""
    suppliers = list_suppliers(db, active_only=active_only, skip=skip, limit=limit)
    return [SupplierResponse.model_validate(s) for s in suppliers]


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_single_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
) -> SupplierResponse:
    """Get a supplier by ID."""
    supplier = get_supplier(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found.",
        )
    return SupplierResponse.model_validate(supplier)


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_new_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
) -> SupplierResponse:
    """Create a new supplier."""
    try:
        supplier = create_supplier(db, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return SupplierResponse.model_validate(supplier)


@router.patch("/{supplier_id}", response_model=SupplierResponse)
def update_existing_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
) -> SupplierResponse:
    """Update supplier fields or active status."""
    supplier = get_supplier(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found.",
        )
    try:
        updated = update_supplier(db, supplier, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return SupplierResponse.model_validate(updated)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete a supplier (only if no purchase orders exist)."""
    supplier = get_supplier(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found.",
        )
    try:
        delete_supplier(db, supplier)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
