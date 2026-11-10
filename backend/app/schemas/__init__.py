"""
Schemas package — Pydantic request/response schemas.
"""

from app.schemas.analytics import (
    CategorySalesShare,
    DailySalesTrend,
    ExpiryRiskExposure,
    InventoryAnalyticsResponse,
    InventoryValuationSummary,
    LowStockExposure,
    SalesAnalyticsResponse,
    SalesSummaryKPIs,
    TopSellingProduct,
)
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
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
    PurchaseOrderItemResponse,
    PurchaseOrderListResponse,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    ReceiptItemResponse,
    ReceiptResponse,
    ReceiveItemInput,
    ReceiveOrderRequest,
)
from app.schemas.sale import (
    CheckoutItem,
    CheckoutRequest,
    SaleItemResponse,
    SaleListResponse,
    SaleResponse,
)
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate

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
    "CategorySalesShare",
    "CheckoutItem",
    "CheckoutRequest",
    "DailySalesTrend",
    "ExpiryRiskExposure",
    "InventoryAnalyticsResponse",
    "InventoryValuationSummary",
    "LowStockExposure",
    "ProductCreate",
    "ProductResponse",
    "ProductUpdate",
    "PurchaseOrderCreate",
    "PurchaseOrderItemCreate",
    "PurchaseOrderItemResponse",
    "PurchaseOrderListResponse",
    "PurchaseOrderResponse",
    "PurchaseOrderUpdate",
    "ReceiptItemResponse",
    "ReceiptResponse",
    "ReceiveItemInput",
    "ReceiveOrderRequest",
    "SaleItemResponse",
    "SaleListResponse",
    "SaleResponse",
    "SalesAnalyticsResponse",
    "SalesSummaryKPIs",
    "StockDeductRequest",
    "StockDeductResponse",
    "SupplierCreate",
    "SupplierResponse",
    "SupplierUpdate",
    "TopSellingProduct",
]
