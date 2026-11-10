"""
StockSense — Supplier database model.

A supplier is an external vendor from whom the retail shop purchases stock.
Suppliers carry contact details and an active/inactive status.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Name of the supplier / company (e.g. "Acme Food Distributors")
    name: Mapped[str] = mapped_column(
        String(150), unique=True, nullable=False, index=True
    )

    # Primary contact person
    contact_name: Mapped[str | None] = mapped_column(String(100), default=None)

    # Contact details
    email: Mapped[str | None] = mapped_column(String(100), default=None)
    phone: Mapped[str | None] = mapped_column(String(50), default=None)
    address: Mapped[str | None] = mapped_column(String(255), default=None)

    # Inactive suppliers cannot be chosen for new purchase orders
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship to purchase orders
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="supplier",
        order_by="PurchaseOrder.id.desc()",
    )

    def __repr__(self) -> str:
        return f"<Supplier id={self.id} name={self.name!r} active={self.is_active}>"


from app.models.purchase_order import PurchaseOrder  # noqa: E402, F401
