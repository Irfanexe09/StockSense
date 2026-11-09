"""
Tests for the products API.
"""


def test_create_product(client):
    """POST /api/v1/products/ should create and return a product."""
    response = client.post(
        "/api/v1/products/",
        json={
            "sku": "BEV-001",
            "name": "Orange Juice 1L",
            "cost_price": 45.00,
            "selling_price": 65.00,
            "stock_quantity": 100,
            "reorder_level": 10,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "BEV-001"
    assert data["name"] == "Orange Juice 1L"
    assert data["stock_quantity"] == 100
    assert data["is_low_stock"] is False


def test_create_product_with_category(client):
    """A product can optionally belong to a category."""
    cat_resp = client.post("/api/v1/categories/", json={"name": "Beverages"})
    cat_id = cat_resp.json()["id"]
    response = client.post(
        "/api/v1/products/",
        json={
            "sku": "BEV-002",
            "name": "Apple Juice 500ml",
            "cost_price": 30.00,
            "selling_price": 50.00,
            "category_id": cat_id,
        },
    )
    assert response.status_code == 201
    assert response.json()["category_id"] == cat_id


def test_create_product_invalid_category(client):
    """Creating a product with a non-existent category should return 404."""
    response = client.post(
        "/api/v1/products/",
        json={
            "sku": "X-001",
            "name": "Ghost Product",
            "cost_price": 10.00,
            "selling_price": 20.00,
            "category_id": 999,
        },
    )
    assert response.status_code == 404


def test_create_duplicate_sku(client):
    """Two products cannot have the same SKU."""
    client.post(
        "/api/v1/products/",
        json={"sku": "DUP-001", "name": "Item A", "cost_price": 10, "selling_price": 20},
    )
    response = client.post(
        "/api/v1/products/",
        json={"sku": "DUP-001", "name": "Item B", "cost_price": 15, "selling_price": 25},
    )
    assert response.status_code == 409


def test_list_products(client):
    """GET /api/v1/products/ should return items and total count."""
    client.post(
        "/api/v1/products/",
        json={"sku": "A-001", "name": "Item A", "cost_price": 10, "selling_price": 20},
    )
    client.post(
        "/api/v1/products/",
        json={"sku": "B-001", "name": "Item B", "cost_price": 15, "selling_price": 25},
    )
    response = client.get("/api/v1/products/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_search_products(client):
    """Search should filter by name or SKU substring."""
    client.post(
        "/api/v1/products/",
        json={"sku": "JUI-001", "name": "Orange Juice", "cost_price": 10, "selling_price": 20},
    )
    client.post(
        "/api/v1/products/",
        json={"sku": "MLK-001", "name": "Whole Milk", "cost_price": 10, "selling_price": 20},
    )
    response = client.get("/api/v1/products/", params={"search": "juice"})
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["sku"] == "JUI-001"


def test_low_stock_filter(client):
    """low_stock_only=true should return only products at or below reorder level."""
    client.post(
        "/api/v1/products/",
        json={
            "sku": "LO-001",
            "name": "Low Item",
            "cost_price": 5,
            "selling_price": 10,
            "stock_quantity": 3,
            "reorder_level": 5,
        },
    )
    client.post(
        "/api/v1/products/",
        json={
            "sku": "HI-001",
            "name": "Stocked Item",
            "cost_price": 5,
            "selling_price": 10,
            "stock_quantity": 100,
            "reorder_level": 5,
        },
    )
    response = client.get("/api/v1/products/", params={"low_stock_only": True})
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["sku"] == "LO-001"
    assert data["items"][0]["is_low_stock"] is True


def test_get_product_by_id(client):
    """GET /api/v1/products/{id} should return the product."""
    create_resp = client.post(
        "/api/v1/products/",
        json={"sku": "P-100", "name": "Test Product", "cost_price": 10, "selling_price": 20},
    )
    pid = create_resp.json()["id"]
    response = client.get(f"/api/v1/products/{pid}")
    assert response.status_code == 200
    assert response.json()["sku"] == "P-100"


def test_get_missing_product(client):
    """GET /api/v1/products/999 should return 404."""
    response = client.get("/api/v1/products/999")
    assert response.status_code == 404


def test_update_product(client):
    """PATCH /api/v1/products/{id} should update fields."""
    create_resp = client.post(
        "/api/v1/products/",
        json={"sku": "UP-001", "name": "Old Name", "cost_price": 10, "selling_price": 20},
    )
    pid = create_resp.json()["id"]
    response = client.patch(
        f"/api/v1/products/{pid}",
        json={"name": "New Name", "selling_price": 25.00},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert float(data["selling_price"]) == 25.00


def test_delete_product(client):
    """DELETE /api/v1/products/{id} should remove the product."""
    create_resp = client.post(
        "/api/v1/products/",
        json={"sku": "DEL-001", "name": "Doomed", "cost_price": 5, "selling_price": 10},
    )
    pid = create_resp.json()["id"]
    response = client.delete(f"/api/v1/products/{pid}")
    assert response.status_code == 204

    response = client.get(f"/api/v1/products/{pid}")
    assert response.status_code == 404
