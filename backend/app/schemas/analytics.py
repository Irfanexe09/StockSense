"""
StockSense — Analytics Pydantic schemas.

Response shapes for sales summaries, trends, product performance,
category breakdowns, and inventory valuation metrics.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SalesSummaryKPIs(BaseModel):
    """Core sales summary counts and totals over a selected period."""

    total_revenue: Decimal = Field(..., description="Total sales revenue")
    order_count: int = Field(..., description="Total completed orders")
    units_sold: int = Field(..., description="Total quantity of units sold")
    average_order_value: Decimal = Field(..., description="Average revenue per order")


class DailySalesTrend(BaseModel):
    """Daily aggregated sales metric for charting."""

    date: date
    revenue: Decimal
    order_count: int
    units_sold: int


class TopSellingProduct(BaseModel):
    """Performance summary for a product."""

    product_id: int | None
    product_name: str
    product_sku: str
    units_sold: int
    total_revenue: Decimal
    order_count: int


class CategorySalesShare(BaseModel):
    """Category breakdown of sales."""

    category_id: int | None
    category_name: str
    units_sold: int
    total_revenue: Decimal
    revenue_percentage: float = Field(..., description="Percentage of total revenue (0-100)")


class SalesAnalyticsResponse(BaseModel):
    """Complete sales analytics payload for a given date range."""

    start_date: date
    end_date: date
    summary: SalesSummaryKPIs
    daily_trends: list[DailySalesTrend]
    top_products: list[TopSellingProduct]
    category_breakdown: list[CategorySalesShare]


class InventoryValuationSummary(BaseModel):
    """Valuation of current on-hand inventory."""

    total_products_count: int
    total_stock_units: int
    total_cost_value: Decimal = Field(
        ..., description="Current cost value (sum of stock_quantity * cost_price)"
    )
    total_retail_value: Decimal = Field(
        ..., description="Current retail value (sum of stock_quantity * selling_price)"
    )
    potential_margin_value: Decimal = Field(
        ..., description="Potential gross margin value (retail_value - cost_value)"
    )
    potential_margin_percent: float = Field(
        ..., description="Potential gross margin percentage"
    )


class LowStockExposure(BaseModel):
    """Low-stock deficit and restock cost requirements."""

    low_stock_products_count: int
    total_units_deficit: int = Field(
        ..., description="Sum of max(0, reorder_level - stock_quantity)"
    )
    estimated_restock_cost: Decimal = Field(
        ..., description="Estimated cost to bring all items to reorder level"
    )


class ExpiryRiskExposure(BaseModel):
    """Stock exposure from expired or expiring batches."""

    expired_batches_count: int
    expired_units: int
    expired_cost_value: Decimal
    expiring_soon_batches_count: int
    expiring_soon_units: int
    expiring_soon_cost_value: Decimal


class InventoryAnalyticsResponse(BaseModel):
    """Consolidated inventory valuation and exposure metrics."""

    valuation: InventoryValuationSummary
    low_stock_exposure: LowStockExposure
    expiry_risk: ExpiryRiskExposure
