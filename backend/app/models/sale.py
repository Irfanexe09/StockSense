"""
StockSense — Sale and SaleItem database models.

A Sale represents a single point-of-sale checkout transaction.
Each sale contains one or more SaleItems, where each item records
a snapshot of the product at the time of purchase (name, SKU,
unit price) along with the quantity sold.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Human-readable receipt number, e.g. "SS-20261110-0001"
    receipt_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    # When the sale was recorded
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Grand total for the entire sale (sum of all line totals)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2), nullable=False
    )

    # Number of distinct line items in this sale
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationship to line items
    items: Mapped[list["SaleItem"]] = relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan",
        order_by="SaleItem.id",
    )

    def __repr__(self) -> str:
        return f"<Sale id={self.id} receipt={self.receipt_number!r} total={self.total_amount}>"


class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    sale_id: Mapped[int] = mapped_column(
        ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Snapshot fields — preserved even if the product is later edited or deleted
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    product_sku: Mapped[str] = mapped_column(String(50), nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Price per unit at the time of sale
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False
    )

    # quantity × unit_price
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2), nullable=False
    )

    # Relationships
    sale: Mapped["Sale"] = relationship("Sale", back_populates="items")
    product: Mapped["Product | None"] = relationship("Product")

    def __repr__(self) -> str:
        return (
            f"<SaleItem id={self.id} sale_id={self.sale_id} "
            f"sku={self.product_sku!r} qty={self.quantity}>"
        )


from app.models.product import Product  # noqa: E402, F401
