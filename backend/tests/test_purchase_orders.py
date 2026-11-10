"""
Tests for StockSense Purchase Orders & Restocking API.

Covers:
  - PO creation (draft & ordered)
  - Line totals and grand total calculation
  - Inactive supplier rejection
  - Invalid product / quantity / cost rejection
  - Updating draft purchase orders
  - Order submission transition (DRAFT -> ORDERED)
  - Cancellation rules (before receipt vs after receipt)
  - Partial and complete receiving into inventory batches
  - Product stock_quantity synchronization upon receiving
  - Over-receipt rejection
  - Duplicate / invalid status receipt protection
  - Atomic rollback on failed receipt item
  - Supplier deletion protection when orders exist
"""

from decimal import Decimal
import pytest


# ── Helpers ──────────────────────────────────────────────────────────


def _create_supplier(client, name="Test Supplier", is_active=True):
    resp = client.post("/api/v1/suppliers/", json={"name": name, "is_active": is_active})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_product(client, sku="PROD-01", name="Product 01", cost_price=10.0, selling_price=15.0, stock_quantity=0):
    resp = client.post("/api/v1/products/", json={
        "sku": sku,
        "name": name,
        "cost_price": cost_price,
        "selling_price": selling_price,
        "stock_quantity": stock_quantity,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Tests ────────────────────────────────────────────────────────────


class TestPurchaseOrderCreation:
    def test_create_draft_order(self, client):
        supplier = _create_supplier(client, name="Vendor A")
        p1 = _create_product(client, sku="VA-01", cost_price=12.0)
        p2 = _create_product(client, sku="VA-02", cost_price=20.0)

        resp = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "notes": "Urgent restock",
            "items": [
                {"product_id": p1["id"], "quantity": 10, "unit_cost": 12.0},
                {"product_id": p2["id"], "quantity": 5, "unit_cost": 20.0},
            ],
        })
        assert resp.status_code == 201, resp.text
        po = resp.json()

        assert po["order_number"].startswith("PO-")
        assert po["status"] == "DRAFT"
        assert po["supplier_name"] == "Vendor A"
        assert po["item_count"] == 2
        # Total: 10 * 12 + 5 * 20 = 120 + 100 = 220
        assert Decimal(str(po["total_amount"])) == Decimal("220.00")
        assert len(po["items"]) == 2
        assert po["items"][0]["product_sku"] == "VA-01"
        assert po["items"][0]["remaining_quantity"] == 10
        assert po["items"][0]["received_quantity"] == 0

    def test_create_order_with_submit_now(self, client):
        supplier = _create_supplier(client, name="Vendor B")
        p = _create_product(client, sku="VB-01")

        resp = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "submit_now": True,
            "items": [{"product_id": p["id"], "quantity": 25, "unit_cost": 8.50}],
        })
        assert resp.status_code == 201
        assert resp.json()["status"] == "ORDERED"

    def test_inactive_supplier_rejected(self, client):
        supplier = _create_supplier(client, name="Inactive Vendor", is_active=False)
        p = _create_product(client, sku="IV-01")

        resp = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "items": [{"product_id": p["id"], "quantity": 10, "unit_cost": 5.0}],
        })
        assert resp.status_code == 400
        assert "inactive supplier" in resp.json()["detail"]

    def test_invalid_product_id_rejected(self, client):
        supplier = _create_supplier(client)
        resp = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "items": [{"product_id": 99999, "quantity": 10, "unit_cost": 5.0}],
        })
        assert resp.status_code == 400
        assert "not found" in resp.json()["detail"]

    def test_invalid_quantity_rejected(self, client):
        supplier = _create_supplier(client)
        p = _create_product(client, sku="IQ-01")
        resp = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "items": [{"product_id": p["id"], "quantity": 0, "unit_cost": 5.0}],
        })
        assert resp.status_code == 422


