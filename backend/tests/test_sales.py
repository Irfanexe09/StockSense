"""
Tests for StockSense Point-of-Sale / Checkout API.

Covers:
  - Successful single-item checkout
  - Successful multi-item checkout
  - FIFO deduction verification during checkout
  - Insufficient stock → full rollback
  - Invalid product ID rejection
  - Invalid quantity (zero / negative) rejection
  - Price mismatch rejection
  - Transaction total calculation accuracy
  - Sale history listing and individual sale retrieval
  - Empty cart rejection
"""

import pytest
from decimal import Decimal


# ── Helper to create a product with batches ──────────────────────────


def _create_product(client, sku="TEST-001", name="Test Product",
                    cost_price=10.0, selling_price=20.0, stock_quantity=0):
    """Create a product via the API and return its JSON."""
    resp = client.post("/api/v1/products/", json={
        "sku": sku,
        "name": name,
        "cost_price": cost_price,
        "selling_price": selling_price,
        "stock_quantity": stock_quantity,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_batch(client, product_id, batch_number, quantity,
                  expiry_date=None, received_date=None):
    """Create a batch via the API and return its JSON."""
    data = {
        "product_id": product_id,
        "batch_number": batch_number,
        "quantity": quantity,
    }
    if expiry_date:
        data["expiry_date"] = expiry_date
    if received_date:
        data["received_date"] = received_date
    resp = client.post("/api/v1/batches/", json=data)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Tests ────────────────────────────────────────────────────────────


class TestCheckoutSuccess:
    """Happy-path checkout tests."""

    def test_single_item_checkout(self, client):
        """Checkout with one item should succeed and return receipt."""
        product = _create_product(client, sku="POS-001", selling_price=25.0)
        _create_batch(client, product["id"], "B-001", 10)

        resp = client.post("/api/v1/sales/checkout", json={
            "items": [
                {"product_id": product["id"], "quantity": 3, "unit_price": 25.0}
            ]
        })
        assert resp.status_code == 201
        sale = resp.json()

        assert sale["receipt_number"].startswith("SS-")
        assert sale["item_count"] == 1
        assert float(sale["total_amount"]) == 75.0  # 3 × 25
        assert len(sale["items"]) == 1
        assert sale["items"][0]["product_sku"] == "POS-001"
        assert sale["items"][0]["quantity"] == 3

        # Verify stock was deducted
        prod_resp = client.get(f"/api/v1/products/{product['id']}")
        assert prod_resp.json()["stock_quantity"] == 7  # 10 - 3

    def test_multi_item_checkout(self, client):
        """Checkout with multiple items should succeed atomically."""
        p1 = _create_product(client, sku="MI-001", name="Apple Juice",
                             selling_price=15.0)
        p2 = _create_product(client, sku="MI-002", name="Orange Juice",
                             selling_price=20.0)
        _create_batch(client, p1["id"], "B-A1", 20)
        _create_batch(client, p2["id"], "B-O1", 15)

        resp = client.post("/api/v1/sales/checkout", json={
            "items": [
                {"product_id": p1["id"], "quantity": 5, "unit_price": 15.0},
                {"product_id": p2["id"], "quantity": 3, "unit_price": 20.0},
            ]
        })
        assert resp.status_code == 201
        sale = resp.json()

        assert sale["item_count"] == 2
        # Total = 5×15 + 3×20 = 75 + 60 = 135
        assert float(sale["total_amount"]) == 135.0

        # Check stock levels
        assert client.get(f"/api/v1/products/{p1['id']}").json()["stock_quantity"] == 15
        assert client.get(f"/api/v1/products/{p2['id']}").json()["stock_quantity"] == 12


class TestFIFODuringCheckout:
    """Verify FIFO batch deduction during checkout."""

    def test_fifo_deducts_earliest_expiry_first(self, client):
        """Batches with the earliest expiry date should be consumed first."""
        product = _create_product(client, sku="FIFO-001", selling_price=10.0)
        # Batch with far expiry (should be consumed second)
        _create_batch(client, product["id"], "B-FAR", 5,
                      expiry_date="2027-12-31", received_date="2026-01-01")
        # Batch with near expiry (should be consumed first)
        _create_batch(client, product["id"], "B-NEAR", 5,
                      expiry_date="2026-12-01", received_date="2026-01-01")

        resp = client.post("/api/v1/sales/checkout", json={
            "items": [
                {"product_id": product["id"], "quantity": 7, "unit_price": 10.0}
            ]
        })
        assert resp.status_code == 201

        # Check batch quantities — NEAR should be fully consumed
        batches_resp = client.get(
            f"/api/v1/batches/?product_id={product['id']}&active_only=false"
        )
        batches = {b["batch_number"]: b["quantity"]
                   for b in batches_resp.json()}
        assert batches["B-NEAR"] == 0   # 5 consumed
        assert batches["B-FAR"] == 3    # 2 consumed from far

    def test_fifo_non_perishable_after_perishable(self, client):
        """Non-perishable batches (no expiry) are used after perishable ones."""
        product = _create_product(client, sku="FIFO-002", selling_price=5.0)
        # Non-perishable batch
        _create_batch(client, product["id"], "B-NP", 10,
                      received_date="2026-01-01")
        # Perishable batch
        _create_batch(client, product["id"], "B-P", 5,
                      expiry_date="2027-06-30", received_date="2026-06-01")

        resp = client.post("/api/v1/sales/checkout", json={
            "items": [
                {"product_id": product["id"], "quantity": 7, "unit_price": 5.0}
            ]
        })
        assert resp.status_code == 201

        batches_resp = client.get(
            f"/api/v1/batches/?product_id={product['id']}&active_only=false"
        )
        batches = {b["batch_number"]: b["quantity"]
                   for b in batches_resp.json()}
        assert batches["B-P"] == 0     # perishable fully consumed first
        assert batches["B-NP"] == 8    # 2 consumed from non-perishable


class TestCheckoutValidation:
    """Validation and error handling tests."""

    def test_insufficient_stock_rollback(self, client):
        """If any item has insufficient stock, the entire checkout rolls back."""
        p1 = _create_product(client, sku="RB-001", selling_price=10.0)
        p2 = _create_product(client, sku="RB-002", selling_price=20.0)
        _create_batch(client, p1["id"], "B-1", 10)
        _create_batch(client, p2["id"], "B-2", 2)  # only 2 in stock

        resp = client.post("/api/v1/sales/checkout", json={
            "items": [
                {"product_id": p1["id"], "quantity": 5, "unit_price": 10.0},
                {"product_id": p2["id"], "quantity": 5, "unit_price": 20.0},  # exceeds stock
            ]
        })
        assert resp.status_code == 400
        assert "Insufficient stock" in resp.json()["detail"]

        # Verify p1 stock was NOT deducted (full rollback)
        assert client.get(f"/api/v1/products/{p1['id']}").json()["stock_quantity"] == 10
        assert client.get(f"/api/v1/products/{p2['id']}").json()["stock_quantity"] == 2

    def test_invalid_product_id_rejected(self, client):
        """Checkout with a nonexistent product ID should fail."""
        resp = client.post("/api/v1/sales/checkout", json={
            "items": [
                {"product_id": 99999, "quantity": 1, "unit_price": 10.0}
            ]
        })
        assert resp.status_code == 400
        assert "not found" in resp.json()["detail"]

    def test_zero_quantity_rejected(self, client):
        """Quantity must be greater than zero."""
        product = _create_product(client, sku="ZQ-001", selling_price=10.0)
        _create_batch(client, product["id"], "B-ZQ", 10)

        resp = client.post("/api/v1/sales/checkout", json={
            "items": [
                {"product_id": product["id"], "quantity": 0, "unit_price": 10.0}
            ]
        })
        # Pydantic validation (gt=0) will catch this as 422
        assert resp.status_code == 422

    def test_negative_quantity_rejected(self, client):
        """Negative quantity should be rejected."""
        product = _create_product(client, sku="NQ-001", selling_price=10.0)
        _create_batch(client, product["id"], "B-NQ", 10)

        resp = client.post("/api/v1/sales/checkout", json={
            "items": [
                {"product_id": product["id"], "quantity": -3, "unit_price": 10.0}
            ]
        })
        assert resp.status_code == 422

    def test_price_mismatch_rejected(self, client):
        """Submitted unit_price must match the product's current selling_price."""
        product = _create_product(client, sku="PM-001", selling_price=25.0)
        _create_batch(client, product["id"], "B-PM", 10)

        resp = client.post("/api/v1/sales/checkout", json={
            "items": [
                {"product_id": product["id"], "quantity": 1, "unit_price": 30.0}
            ]
        })
        assert resp.status_code == 400
        assert "Price mismatch" in resp.json()["detail"]

    def test_empty_cart_rejected(self, client):
        """An empty items list should be rejected."""
        resp = client.post("/api/v1/sales/checkout", json={
            "items": []
        })
        # Pydantic validation (min_length=1) catches this as 422
        assert resp.status_code == 422


class TestTransactionTotals:
    """Verify sale total calculations."""

    def test_total_calculation_accuracy(self, client):
        """Grand total should equal sum of line totals."""
        p1 = _create_product(client, sku="TC-001", selling_price=12.50)
        p2 = _create_product(client, sku="TC-002", selling_price=7.99)
        _create_batch(client, p1["id"], "B-TC1", 100)
        _create_batch(client, p2["id"], "B-TC2", 100)

        resp = client.post("/api/v1/sales/checkout", json={
            "items": [
                {"product_id": p1["id"], "quantity": 4, "unit_price": 12.50},
                {"product_id": p2["id"], "quantity": 6, "unit_price": 7.99},
            ]
        })
        assert resp.status_code == 201
        sale = resp.json()

        expected_total = Decimal("12.50") * 4 + Decimal("7.99") * 6
        assert Decimal(str(sale["total_amount"])) == expected_total

        # Verify each line total
        item_totals = {i["product_sku"]: Decimal(str(i["line_total"]))
                       for i in sale["items"]}
        assert item_totals["TC-001"] == Decimal("50.00")
        assert item_totals["TC-002"] == Decimal("47.94")


class TestSaleHistory:
    """Sale retrieval and listing tests."""

    def test_get_sale_by_id(self, client):
        """A completed sale should be retrievable by ID."""
        product = _create_product(client, sku="SH-001", selling_price=10.0)
        _create_batch(client, product["id"], "B-SH1", 50)

        checkout_resp = client.post("/api/v1/sales/checkout", json={
            "items": [
                {"product_id": product["id"], "quantity": 2, "unit_price": 10.0}
            ]
        })
        sale_id = checkout_resp.json()["id"]

        resp = client.get(f"/api/v1/sales/{sale_id}")
        assert resp.status_code == 200
        sale = resp.json()
        assert sale["id"] == sale_id
        assert len(sale["items"]) == 1

    def test_get_nonexistent_sale(self, client):
        """Requesting a nonexistent sale should return 404."""
        resp = client.get("/api/v1/sales/99999")
        assert resp.status_code == 404

    def test_list_sales(self, client):
        """Sales list should return recent sales in descending order."""
        product = _create_product(client, sku="LS-001", selling_price=5.0)
        _create_batch(client, product["id"], "B-LS", 100)

        # Create multiple sales
        for i in range(3):
            client.post("/api/v1/sales/checkout", json={
                "items": [
                    {"product_id": product["id"], "quantity": 1, "unit_price": 5.0}
                ]
            })

        resp = client.get("/api/v1/sales/")
        assert resp.status_code == 200
        sales = resp.json()
        assert len(sales) == 3

        # Verify receipt numbers are unique
        receipts = [s["receipt_number"] for s in sales]
        assert len(set(receipts)) == 3

    def test_unique_receipt_numbers(self, client):
        """Each checkout should generate a unique receipt number."""
        product = _create_product(client, sku="UR-001", selling_price=10.0)
        _create_batch(client, product["id"], "B-UR", 100)

        receipts = set()
        for _ in range(5):
            resp = client.post("/api/v1/sales/checkout", json={
                "items": [
                    {"product_id": product["id"], "quantity": 1, "unit_price": 10.0}
                ]
            })
            assert resp.status_code == 201
            receipts.add(resp.json()["receipt_number"])

        assert len(receipts) == 5
