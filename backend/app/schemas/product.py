"""
StockSense — Product Pydantic schemas.

Request and response shapes for the products API.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# --- Request schemas ---


class ProductCreate(BaseModel):
    """Fields required to create a new product."""

    sku: str = Field(min_length=1, max_length=50, examples=["BEV-001"])
    name: str = Field(min_length=1, max_length=200, examples=["Orange Juice 1L"])
    description: str | None = Field(default=None, max_length=1000)
    cost_price: Decimal = Field(ge=0, decimal_places=2, examples=[45.00])
    selling_price: Decimal = Field(ge=0, decimal_places=2, examples=[65.00])
    stock_quantity: int = Field(default=0, ge=0, examples=[100])
    reorder_level: int = Field(default=10, ge=0, examples=[10])
    category_id: int | None = Field(default=None, examples=[1])


class ProductUpdate(BaseModel):
    """Fields that can be updated on an existing product.

    All fields are optional — the client sends only what changed.
    """

    sku: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    cost_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    selling_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    stock_quantity: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    category_id: int | None = Field(default=None)


# --- Response schemas ---


class ProductResponse(BaseModel):
    """A product as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    description: str | None
    cost_price: Decimal
    selling_price: Decimal
    stock_quantity: int
    reorder_level: int
    is_low_stock: bool
    category_id: int | None