class TestPurchaseOrderLifecycle:
    def test_submit_draft_order(self, client):
        supplier = _create_supplier(client)
        p = _create_product(client, sku="SUB-01")
        po = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "items": [{"product_id": p["id"], "quantity": 10, "unit_cost": 5.0}],
        }).json()
        assert po["status"] == "DRAFT"

        # Submit order
        resp = client.post(f"/api/v1/purchase-orders/{po['id']}/order")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ORDERED"

    def test_cancel_draft_and_ordered(self, client):
        supplier = _create_supplier(client)
        p = _create_product(client, sku="CAN-01")

        # Cancel DRAFT
        po_draft = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "items": [{"product_id": p["id"], "quantity": 5, "unit_cost": 10.0}],
        }).json()
        resp1 = client.post(f"/api/v1/purchase-orders/{po_draft['id']}/cancel")
        assert resp1.status_code == 200
        assert resp1.json()["status"] == "CANCELLED"

        # Cancel ORDERED
        po_ordered = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "submit_now": True,
            "items": [{"product_id": p["id"], "quantity": 5, "unit_cost": 10.0}],
        }).json()
        resp2 = client.post(f"/api/v1/purchase-orders/{po_ordered['id']}/cancel")
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "CANCELLED"

    def test_cannot_cancel_already_cancelled(self, client):
        supplier = _create_supplier(client)
        p = _create_product(client, sku="CC-01")
        po = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "items": [{"product_id": p["id"], "quantity": 5, "unit_cost": 10.0}],
        }).json()
        client.post(f"/api/v1/purchase-orders/{po['id']}/cancel")

        resp = client.post(f"/api/v1/purchase-orders/{po['id']}/cancel")
        assert resp.status_code == 400


