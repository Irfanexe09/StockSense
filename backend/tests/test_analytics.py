"""
Tests for StockSense Sales & Inventory Analytics API.

Covers:
  - Empty sales scenario (zero counts, filled daily trends)
  - Sales summary KPI calculations (revenue, orders, units, AOV)
  - Date boundary filtering (today, 7d, 30d, custom)
  - Date validation (invalid preset, start_date > end_date)
  - Top selling products ranking
  - Category sales breakdown and percentage share
  - Inventory valuation (cost, retail, potential margin)
  - Low-stock deficit and estimated restock cost
  - Expiry risk exposure calculation
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest


# ── Helpers ──────────────────────────────────────────────────────────


def _create_category(client, name="Beverages"):
    resp = client.post("/api/v1/categories/", json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_product(client, sku="SKU-01", name="Product 01", cost_price=10.0, selling_price=15.0,
                    stock_quantity=0, category_id=None, reorder_level=10):
    resp = client.post("/api/v1/products/", json={
        "sku": sku,
        "name": name,
        "cost_price": cost_price,
        "selling_price": selling_price,
        "stock_quantity": stock_quantity,
        "category_id": category_id,
        "reorder_level": reorder_level,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_batch(client, product_id, batch_number, quantity, expiry_date=None):
    resp = client.post("/api/v1/batches/", json={
        "product_id": product_id,
        "batch_number": batch_number,
        "quantity": quantity,
        "expiry_date": expiry_date,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def _checkout(client, items):
    resp = client.post("/api/v1/sales/checkout", json={"items": items})
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Tests ────────────────────────────────────────────────────────────


class TestSalesAnalyticsEmpty:
    def test_empty_sales_returns_zeroes_and_filled_trend(self, client):
        resp = client.get("/api/v1/analytics/sales?preset=7d")
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["summary"]["total_revenue"] == "0.00"
        assert data["summary"]["order_count"] == 0
        assert data["summary"]["units_sold"] == 0
        assert data["summary"]["average_order_value"] == "0.00"
        assert len(data["daily_trends"]) == 7
        assert all(t["revenue"] == "0.00" and t["order_count"] == 0 for t in data["daily_trends"])
        assert data["top_products"] == []
        assert data["category_breakdown"] == []


class TestSalesAnalyticsKPIs:
    def test_sales_kpi_calculations_and_daily_trends(self, client):
        cat = _create_category(client, name="Snacks")
        p1 = _create_product(client, sku="SNK-01", name="Chips", cost_price=5.0, selling_price=10.0, category_id=cat["id"])
        p2 = _create_product(client, sku="SNK-02", name="Pretzels", cost_price=8.0, selling_price=12.0, category_id=cat["id"])

        _create_batch(client, p1["id"], "B-1", 50)
        _create_batch(client, p2["id"], "B-2", 50)

        # Checkout 1: 3 Chips ($30) + 2 Pretzels ($24) = $54
        _checkout(client, [
            {"product_id": p1["id"], "quantity": 3, "unit_price": 10.0},
            {"product_id": p2["id"], "quantity": 2, "unit_price": 12.0},
        ])

        # Checkout 2: 1 Chips ($10)
        _checkout(client, [
            {"product_id": p1["id"], "quantity": 1, "unit_price": 10.0},
        ])

        resp = client.get("/api/v1/analytics/sales?preset=today")
        assert resp.status_code == 200
        data = resp.json()

        summary = data["summary"]
        assert Decimal(summary["total_revenue"]) == Decimal("64.00")
        assert summary["order_count"] == 2
        assert summary["units_sold"] == 6  # (3 + 2) + 1
        assert Decimal(summary["average_order_value"]) == Decimal("32.00")  # 64 / 2

        # Daily trend has today's metric
        assert len(data["daily_trends"]) == 1
        assert Decimal(data["daily_trends"][0]["revenue"]) == Decimal("64.00")
        assert data["daily_trends"][0]["units_sold"] == 6

        # Top products
        top_prods = {p["product_sku"]: p for p in data["top_products"]}
        assert "SNK-01" in top_prods
        assert top_prods["SNK-01"]["units_sold"] == 4  # 3 + 1
        assert Decimal(top_prods["SNK-01"]["total_revenue"]) == Decimal("40.00")
        assert top_prods["SNK-02"]["units_sold"] == 2
        assert Decimal(top_prods["SNK-02"]["total_revenue"]) == Decimal("24.00")

        # Category breakdown
        assert len(data["category_breakdown"]) == 1
        cat_share = data["category_breakdown"][0]
        assert cat_share["category_name"] == "Snacks"
        assert Decimal(cat_share["total_revenue"]) == Decimal("64.00")
        assert cat_share["revenue_percentage"] == 100.0


class TestSalesDateBoundariesAndValidation:
    def test_custom_date_range_valid(self, client):
        today = date.today()
        yesterday = today - timedelta(days=1)
        resp = client.get(
            f"/api/v1/analytics/sales?preset=custom&start_date={yesterday}&end_date={today}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["daily_trends"]) == 2

    def test_custom_date_range_inverted_rejected(self, client):
        today = date.today()
        yesterday = today - timedelta(days=1)
        resp = client.get(
            f"/api/v1/analytics/sales?preset=custom&start_date={today}&end_date={yesterday}"
        )
        assert resp.status_code == 400
        assert "cannot be after end_date" in resp.json()["detail"]

    def test_custom_date_missing_params_rejected(self, client):
        resp = client.get("/api/v1/analytics/sales?preset=custom")
        assert resp.status_code == 400
        assert "Both start_date and end_date are required" in resp.json()["detail"]

    def test_invalid_preset_rejected(self, client):
        resp = client.get("/api/v1/analytics/sales?preset=invalid_choice")
        assert resp.status_code == 400
        assert "Invalid preset" in resp.json()["detail"]


class TestInventoryAnalytics:
    def test_inventory_valuation_and_exposure(self, client):
        today = date.today()
        expired_date = today - timedelta(days=10)
        expiring_date = today + timedelta(days=15)

        # Product 1: well stocked
        p1 = _create_product(client, sku="INV-01", cost_price=10.0, selling_price=20.0, stock_quantity=0, reorder_level=5)
        # 10 units active
        _create_batch(client, p1["id"], "B-W1", 10)

        # Product 2: low stock (deficit: reorder_level 10 - stock 2 = 8 units)
        p2 = _create_product(client, sku="INV-02", cost_price=5.0, selling_price=8.0, stock_quantity=0, reorder_level=10)
        # 2 units expiring soon
        _create_batch(client, p2["id"], "B-EXP-SOON", 2, expiry_date=str(expiring_date))

        # Product 3: expired batch
        p3 = _create_product(client, sku="INV-03", cost_price=4.0, selling_price=7.0, stock_quantity=0, reorder_level=2)
        _create_batch(client, p3["id"], "B-EXPIRED", 3, expiry_date=str(expired_date))

        resp = client.get("/api/v1/analytics/inventory")
        assert resp.status_code == 200
        data = resp.json()

        # Valuation
        val = data["valuation"]
        assert val["total_products_count"] == 3
        # Total units: 10 + 2 + 3 = 15
        assert val["total_stock_units"] == 15
        # Total cost: 10*10 + 2*5 + 3*4 = 100 + 10 + 12 = 122
        assert Decimal(val["total_cost_value"]) == Decimal("122.00")
        # Total retail: 10*20 + 2*8 + 3*7 = 200 + 16 + 21 = 237
        assert Decimal(val["total_retail_value"]) == Decimal("237.00")
        # Potential margin: 237 - 122 = 115
        assert Decimal(val["potential_margin_value"]) == Decimal("115.00")

        # Low-stock exposure:
        # p2 has stock=2 <= reorder=10 (deficit=8)
        # p3 has stock=3, reorder=2 (not low stock)
        # p1 has stock=10, reorder=5 (not low stock)
        ls = data["low_stock_exposure"]
        assert ls["low_stock_products_count"] == 1
        assert ls["total_units_deficit"] == 8
        # Restock cost: 8 units * $5 cost_price = $40.00
        assert Decimal(ls["estimated_restock_cost"]) == Decimal("40.00")

        # Expiry risk
        exp = data["expiry_risk"]
        assert exp["expired_batches_count"] == 1
        assert exp["expired_units"] == 3
        assert Decimal(exp["expired_cost_value"]) == Decimal("12.00")  # 3 * 4.0

        assert exp["expiring_soon_batches_count"] == 1
        assert exp["expiring_soon_units"] == 2
        assert Decimal(exp["expiring_soon_cost_value"]) == Decimal("10.00")  # 2 * 5.0
