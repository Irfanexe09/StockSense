"""
StockSense — Batch service.

Implements all inventory lot / batch operations and FIFO stock deductions.

FIFO rules:
  1. Batches with an expiry date are consumed first, ordered by earliest expiry_date.
  2. Batches without an expiry date are consumed after perishable batches,
     ordered by earliest received_date (or id).
  3. If total stock across all active batches is less than the requested deduction,
     the transaction is rejected immediately with an InsufficientStockError.
"""

from datetime import date, datetime, timedelta, timezone
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.product import Product
from app.schemas.batch import (
    BatchCreate,
    BatchDeductionDetail,
    BatchResponse,
    BatchUpdate,
    StockDeductResponse,
)


class InsufficientStockError(ValueError):
    """Raised when attempting to deduct more stock than available."""
    pass


def _enrich_batch_response(batch: Batch) -> BatchResponse:
    """Helper to convert a Batch ORM model to BatchResponse with product details."""
    resp = BatchResponse.model_validate(batch)
    if batch.product:
        resp.product_name = batch.product.name
        resp.product_sku = batch.product.sku
    return resp


def create_batch(db: Session, data: BatchCreate) -> Batch:
    """
    Create a new batch and increment the product's total stock_quantity.
    """
    product = db.get(Product, data.product_id)
    if not product:
        raise ValueError(f"Product with id {data.product_id} not found.")

    received_date = data.received_date or datetime.now(timezone.utc).date()

    batch = Batch(
        product_id=data.product_id,
        batch_number=data.batch_number,
        initial_quantity=data.quantity,
        quantity=data.quantity,
        expiry_date=data.expiry_date,
        received_date=received_date,
    )
    db.add(batch)

    # Maintain consistency: product stock_quantity is the sum of batch quantities
    product.stock_quantity += data.quantity

    db.commit()
    db.refresh(batch)
    db.refresh(product)
    return batch


def get_batches(
    db: Session,
    product_id: int | None = None,
    expiring_within_days: int | None = None,
    expired_only: bool = False,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
) -> list[Batch]:
    """Return filtered batches ordered by expiry date (nulls last) and received date."""
    stmt = select(Batch)

    if product_id is not None:
        stmt = stmt.where(Batch.product_id == product_id)

    if active_only:
        stmt = stmt.where(Batch.quantity > 0)

    today = datetime.now(timezone.utc).date()

    if expired_only:
        stmt = stmt.where(Batch.expiry_date.is_not(None)).where(Batch.expiry_date < today)
    elif expiring_within_days is not None:
        cutoff = today + timedelta(days=expiring_within_days)
        stmt = (
            stmt.where(Batch.expiry_date.is_not(None))
            .where(Batch.expiry_date >= today)
            .where(Batch.expiry_date <= cutoff)
        )

    # Order: earliest expiring first, then non-expiring by received date
    stmt = stmt.order_by(
        case((Batch.expiry_date.is_(None), 1), else_=0),
        Batch.expiry_date.asc(),
        Batch.received_date.asc(),
        Batch.id.asc(),
    ).offset(skip).limit(limit)

    return list(db.scalars(stmt).all())


def get_batch(db: Session, batch_id: int) -> Batch | None:
    """Return a single batch by ID."""
    return db.get(Batch, batch_id)


def update_batch(db: Session, batch: Batch, data: BatchUpdate) -> Batch:
    """
    Update batch fields. If quantity changes, adjust product.stock_quantity accordingly.
    """
    product = db.get(Product, batch.product_id)

    update_fields = data.model_dump(exclude_unset=True)
    if "quantity" in update_fields and update_fields["quantity"] is not None:
        new_qty = update_fields["quantity"]
        diff = new_qty - batch.quantity
        batch.quantity = new_qty
        if product:
            product.stock_quantity += diff

    for field, val in update_fields.items():
        if field != "quantity":
            setattr(batch, field, val)

    db.commit()
    db.refresh(batch)
    if product:
        db.refresh(product)
    return batch


def delete_batch(db: Session, batch: Batch) -> None:
    """
    Delete a batch and decrease the product's stock_quantity.
    """
    product = db.get(Product, batch.product_id)
    if product and batch.quantity > 0:
        product.stock_quantity = max(0, product.stock_quantity - batch.quantity)

    db.delete(batch)
    db.commit()
    if product:
        db.refresh(product)


