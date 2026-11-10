"""
StockSense — Purchase Order and Receiving Pydantic schemas.

Request and response shapes for purchasing, line items, and inventory receipts.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ── Purchase Order Items ──


class PurchaseOrderItemCreate(BaseModel):
    product_id: int = Field(..., examples=[1])
    quantity: int = Field(..., gt=0, examples=[50])
    unit_cost: Decimal = Field(..., ge=0, decimal_places=2, examples=[25.00])


class PurchaseOrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_order_id: int
    product_id: int | None
    product_name: str
    product_sku: str
    quantity: int
    received_quantity: int
    remaining_quantity: int
    unit_cost: Decimal
    line_total: Decimal
    is_fully_received: bool


# ── Receiving & Receipts ──


class ReceiveItemInput(BaseModel):
    purchase_order_item_id: int = Field(..., examples=[1])
    quantity_received: int = Field(..., gt=0, examples=[25])
    batch_number: str = Field(..., min_length=1, max_length=100, examples=["BATCH-2026-01"])
    expiry_date: date | None = Field(default=None, examples=["2027-12-31"])


class ReceiveOrderRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=500, examples=["Delivered in good condition"])
    items: list[ReceiveItemInput] = Field(..., min_length=1)


class ReceiptItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_order_item_id: int
    batch_id: int | None
    quantity_received: int
    batch_number: str
    expiry_date: date | None


class ReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_order_id: int
    receipt_number: str
    received_at: datetime
    notes: str | None
    items: list[ReceiptItemResponse]


# ── Purchase Orders ──


class PurchaseOrderCreate(BaseModel):
    supplier_id: int = Field(..., examples=[1])
    order_date: date | None = Field(default=None)
    expected_delivery_date: date | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=1000)
    submit_now: bool = Field(
        default=False,
        description="If True, PO transitions to ORDERED immediately. Otherwise remains in DRAFT.",
    )
    items: list[PurchaseOrderItemCreate] = Field(..., min_length=1)


class PurchaseOrderUpdate(BaseModel):
    supplier_id: int | None = None
    order_date: date | None = None
    expected_delivery_date: date | None = None
    notes: str | None = None
    items: list[PurchaseOrderItemCreate] | None = None


class PurchaseOrderListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    supplier_id: int
    supplier_name: str | None = None
    status: str
    order_date: date
    expected_delivery_date: date | None
    total_amount: Decimal
    item_count: int
    created_at: datetime


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    supplier_id: int
    supplier_name: str | None = None
    status: str
    order_date: date
    expected_delivery_date: date | None
    notes: str | None
    total_amount: Decimal
    item_count: int
    created_at: datetime
    updated_at: datetime
    items: list[PurchaseOrderItemResponse]
    receipts: list[ReceiptResponse]
