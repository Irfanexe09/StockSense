"""Services package — business logic."""

from app.services.batch_service import (
    InsufficientStockError,
    create_batch,
    deduct_stock_fifo,
    delete_batch,
    get_batch,
    get_batches,
    get_inventory_alerts,
    update_batch,
)
from app.services.category_service import (
    create_category,
    delete_category,
    get_categories,
    get_category,
    get_category_by_name,
    update_category,
)
from app.services.product_service import (
    count_products,
    create_product,
    delete_product,
    get_product,
    get_product_by_sku,
    get_products,
    update_product,
)

__all__ = [
    "InsufficientStockError",
    "count_products",
    "create_batch",
    "create_category",
    "create_product",
    "deduct_stock_fifo",
    "delete_batch",
    "delete_category",
    "delete_product",
    "get_batch",
    "get_batches",
    "get_categories",
    "get_category",
    "get_category_by_name",
    "get_inventory_alerts",
    "get_product",
    "get_product_by_sku",
    "get_products",
    "update_batch",
    "update_category",
    "update_product",
]
