"""
Schemas package — Pydantic request/response schemas.
"""

from app.schemas.batch import (
    AlertsSummaryCounts,
    AlertsSummaryResponse,
    BatchCreate,
    BatchDeductionDetail,
    BatchResponse,
    BatchUpdate,
    StockDeductRequest,
    StockDeductResponse,
)
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.schemas.sale import (
    CheckoutItem,
    CheckoutRequest,
    SaleItemResponse,
    SaleListResponse,
    SaleResponse,
)

__all__ = [
    "AlertsSummaryCounts",
    "AlertsSummaryResponse",
    "BatchCreate",
    "BatchDeductionDetail",
    "BatchResponse",
    "BatchUpdate",
    "CategoryCreate",
    "CategoryResponse",
    "CategoryUpdate",
    "CheckoutItem",
    "CheckoutRequest",
    "ProductCreate",
    "ProductResponse",
    "ProductUpdate",
    "SaleItemResponse",
    "SaleListResponse",
    "SaleResponse",
    "StockDeductRequest",
    "StockDeductResponse",
]
