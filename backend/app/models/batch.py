"""
StockSense — Batch database model.

A Batch (or Lot) represents a specific incoming consignment of a product.
Tracking batches allows:
  1. Expiry tracking: different batches of the same product can expire on different dates.
  2. FIFO stock deduction: older or earlier-expiring stock is sold/used first.
  3. Batch traceability: knowing exactly which batch was received and when.
"""

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Unique or supplier batch identifier (e.g. "LOT-2026-04", "B-9872")
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Quantity originally received in this batch
    initial_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Quantity currently remaining in this batch
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Optional expiry date (null for non-perishable goods)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    # Date this batch was received into inventory
    received_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).date(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship back to parent product
    product: Mapped["Product"] = relationship("Product", back_populates="batches")

    @property
    def is_expired(self) -> bool:
        """True if batch has an expiry date that is before today."""
        if self.expiry_date is None:
            return False
        return self.expiry_date < datetime.now(timezone.utc).date()

    @property
    def days_until_expiry(self) -> int | None:
        """Number of days until expiry (negative if already expired)."""
        if self.expiry_date is None:
            return None
        today = datetime.now(timezone.utc).date()
        return (self.expiry_date - today).days

    def __repr__(self) -> str:
        return (
            f"<Batch id={self.id} product_id={self.product_id} "
            f"batch_number={self.batch_number!r} qty={self.quantity} "
            f"expiry={self.expiry_date}>"
        )


from app.models.product import Product  # noqa: E402, F401
