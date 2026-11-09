"""
StockSense — Product database model.

A product is a single item that the shop stocks and sells.
Each product belongs to one category and carries pricing,
stock-level, and reorder information.
"""

from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)

    # SKU = Stock Keeping Unit.  A short code (like a barcode number)
    # that uniquely identifies a product across the shop.
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    description: Mapped[str | None] = mapped_column(String(1000), default=None)

    # What the shop pays to buy this item from a supplier.
    cost_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False
    )

    # What the shop charges the customer.
    selling_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False
    )

    # Current quantity in stock.  Updated when sales or purchases happen.
    stock_quantity: Mapped[int] = mapped_column(default=0)

    # When stock drops to or below this number, the dashboard shows a warning.
    reorder_level: Mapped[int] = mapped_column(default=10)

    # Foreign key linking this product to a category.
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), default=None
    )

    # Relationship: each product belongs to one category.
    category: Mapped["Category | None"] = relationship(
        "Category", back_populates="products"
    )

    @property
    def is_low_stock(self) -> bool:
        """True when stock is at or below the reorder threshold."""
        return self.stock_quantity <= self.reorder_level

    def __repr__(self) -> str:
        return f"<Product id={self.id} sku={self.sku!r} name={self.name!r}>"


from app.models.category import Category  # noqa: E402, F401
