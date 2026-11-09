"""
Tests for the categories API.
"""


def test_create_category(client):
    """POST /api/v1/categories/ should create and return a category."""
    response = client.post(
        "/api/v1/categories/",
        json={"name": "Beverages", "description": "Drinks"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Beverages"
    assert data["description"] == "Drinks"
    assert "id" in data


def test_create_duplicate_category(client):
    """Creating a category with the same name should return 409."""
    client.post("/api/v1/categories/", json={"name": "Dairy"})
    response = client.post("/api/v1/categories/", json={"name": "Dairy"})
    assert response.status_code == 409


def test_list_categories(client):
    """GET /api/v1/categories/ should return all categories."""
    client.post("/api/v1/categories/", json={"name": "Snacks"})
    client.post("/api/v1/categories/", json={"name": "Dairy"})
    response = client.get("/api/v1/categories/")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2


def test_get_category_by_id(client):
    """GET /api/v1/categories/{id} should return the category."""
    create_resp = client.post("/api/v1/categories/", json={"name": "Frozen"})
    cat_id = create_resp.json()["id"]
    response = client.get(f"/api/v1/categories/{cat_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Frozen"


def test_get_missing_category(client):
    """GET /api/v1/categories/999 should return 404."""
    response = client.get("/api/v1/categories/999")
    assert response.status_code == 404


def test_update_category(client):
    """PATCH /api/v1/categories/{id} should update fields."""
    create_resp = client.post("/api/v1/categories/", json={"name": "Drinks"})
    cat_id = create_resp.json()["id"]
    response = client.patch(
        f"/api/v1/categories/{cat_id}",
        json={"name": "Beverages"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Beverages"


def test_delete_category(client):
    """DELETE /api/v1/categories/{id} should remove the category."""
    create_resp = client.post("/api/v1/categories/", json={"name": "Temp"})
    cat_id = create_resp.json()["id"]
    response = client.delete(f"/api/v1/categories/{cat_id}")
    assert response.status_code == 204

    # Verify it's gone.
    response = client.get(f"/api/v1/categories/{cat_id}")
    assert response.status_code == 404


def test_delete_category_with_products(client):
    """Cannot delete a category that still has products."""
    cat_resp = client.post("/api/v1/categories/", json={"name": "Dairy"})
    cat_id = cat_resp.json()["id"]
    client.post(
        "/api/v1/products/",
        json={
            "sku": "DAI-001",
            "name": "Milk 1L",
            "cost_price": 30,
            "selling_price": 45,
            "category_id": cat_id,
        },
    )
    response = client.delete(f"/api/v1/categories/{cat_id}")
    assert response.status_code == 409
