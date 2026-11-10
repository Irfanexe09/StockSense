"""
StockSense — v1 API router.

Aggregates all v1 endpoint routers into a single router
that is mounted at /api/v1 in main.py.
"""

from fastapi import APIRouter

from app.api.v1.alerts import router as alerts_router
from app.api.v1.batches import router as batches_router
from app.api.v1.categories import router as categories_router
from app.api.v1.health import router as health_router
from app.api.v1.products import router as products_router
from app.api.v1.purchase_orders import router as purchase_orders_router
from app.api.v1.sales import router as sales_router
from app.api.v1.suppliers import router as suppliers_router

api_router = APIRouter()

# --- Health check ---
api_router.include_router(health_router, tags=["health"])

# --- Categories ---
api_router.include_router(categories_router)

# --- Products ---
api_router.include_router(products_router)

# --- Batches ---
api_router.include_router(batches_router)

# --- Inventory Alerts ---
api_router.include_router(alerts_router)

# --- Sales / Point of Sale ---
api_router.include_router(sales_router)

# --- Suppliers ---
api_router.include_router(suppliers_router)

# --- Purchase Orders & Restocking ---
api_router.include_router(purchase_orders_router)
