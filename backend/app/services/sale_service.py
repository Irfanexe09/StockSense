"""
StockSense — Sale service.

Implements the point-of-sale checkout flow and sale history queries.

Checkout guarantees:
  1. All cart items are validated (product exists, price matches, quantity > 0).
  2. Stock is deducted using FIFO batch logic for every item.
  3. The sale and its line items are recorded atomically.
  4. If ANY item fails validation or has insufficient stock, the ENTIRE
     transaction is rolled back — no partial sales.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.schemas.sale import CheckoutItem, CheckoutRequest
from app.services.batch_service import InsufficientStockError, deduct_stock_fifo


class CheckoutError(ValueError):
    """Raised when checkout validation fails."""
    pass


def _generate_receipt_number(db: Session) -> str:
    """
    Generate a unique, human-readable receipt number.

    Format: SS-YYYYMMDD-NNNN
    Example: SS-20261110-0001

    The sequence resets daily — the counter is derived from the number
    of sales already recorded on the current date.
    """
    today = datetime.now(timezone.utc).date()
    date_str = today.strftime("%Y%m%d")

    # Count existing sales whose receipt starts with today's prefix
    prefix = f"SS-{date_str}-"
    count = db.scalar(
        select(func.count(Sale.id)).where(
            Sale.receipt_number.like(f"{prefix}%")
        )
    ) or 0

    sequence = count + 1
    return f"{prefix}{sequence:04d}"


def checkout(db: Session, request: CheckoutRequest) -> Sale:
    """
    Process a point-of-sale checkout.

    Validates every item, deducts stock via FIFO, records the sale,
    and commits atomically.  Rolls back on any failure.
    """
    if not request.items:
        raise CheckoutError("Cart is empty.")

    # --- Step 1: Validate all items upfront ---
    validated_items: list[tuple[Product, CheckoutItem]] = []

    for item in request.items:
        if item.quantity <= 0:
            raise CheckoutError(
                f"Quantity must be positive (product_id={item.product_id})."
            )

        product = db.get(Product, item.product_id)
        if not product:
            raise CheckoutError(
                f"Product with id {item.product_id} not found."
            )

        # Verify the submitted price matches the current selling price
        if Decimal(str(item.unit_price)) != product.selling_price:
            raise CheckoutError(
                f"Price mismatch for product '{product.name}' "
                f"(SKU: {product.sku}). "
                f"Expected {product.selling_price}, got {item.unit_price}."
            )

        validated_items.append((product, item))

    # --- Step 2: Deduct stock for every item (no commit yet) ---
    try:
        for product, item in validated_items:
            deduct_stock_fifo(
                db,
                product_id=product.id,
                quantity=item.quantity,
                reason=f"POS checkout",
                commit=False,
            )
    except InsufficientStockError:
        db.rollback()
        raise

    # --- Step 3: Build sale record ---
    receipt_number = _generate_receipt_number(db)

    sale_items: list[SaleItem] = []
    grand_total = Decimal("0.00")

    for product, item in validated_items:
        line_total = Decimal(str(item.unit_price)) * item.quantity
        grand_total += line_total

        sale_items.append(
            SaleItem(
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=line_total,
            )
        )

    sale = Sale(
        receipt_number=receipt_number,
        total_amount=grand_total,
        item_count=len(sale_items),
        items=sale_items,
    )
    db.add(sale)

    # --- Step 4: Commit everything atomically ---
    try:
        db.commit()
        db.refresh(sale)
    except Exception:
        db.rollback()
        raise

    return sale


def get_sale(db: Session, sale_id: int) -> Sale | None:
    """Return a single sale with its line items."""
    return db.get(Sale, sale_id)


def get_sale_by_receipt(db: Session, receipt_number: str) -> Sale | None:
    """Return a sale by its receipt number."""
    stmt = select(Sale).where(Sale.receipt_number == receipt_number)
    return db.scalar(stmt)


def list_sales(
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> list[Sale]:
    """Return recent sales ordered by newest first."""
    stmt = (
        select(Sale)
        .order_by(Sale.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def count_sales(db: Session) -> int:
    """Return the total number of sales."""
    return db.scalar(select(func.count(Sale.id))) or 0
