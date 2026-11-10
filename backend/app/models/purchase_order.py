"""
StockSense — Purchase Order and Receiving models.

Tracks supplier orders, line items, and inventory receipts.
Receiving an order (partially or completely) generates Batches
in the inventory system and updates product stock levels.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PurchaseOrderStatus(str, Enum):
    DRAFT = "DRAFT"
    ORDERED = "ORDERED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Human-readable order number, e.g. "PO-20261110-0001"
    order_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Order lifecycle status
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT.value,
        index=True,
    )

    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).date(),
    )

    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    notes: Mapped[str | None] = mapped_column(String(1000), default=None)

    # Total cost of the order (sum of line_totals)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2), nullable=False, default=Decimal("0.00")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="purchase_orders")

    items: Mapped[list["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderItem.id",
    )

    receipts: Mapped[list["PurchaseOrderReceipt"]] = relationship(
        "PurchaseOrderReceipt",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderReceipt.id.desc()",
    )

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def supplier_name(self) -> str | None:
        return self.supplier.name if self.supplier else None

    def __repr__(self) -> str:
        return f"<PurchaseOrder id={self.id} number={self.order_number!r} status={self.status!r}>"


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Snapshot of product info at time of order
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    product_sku: Mapped[str] = mapped_column(String(50), nullable=False)

    # Quantities
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Cost per unit at time of purchase order
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False
    )

    # quantity * unit_cost
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2), nullable=False
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="items"
    )
    product: Mapped["Product | None"] = relationship("Product")

    @property
    def remaining_quantity(self) -> int:
        return max(0, self.quantity - self.received_quantity)

    @property
    def is_fully_received(self) -> bool:
        return self.received_quantity >= self.quantity

    def __repr__(self) -> str:
        return (
            f"<PurchaseOrderItem id={self.id} po={self.purchase_order_id} "
            f"sku={self.product_sku!r} qty={self.quantity} rcv={self.received_quantity}>"
        )


class PurchaseOrderReceipt(Base):
    __tablename__ = "purchase_order_receipts"

    id: Mapped[int] = mapped_column(primary_key=True)

    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Human-readable receipt number, e.g. "POR-20261110-0001"
    receipt_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    notes: Mapped[str | None] = mapped_column(String(500), default=None)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="receipts"
    )

    items: Mapped[list["PurchaseOrderReceiptItem"]] = relationship(
        "PurchaseOrderReceiptItem",
        back_populates="receipt",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderReceiptItem.id",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderReceipt id={self.id} number={self.receipt_number!r}>"


class PurchaseOrderReceiptItem(Base):
    __tablename__ = "purchase_order_receipt_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    receipt_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_order_receipts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    purchase_order_item_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_order_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Links directly to the Batch created in inventory
    batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    quantity_received: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    receipt: Mapped["PurchaseOrderReceipt"] = relationship(
        "PurchaseOrderReceipt", back_populates="items"
    )
    purchase_order_item: Mapped["PurchaseOrderItem"] = relationship("PurchaseOrderItem")
    batch: Mapped["Batch | None"] = relationship("Batch")

    def __repr__(self) -> str:
        return (
            f"<PurchaseOrderReceiptItem id={self.id} item={self.purchase_order_item_id} "
            f"batch={self.batch_number!r} qty={self.quantity_received}>"
        )


from app.models.supplier import Supplier  # noqa: E402, F401
from app.models.product import Product  # noqa: E402, F401
from app.models.batch import Batch  # noqa: E402, F401