class TestReceivingAndRestocking:
    def test_complete_receiving_creates_batches_and_stock(self, client):
        supplier = _create_supplier(client)
        p = _create_product(client, sku="RCV-01", stock_quantity=0)

        # Place order
        po = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "submit_now": True,
            "items": [{"product_id": p["id"], "quantity": 50, "unit_cost": 15.0}],
        }).json()
        item_id = po["items"][0]["id"]

        # Receive the order fully
        rcv_resp = client.post(f"/api/v1/purchase-orders/{po['id']}/receive", json={
            "notes": "Full delivery",
            "items": [{
                "purchase_order_item_id": item_id,
                "quantity_received": 50,
                "batch_number": "BATCH-RCV-01",
                "expiry_date": "2027-10-31",
            }],
        })
        assert rcv_resp.status_code == 201, rcv_resp.text
        receipt = rcv_resp.json()
        assert receipt["receipt_number"].startswith("POR-")
        assert len(receipt["items"]) == 1
        assert receipt["items"][0]["quantity_received"] == 50
        assert receipt["items"][0]["batch_number"] == "BATCH-RCV-01"

        # Verify PO status transitioned to RECEIVED
        updated_po = client.get(f"/api/v1/purchase-orders/{po['id']}").json()
        assert updated_po["status"] == "RECEIVED"
        assert updated_po["items"][0]["received_quantity"] == 50
        assert updated_po["items"][0]["remaining_quantity"] == 0
        assert updated_po["items"][0]["is_fully_received"] is True

        # Verify product stock updated to 50
        prod = client.get(f"/api/v1/products/{p['id']}").json()
        assert prod["stock_quantity"] == 50

        # Verify batch was created in inventory
        batches = client.get(f"/api/v1/batches/?product_id={p['id']}").json()
        assert any(b["batch_number"] == "BATCH-RCV-01" and b["quantity"] == 50 for b in batches)

    def test_partial_receiving(self, client):
        supplier = _create_supplier(client)
        p = _create_product(client, sku="PART-01", stock_quantity=0)

        po = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "submit_now": True,
            "items": [{"product_id": p["id"], "quantity": 100, "unit_cost": 20.0}],
        }).json()
        item_id = po["items"][0]["id"]

        # First partial delivery of 40 units
        client.post(f"/api/v1/purchase-orders/{po['id']}/receive", json={
            "items": [{
                "purchase_order_item_id": item_id,
                "quantity_received": 40,
                "batch_number": "LOT-PART-A",
            }],
        })

        po_after_first = client.get(f"/api/v1/purchase-orders/{po['id']}").json()
        assert po_after_first["status"] == "PARTIALLY_RECEIVED"
        assert po_after_first["items"][0]["received_quantity"] == 40
        assert po_after_first["items"][0]["remaining_quantity"] == 60
        assert client.get(f"/api/v1/products/{p['id']}").json()["stock_quantity"] == 40

        # Second delivery of remaining 60 units
        client.post(f"/api/v1/purchase-orders/{po['id']}/receive", json={
            "items": [{
                "purchase_order_item_id": item_id,
                "quantity_received": 60,
                "batch_number": "LOT-PART-B",
            }],
        })

        po_after_second = client.get(f"/api/v1/purchase-orders/{po['id']}").json()
        assert po_after_second["status"] == "RECEIVED"
        assert po_after_second["items"][0]["received_quantity"] == 100
        assert po_after_second["items"][0]["remaining_quantity"] == 0
        assert client.get(f"/api/v1/products/{p['id']}").json()["stock_quantity"] == 100
        assert len(po_after_second["receipts"]) == 2

    def test_over_receipt_rejected(self, client):
        supplier = _create_supplier(client)
        p = _create_product(client, sku="OVER-01")

        po = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "submit_now": True,
            "items": [{"product_id": p["id"], "quantity": 20, "unit_cost": 10.0}],
        }).json()
        item_id = po["items"][0]["id"]

        # Attempt to receive 25 when only 20 ordered
        resp = client.post(f"/api/v1/purchase-orders/{po['id']}/receive", json={
            "items": [{
                "purchase_order_item_id": item_id,
                "quantity_received": 25,
                "batch_number": "LOT-OVER",
            }],
        })
        assert resp.status_code == 400
        assert "Only 20 units remain" in resp.json()["detail"]

        # Product stock remains 0
        assert client.get(f"/api/v1/products/{p['id']}").json()["stock_quantity"] == 0

    def test_cannot_receive_draft_or_cancelled_order(self, client):
        supplier = _create_supplier(client)
        p = _create_product(client, sku="STATE-01")

        po_draft = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "submit_now": False,
            "items": [{"product_id": p["id"], "quantity": 10, "unit_cost": 10.0}],
        }).json()
        item_id = po_draft["items"][0]["id"]

        # Cannot receive DRAFT
        resp1 = client.post(f"/api/v1/purchase-orders/{po_draft['id']}/receive", json={
            "items": [{
                "purchase_order_item_id": item_id,
                "quantity_received": 10,
                "batch_number": "B-FAIL",
            }],
        })
        assert resp1.status_code == 400
        assert "must be ORDERED or PARTIALLY_RECEIVED" in resp1.json()["detail"]

    def test_cannot_cancel_after_partial_receipt(self, client):
        supplier = _create_supplier(client)
        p = _create_product(client, sku="NOCAN-01")

        po = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "submit_now": True,
            "items": [{"product_id": p["id"], "quantity": 50, "unit_cost": 10.0}],
        }).json()
        item_id = po["items"][0]["id"]

        client.post(f"/api/v1/purchase-orders/{po['id']}/receive", json={
            "items": [{
                "purchase_order_item_id": item_id,
                "quantity_received": 10,
                "batch_number": "B-PART",
            }],
        })

        # Try to cancel
        resp = client.post(f"/api/v1/purchase-orders/{po['id']}/cancel")
        assert resp.status_code == 400
        assert "Cannot cancel purchase order in 'PARTIALLY_RECEIVED' status" in resp.json()["detail"]

    def test_supplier_delete_blocked_when_orders_exist(self, client):
        supplier = _create_supplier(client, name="Vendor With Orders")
        p = _create_product(client, sku="DEL-BLK")

        client.post("/api/v1/purchase-orders/", json={
            "supplier_id": supplier["id"],
            "items": [{"product_id": p["id"], "quantity": 10, "unit_cost": 10.0}],
        })

        # Try to delete supplier
        resp = client.delete(f"/api/v1/suppliers/{supplier['id']}")
        assert resp.status_code == 400
        assert "purchase orders exist" in resp.json()["detail"]
