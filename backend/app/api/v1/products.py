"""
StockSense — Product API endpoints.

CRUD operations for products, with search and filtering support.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services import (
    count_products,
    create_product,
    delete_product,
    get_product,
    get_product_by_sku,
    get_products,
    update_product,
)
from app.services.category_service import get_category

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/")
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category_id: int | None = None,
    search: str | None = None,
    low_stock_only: bool = False,
    db: Session = Depends(get_db),
) -> dict:
    """Return a filtered, paginated list of products.

    Response includes `items` (the products) and `total` (how many
    match the filters overall) so the frontend can build pagination.
    """
    items = get_products(
        db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        search=search,
        low_stock_only=low_stock_only,
    )
    total = count_products(
        db,
        category_id=category_id,
        search=search,
        low_stock_only=low_stock_only,
    )
    return {
        "items": [ProductResponse.model_validate(p) for p in items],
        "total": total,
    }


@router.get("/{product_id}", response_model=ProductResponse)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
) -> ProductResponse:
    """Return a single product by ID."""
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found.",
        )
    return product


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
) -> ProductResponse:
    """Create a new product. SKU must be unique."""
    # Validate SKU uniqueness.
    if get_product_by_sku(db, data.sku):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A product with SKU '{data.sku}' already exists.",
        )
    # Validate category exists if provided.
    if data.category_id is not None:
        if get_category(db, data.category_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {data.category_id} not found.",
            )
    return create_product(db, data)


@router.patch("/{product_id}", response_model=ProductResponse)
def update_existing_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
) -> ProductResponse:
    """Update an existing product. Only send the fields to change."""
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found.",
        )
    # If changing SKU, check uniqueness.
    if data.sku is not None and data.sku != product.sku:
        conflict = get_product_by_sku(db, data.sku)
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A product with SKU '{data.sku}' already exists.",
            )
    # If changing category, verify it exists.
    if data.category_id is not None:
        if get_category(db, data.category_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {data.category_id} not found.",
            )
    return update_product(db, product, data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_product(
    product_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete a product."""
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found.",
        )
    delete_product(db, product)
