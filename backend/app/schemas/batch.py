"""
StockSense — Batch and stock management Pydantic schemas.

Request and response shapes for batches, stock deductions, and alerts.
"""

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductResponse


# --- Batch Schemas ---


class BatchCreate(BaseModel):
    """Fields to create a new product batch."""

    product_id: int = Field(examples=[1])
    batch_number: str = Field(min_length=1, max_length=100, examples=["LOT-2026-A1"])
    quantity: int = Field(gt=0, examples=[50])
    expiry_date: date | None = Field(default=None, examples=["2026-12-31"])
    received_date: date | None = Field(default=None, examples=["2026-11-09"])


class BatchUpdate(BaseModel):
    """Fields to update on an existing batch."""

    batch_number: str | None = Field(default=None, min_length=1, max_length=100)
    quantity: int | None = Field(default=None, ge=0)
    expiry_date: date | None = None
    received_date: date | None = None


class BatchResponse(BaseModel):
    """A batch as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    batch_number: str
    initial_quantity: int
    quantity: int
    expiry_date: date | None
    received_date: date
    created_at: datetime
    is_expired: bool
    days_until_expiry: int | None
    product_name: str | None = None
    product_sku: str | None = None


# --- Stock Deduction & Adjustment Schemas ---


class StockDeductRequest(BaseModel):
    """Request payload to deduct stock using FIFO order."""

    quantity: int = Field(gt=0, examples=[5])
    reason: str | None = Field(default="sale", max_length=200, examples=["sale", "damage", "spoilage"])


class BatchDeductionDetail(BaseModel):
    """Information on how a single batch contributed to a deduction."""

    batch_id: int
    batch_number: str
    deducted_quantity: int
    remaining_in_batch: int
    expiry_date: date | None


class StockDeductResponse(BaseModel):
    """Result of a FIFO stock deduction."""

    product_id: int
    requested_quantity: int
    deducted_quantity: int
    remaining_stock: int
    batches_affected: list[BatchDeductionDetail]


# --- Inventory Alerts Summary Schema ---


class AlertsSummaryCounts(BaseModel):
    """Aggregated alert counters for dashboard badges."""

    low_stock_products_count: int
    expiring_batches_count: int
    expired_batches_count: int


class AlertsSummaryResponse(BaseModel):
    """Comprehensive alert status for the dashboard."""

    counts: AlertsSummaryCounts
    low_stock_products: list[ProductResponse]
    expiring_batches: list[BatchResponse]
    expired_batches: list[BatchResponse]
