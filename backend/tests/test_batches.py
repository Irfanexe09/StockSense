"""
StockSense — Batch and FIFO deduction backend tests.

Verifies:
  1. Batch creation and stock totals synchronization.
  2. FIFO stock deduction order (earliest expiry first, oldest non-expiring second).
  3. Insufficient stock rejection without partial state corruption.
  4. Expiry filtering and alert counters (expired, expiring soon, healthy).
  5. Low-stock alert detection.
  6. Batch updates and deletion adjusting product stock totals accurately.
"""

from datetime import date, timedelta


def _create_product(client, sku="TEST-001", name="Test Product", stock=0, reorder=10):
    resp = client.post(
        "/api/v1/products/",
        json={
            "sku": sku,
            "name": name,
            "cost_price": 10.0,
            "selling_price": 20.0,
            "stock_quantity": stock,
            "reorder_level": reorder,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# -------------------------------------------------------------------------
# 1. Batch Creation & Stock Consistency
# -------------------------------------------------------------------------


def test_create_batch_increases_product_stock(client):
    """Creating a batch for a product should increase its stock_quantity."""
    product = _create_product(client, sku="LOT-01", stock=0)
    pid = product["id"]

    # Add a batch with 30 units
    resp = client.post(
        "/api/v1/batches/",
        json={
            "product_id": pid,
            "batch_number": "B-001",
            "quantity": 30,
            "expiry_date": "2027-01-01",
        },
    )
    assert resp.status_code == 201
    batch_data = resp.json()
    assert batch_data["quantity"] == 30
    assert batch_data["initial_quantity"] == 30
    assert batch_data["batch_number"] == "B-001"
    assert batch_data["product_sku"] == "LOT-01"

    # Verify product stock increased to 30
    p_resp = client.get(f"/api/v1/products/{pid}")
    assert p_resp.json()["stock_quantity"] == 30


def test_initial_stock_creates_initial_batch(client):
    """Creating a product with initial stock should automatically create an INIT batch."""
    product = _create_product(client, sku="INIT-01", stock=50)
    pid = product["id"]

    # Product should have stock 50
    assert product["stock_quantity"] == 50

    # Batches for product should contain the INIT batch
    b_resp = client.get(f"/api/v1/products/{pid}/batches")
    assert b_resp.status_code == 200
    batches = b_resp.json()
    assert len(batches) == 1
    assert batches[0]["batch_number"] == "INIT-INIT-01"
    assert batches[0]["quantity"] == 50


# -------------------------------------------------------------------------
# 2. FIFO Stock Deduction Behavior
# -------------------------------------------------------------------------


def test_fifo_deduction_earliest_expiry_first(client):
    """
    Batches with earlier expiry dates must be consumed first.
    Batch A expires in 10 days (qty: 20)
    Batch B expires in 30 days (qty: 20)
    Deducting 25 should take all 20 from Batch A, and 5 from Batch B.
    """
    product = _create_product(client, sku="FIFO-01", stock=0)
    pid = product["id"]

    today = date.today()
    exp_a = (today + timedelta(days=10)).isoformat()
    exp_b = (today + timedelta(days=30)).isoformat()

    b_a = client.post(
        "/api/v1/batches/",
        json={"product_id": pid, "batch_number": "BATCH-A", "quantity": 20, "expiry_date": exp_a},
    ).json()

    b_b = client.post(
        "/api/v1/batches/",
        json={"product_id": pid, "batch_number": "BATCH-B", "quantity": 20, "expiry_date": exp_b},
    ).json()

    # Total product stock is 40
    assert client.get(f"/api/v1/products/{pid}").json()["stock_quantity"] == 40

    # Deduct 25
    deduct_resp = client.post(
        f"/api/v1/products/{pid}/deduct",
        json={"quantity": 25, "reason": "sale"},
    )
    assert deduct_resp.status_code == 200
    deduct_data = deduct_resp.json()
    assert deduct_data["deducted_quantity"] == 25
    assert deduct_data["remaining_stock"] == 15

    affected = deduct_data["batches_affected"]
    assert len(affected) == 2

    # First affected batch is A (all 20 taken)
    assert affected[0]["batch_id"] == b_a["id"]
    assert affected[0]["deducted_quantity"] == 20
    assert affected[0]["remaining_in_batch"] == 0

    # Second affected batch is B (5 taken)
    assert affected[1]["batch_id"] == b_b["id"]
    assert affected[1]["deducted_quantity"] == 5
    assert affected[1]["remaining_in_batch"] == 15


def test_fifo_deduction_expiring_before_non_expiring(client):
    """
    Batches with an expiry date should be consumed BEFORE batches without an expiry date.
    """
    product = _create_product(client, sku="FIFO-02", stock=0)
    pid = product["id"]

    today = date.today()
    future_exp = (today + timedelta(days=60)).isoformat()

    # Batch No Expiry (received first)
    b_no_exp = client.post(
        "/api/v1/batches/",
        json={"product_id": pid, "batch_number": "NO-EXP", "quantity": 10, "expiry_date": None},
    ).json()

    # Batch With Expiry (received second)
    b_exp = client.post(
        "/api/v1/batches/",
        json={"product_id": pid, "batch_number": "WITH-EXP", "quantity": 10, "expiry_date": future_exp},
    ).json()

    # Deduct 8 — should be taken from WITH-EXP first
    deduct_resp = client.post(
        f"/api/v1/products/{pid}/deduct",
        json={"quantity": 8},
    )
    assert deduct_resp.status_code == 200
    affected = deduct_resp.json()["batches_affected"]
    assert len(affected) == 1
    assert affected[0]["batch_id"] == b_exp["id"]
    assert affected[0]["deducted_quantity"] == 8

    # Batch WITH-EXP should have 2 left, NO-EXP still has 10
    batches = client.get(f"/api/v1/products/{pid}/batches").json()
    batch_map = {b["batch_number"]: b["quantity"] for b in batches}
    assert batch_map["WITH-EXP"] == 2
    assert batch_map["NO-EXP"] == 10


# -------------------------------------------------------------------------
# 3. Insufficient Stock Handling
# -------------------------------------------------------------------------


def test_insufficient_stock_raises_400_and_does_not_mutate(client):
    """
    Requesting more stock than available should return HTTP 400
    and leave all batch quantities completely untouched.
    """
    product = _create_product(client, sku="UNDER-01", stock=0)
    pid = product["id"]

    client.post(
        "/api/v1/batches/",
        json={"product_id": pid, "batch_number": "B-5", "quantity": 5},
    )

    # Attempt to deduct 10
    resp = client.post(
        f"/api/v1/products/{pid}/deduct",
        json={"quantity": 10},
    )
    assert resp.status_code == 400
    assert "Insufficient stock" in resp.json()["detail"]

    # Verify stock is still 5
    p_check = client.get(f"/api/v1/products/{pid}").json()
    assert p_check["stock_quantity"] == 5

    b_check = client.get(f"/api/v1/products/{pid}/batches").json()
    assert b_check[0]["quantity"] == 5


# -------------------------------------------------------------------------
# 4. Expiry Tracking & Alerts
# -------------------------------------------------------------------------


def test_expiry_alerts_and_filtering(client):
    """
    Tests identification of expired batches and batches expiring within 30 days.
    """
    today = date.today()
    past_date = (today - timedelta(days=5)).isoformat()
    soon_date = (today + timedelta(days=15)).isoformat()
    far_date = (today + timedelta(days=90)).isoformat()

    product = _create_product(client, sku="EXP-ALERT", stock=0, reorder=2)
    pid = product["id"]

    # 1 expired batch
    client.post(
        "/api/v1/batches/",
        json={"product_id": pid, "batch_number": "EXPIRED", "quantity": 4, "expiry_date": past_date},
    )
    # 1 expiring soon batch (15 days)
    client.post(
        "/api/v1/batches/",
        json={"product_id": pid, "batch_number": "SOON", "quantity": 6, "expiry_date": soon_date},
    )
    # 1 far future batch
    client.post(
        "/api/v1/batches/",
        json={"product_id": pid, "batch_number": "SAFE", "quantity": 10, "expiry_date": far_date},
    )

    # Call alerts endpoint
    alerts_resp = client.get("/api/v1/alerts/?expiring_within_days=30")
    assert alerts_resp.status_code == 200
    data = alerts_resp.json()

    counts = data["counts"]
    assert counts["expired_batches_count"] >= 1
    assert counts["expiring_batches_count"] >= 1

    expired_numbers = [b["batch_number"] for b in data["expired_batches"]]
    assert "EXPIRED" in expired_numbers

    expiring_numbers = [b["batch_number"] for b in data["expiring_batches"]]
    assert "SOON" in expiring_numbers
    assert "SAFE" not in expiring_numbers


def test_low_stock_alert_detection(client):
    """Products with stock_quantity <= reorder_level should appear in low-stock alerts."""
    p_low = _create_product(client, sku="LOW-ALERT", stock=2, reorder=10)
    p_ok = _create_product(client, sku="OK-STOCK", stock=50, reorder=10)

    alerts = client.get("/api/v1/alerts/").json()
    low_skus = [p["sku"] for p in alerts["low_stock_products"]]

    assert "LOW-ALERT" in low_skus
    assert "OK-STOCK" not in low_skus


# -------------------------------------------------------------------------
# 5. Batch Updates & Deletion
# -------------------------------------------------------------------------


def test_update_batch_adjusts_product_stock(client):
    """Changing batch quantity updates product stock by the difference."""
    product = _create_product(client, sku="ADJ-01", stock=0)
    pid = product["id"]

    batch = client.post(
        "/api/v1/batches/",
        json={"product_id": pid, "batch_number": "ADJ-B", "quantity": 20},
    ).json()
    bid = batch["id"]

    # Update quantity from 20 to 35
    patch_resp = client.patch(
        f"/api/v1/batches/{bid}",
        json={"quantity": 35},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["quantity"] == 35

    # Product stock should now be 35
    assert client.get(f"/api/v1/products/{pid}").json()["stock_quantity"] == 35


def test_delete_batch_reduces_product_stock(client):
    """Deleting a batch decreases product stock."""
    product = _create_product(client, sku="DEL-B01", stock=0)
    pid = product["id"]

    batch = client.post(
        "/api/v1/batches/",
        json={"product_id": pid, "batch_number": "DELETE-ME", "quantity": 15},
    ).json()
    bid = batch["id"]

    assert client.get(f"/api/v1/products/{pid}").json()["stock_quantity"] == 15

    del_resp = client.delete(f"/api/v1/batches/{bid}")
    assert del_resp.status_code == 204

    # Product stock should return to 0
    assert client.get(f"/api/v1/products/{pid}").json()["stock_quantity"] == 0
