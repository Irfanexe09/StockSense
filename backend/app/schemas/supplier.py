"""
StockSense — Supplier Pydantic schemas.

Request and response schemas for supplier management.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150, examples=["Fresh Foods Wholesaler"])
    contact_name: str | None = Field(default=None, max_length=100, examples=["John Doe"])
    email: str | None = Field(default=None, max_length=100, examples=["john@freshfoods.com"])
    phone: str | None = Field(default=None, max_length=50, examples=["+1 555-0192"])
    address: str | None = Field(default=None, max_length=255, examples=["123 Market St, City"])
    is_active: bool = Field(default=True)


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    contact_name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=255)
    is_active: bool | None = Field(default=None)


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    contact_name: str | None
    email: str | None
    phone: str | None
    address: str | None
    is_active: bool
    created_at: datetime
