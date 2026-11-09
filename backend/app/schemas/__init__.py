"""
Schemas package — Pydantic request/response schemas.
"""

from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

__all__ = [
    "CategoryCreate",
    "CategoryResponse",
    "CategoryUpdate",
    "ProductCreate",
    "ProductResponse",
    "ProductUpdate",
]
