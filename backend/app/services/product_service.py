"""
StockSense — Product service.

All database operations for products live here.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    category_id: int | None = None,
    search: str | None = None,
    low_stock_only: bool = False,
) -> list[Product]:
    """Return a filtered, paginated list of products."""
    stmt = select(Product)

    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)

    if search:
        # Case-insensitive partial match on name or SKU.
        pattern = f"%{search}%"
        stmt = stmt.where(
            Product.name.ilike(pattern) | Product.sku.ilike(pattern)
        )

    if low_stock_only:
        stmt = stmt.where(Product.stock_quantity <= Product.reorder_level)

    stmt = stmt.order_by(Product.name).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def count_products(
    db: Session,
    category_id: int | None = None,
    search: str | None = None,
    low_stock_only: bool = False,
) -> int:
    """Count products matching the given filters (for pagination info)."""
    from sqlalchemy import func

    stmt = select(func.count(Product.id))

    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            Product.name.ilike(pattern) | Product.sku.ilike(pattern)
        )

    if low_stock_only:
        stmt = stmt.where(Product.stock_quantity <= Product.reorder_level)

    result = db.execute(stmt).scalar()
    return result or 0


def get_product(db: Session, product_id: int) -> Product | None:
    """Return a single product by ID, or None if not found."""
    return db.get(Product, product_id)


def get_product_by_sku(db: Session, sku: str) -> Product | None:
    """Return a product by its SKU, or None."""
    stmt = select(Product).where(Product.sku == sku)
    return db.scalars(stmt).first()


def create_product(db: Session, data: ProductCreate) -> Product:
    """Insert a new product and return it."""
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product: Product, data: ProductUpdate) -> Product:
    """Apply partial updates to an existing product."""
    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    """Delete a product from the database."""
    db.delete(product)
    db.commit()