def deduct_stock_fifo(
    db: Session,
    product_id: int,
    quantity: int,
    reason: str | None = None,
    *,
    commit: bool = True,
) -> StockDeductResponse:
    """
    Deduct stock from a product using FIFO (earliest expiry first, oldest receipt second).
    Atomically updates both batch quantities and product.stock_quantity.
    Raises InsufficientStockError if quantity > available stock.

    When ``commit=False`` the caller is responsible for committing the
    transaction.  This is used by the checkout service to deduct multiple
    products atomically within a single database transaction.
    """
    product = db.get(Product, product_id)
    if not product:
        raise ValueError(f"Product with id {product_id} not found.")

    if quantity <= 0:
        raise ValueError("Deduction quantity must be greater than zero.")

    # Retrieve all active batches ordered by FIFO rules
    stmt = (
        select(Batch)
        .where(Batch.product_id == product_id)
        .where(Batch.quantity > 0)
        .order_by(
            case((Batch.expiry_date.is_(None), 1), else_=0),
            Batch.expiry_date.asc(),
            Batch.received_date.asc(),
            Batch.id.asc(),
        )
    )
    batches = list(db.scalars(stmt).all())

    total_available = sum(b.quantity for b in batches)
    if total_available < quantity:
        raise InsufficientStockError(
            f"Insufficient stock for product '{product.name}' (SKU: {product.sku}). "
            f"Requested {quantity}, but only {total_available} available."
        )

    remaining_to_deduct = quantity
    affected: list[BatchDeductionDetail] = []

    for b in batches:
        if remaining_to_deduct <= 0:
            break

        take = min(b.quantity, remaining_to_deduct)
        b.quantity -= take
        remaining_to_deduct -= take

        affected.append(
            BatchDeductionDetail(
                batch_id=b.id,
                batch_number=b.batch_number,
                deducted_quantity=take,
                remaining_in_batch=b.quantity,
                expiry_date=b.expiry_date,
            )
        )

    product.stock_quantity = max(0, product.stock_quantity - quantity)

    if commit:
        db.commit()
        db.refresh(product)

    return StockDeductResponse(
        product_id=product.id,
        requested_quantity=quantity,
        deducted_quantity=quantity,
        remaining_stock=product.stock_quantity,
        batches_affected=affected,
    )


def get_inventory_alerts(
    db: Session,
    expiring_within_days: int = 30,
) -> dict:
    """
    Returns aggregated low-stock products and expiring/expired batches for the dashboard.
    """
    today = datetime.now(timezone.utc).date()
    cutoff = today + timedelta(days=expiring_within_days)

    # 1. Low stock products (stock_quantity <= reorder_level)
    low_stock_stmt = (
        select(Product)
        .where(Product.stock_quantity <= Product.reorder_level)
        .order_by(Product.stock_quantity.asc())
    )
    low_stock_products = list(db.scalars(low_stock_stmt).all())

    # 2. Expired active batches (expiry_date < today and quantity > 0)
    expired_stmt = (
        select(Batch)
        .where(Batch.quantity > 0)
        .where(Batch.expiry_date.is_not(None))
        .where(Batch.expiry_date < today)
        .order_by(Batch.expiry_date.asc())
    )
    expired_batches = list(db.scalars(expired_stmt).all())

    # 3. Expiring soon active batches (today <= expiry_date <= cutoff and quantity > 0)
    expiring_stmt = (
        select(Batch)
        .where(Batch.quantity > 0)
        .where(Batch.expiry_date.is_not(None))
        .where(Batch.expiry_date >= today)
        .where(Batch.expiry_date <= cutoff)
        .order_by(Batch.expiry_date.asc())
    )
    expiring_batches = list(db.scalars(expiring_stmt).all())

    return {
        "counts": {
            "low_stock_products_count": len(low_stock_products),
            "expiring_batches_count": len(expiring_batches),
            "expired_batches_count": len(expired_batches),
        },
        "low_stock_products": low_stock_products,
        "expiring_batches": [_enrich_batch_response(b) for b in expiring_batches],
        "expired_batches": [_enrich_batch_response(b) for b in expired_batches],
    }
