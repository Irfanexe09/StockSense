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


class TestSalesAnalyticsDeletedProduct:
    """Sales analytics must handle products deleted after a sale was recorded."""

    def test_deleted_product_appears_in_top_products_via_snapshot(self, client):
        """A deleted product's sale items use snapshot fields, so analytics
        should still include them in top products and category breakdown."""
        cat = _create_category(client, name="Temp")
        p = _create_product(client, sku="DEL-01", name="Doomed Widget",
                            cost_price=5.0, selling_price=10.0, category_id=cat["id"])
        _create_batch(client, p["id"], "B-D1", 20)
        _checkout(client, [{"product_id": p["id"], "quantity": 3, "unit_price": 10.0}])

        # Delete the product
        del_resp = client.delete(f"/api/v1/products/{p['id']}")
        assert del_resp.status_code == 204

        resp = client.get("/api/v1/analytics/sales?preset=today")
        assert resp.status_code == 200
        data = resp.json()

        assert Decimal(data["summary"]["total_revenue"]) == Decimal("30.00")
        assert data["summary"]["units_sold"] == 3

        # Top products should still contain the snapshot
        assert len(data["top_products"]) == 1
        assert data["top_products"][0]["product_name"] == "Doomed Widget"
        # NOTE: In PostgreSQL, product_id would be NULL (SET NULL on delete).
        # SQLite test DB doesn't enforce FKs by default, so product_id retains
        # the old value.  The important check is that snapshot fields survive.
        assert data["top_products"][0]["product_sku"] == "DEL-01"

        # Category breakdown: with SQLite (no FK enforcement), the product_id
        # still references the old row which is deleted, so prod lookup returns
        # nothing — item falls back to "Uncategorized".  In PostgreSQL the
        # product_id would be NULL, achieving the same result.
        assert len(data["category_breakdown"]) == 1
        assert data["category_breakdown"][0]["category_name"] == "Uncategorized"


class TestSalesAnalyticsMultipleCategories:
    """Verify category breakdown with multiple categories and percentage math."""

    def test_two_category_breakdown_percentages(self, client):
        c1 = _create_category(client, name="Drinks")
        c2 = _create_category(client, name="Food")

        p1 = _create_product(client, sku="MC-01", name="Juice", cost_price=2.0,
                             selling_price=5.0, category_id=c1["id"])
        p2 = _create_product(client, sku="MC-02", name="Sandwich", cost_price=3.0,
                             selling_price=15.0, category_id=c2["id"])

        _create_batch(client, p1["id"], "B-MC1", 50)
        _create_batch(client, p2["id"], "B-MC2", 50)

        # 4 Juices ($20) + 2 Sandwiches ($30) = $50 total
        _checkout(client, [
            {"product_id": p1["id"], "quantity": 4, "unit_price": 5.0},
            {"product_id": p2["id"], "quantity": 2, "unit_price": 15.0},
        ])

        resp = client.get("/api/v1/analytics/sales?preset=today")
        assert resp.status_code == 200
        data = resp.json()

        cats = {c["category_name"]: c for c in data["category_breakdown"]}
        assert len(cats) == 2
        assert Decimal(cats["Drinks"]["total_revenue"]) == Decimal("20.00")
        assert Decimal(cats["Food"]["total_revenue"]) == Decimal("30.00")
        assert cats["Drinks"]["revenue_percentage"] == 40.0
        assert cats["Food"]["revenue_percentage"] == 60.0

        # Percentages must sum to 100
        total_pct = sum(c["revenue_percentage"] for c in data["category_breakdown"])
        assert total_pct == 100.0


class TestSalesAnalyticsAllPreset:
    """Verify the 'all' preset spans from the earliest sale to today."""

    def test_all_preset_returns_from_earliest_sale(self, client):
        cat = _create_category(client, name="Misc")
        p = _create_product(client, sku="ALL-01", name="Widget",
                            cost_price=1.0, selling_price=5.0, category_id=cat["id"])
        _create_batch(client, p["id"], "B-ALL", 100)

        _checkout(client, [{"product_id": p["id"], "quantity": 1, "unit_price": 5.0}])

        resp = client.get("/api/v1/analytics/sales?preset=all")
        assert resp.status_code == 200
        data = resp.json()

        today = str(date.today())
        assert data["start_date"] == today  # only sale is today
        assert data["end_date"] == today
        assert data["summary"]["order_count"] == 1

    def test_all_preset_with_no_sales_falls_back_to_30d(self, client):
        resp = client.get("/api/v1/analytics/sales?preset=all")
        assert resp.status_code == 200
        data = resp.json()

        today = date.today()
        expected_start = str(today - timedelta(days=29))
        assert data["start_date"] == expected_start
        assert data["end_date"] == str(today)


class TestInventoryAnalyticsEdgeCases:
    """Edge cases in inventory analytics: depleted batches, products without batches."""

    def test_depleted_batches_excluded_from_expiry_risk(self, client):
        """Batches with quantity=0 should not count as expired or expiring."""
        today = date.today()
        expired_date = today - timedelta(days=5)

        p = _create_product(client, sku="DEPL-01", cost_price=10.0,
                            selling_price=20.0, stock_quantity=0, reorder_level=0)
        _create_batch(client, p["id"], "B-DEPL", 5, expiry_date=str(expired_date))

        # Sell all 5 units to deplete the batch
        _checkout(client, [{"product_id": p["id"], "quantity": 5, "unit_price": 20.0}])

        resp = client.get("/api/v1/analytics/inventory")
        assert resp.status_code == 200
        data = resp.json()

        assert data["expiry_risk"]["expired_batches_count"] == 0
        assert data["expiry_risk"]["expired_units"] == 0

    def test_product_without_batches_included_in_valuation(self, client):
        """Products created with initial stock_quantity=0 and no batches
        should still be counted in total_products_count but contribute
        zero to stock units and valuation."""
        _create_product(client, sku="NOBATCH-01", cost_price=100.0,
                        selling_price=200.0, stock_quantity=0, reorder_level=0)

        resp = client.get("/api/v1/analytics/inventory")
        assert resp.status_code == 200
        data = resp.json()

        val = data["valuation"]
        assert val["total_products_count"] == 1
        assert val["total_stock_units"] == 0
        assert Decimal(val["total_cost_value"]) == Decimal("0.00")
        assert Decimal(val["total_retail_value"]) == Decimal("0.00")

    def test_multiple_batches_same_product_valuation(self, client):
        """Inventory valuation uses product.stock_quantity × catalog price,
        not individual batch sums.  Verify they stay consistent."""
        p = _create_product(client, sku="MULTI-B01", cost_price=10.0,
                            selling_price=25.0, stock_quantity=0, reorder_level=0)
        _create_batch(client, p["id"], "B-M1", 10)
        _create_batch(client, p["id"], "B-M2", 15)

        resp = client.get("/api/v1/analytics/inventory")
        assert resp.status_code == 200
        data = resp.json()

        val = data["valuation"]
        # stock = 10 + 15 = 25
        assert val["total_stock_units"] == 25
        # cost = 25 * 10 = 250, retail = 25 * 25 = 625
        assert Decimal(val["total_cost_value"]) == Decimal("250.00")
        assert Decimal(val["total_retail_value"]) == Decimal("625.00")
        assert Decimal(val["potential_margin_value"]) == Decimal("375.00")


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
