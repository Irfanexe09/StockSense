"""
Models package — SQLAlchemy ORM models.

Import every model here so that:
  1. `from app.models import Category, Product, Batch, Sale, SaleItem, Supplier, PurchaseOrder, ...` works everywhere.
  2. Base.metadata is fully populated when Alembic inspects it.
"""

from app.models.batch import Batch
from app.models.category import Category
from app.models.product import Product
from app.models.purchase_order import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderReceipt,
    PurchaseOrderReceiptItem,
    PurchaseOrderStatus,
)
from app.models.sale import Sale, SaleItem
from app.models.supplier import Supplier

__all__ = [
    "Batch",
    "Category",
    "Product",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "PurchaseOrderReceipt",
    "PurchaseOrderReceiptItem",
    "PurchaseOrderStatus",
    "Sale",
    "SaleItem",
    "Supplier",
]
