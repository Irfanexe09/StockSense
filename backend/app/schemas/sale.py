"""
StockSense — Sale Pydantic schemas.

Request and response shapes for the point-of-sale and sales-history APIs.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# --- Request schemas ---


class CheckoutItem(BaseModel):
    """A single line item in a checkout request."""

    product_id: int = Field(..., examples=[1])
    quantity: int = Field(..., gt=0, examples=[3])
    unit_price: Decimal = Field(..., ge=0, decimal_places=2, examples=[65.00])


class CheckoutRequest(BaseModel):
    """Payload for POST /api/v1/sales/checkout."""

    items: list[CheckoutItem] = Field(
        ..., min_length=1, description="Cart items to purchase"
    )


# --- Response schemas ---


class SaleItemResponse(BaseModel):
    """A single line item as returned in a sale response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int | None
    product_name: str
    product_sku: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class SaleResponse(BaseModel):
    """A completed sale as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    receipt_number: str
    created_at: datetime
    total_amount: Decimal
    item_count: int
    items: list[SaleItemResponse]


class SaleListResponse(BaseModel):
    """Paginated list of sales (without line-item detail)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    receipt_number: str
    created_at: datetime
    total_amount: Decimal
    item_count: int
