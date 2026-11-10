"""
Tests for StockSense Suppliers API.

Covers:
  - Supplier creation with required/optional fields
  - Duplicate name rejection
  - Listing suppliers and active_only filter
  - Single supplier retrieval and 404 handling
  - Supplier update (name, contact info, is_active flag)
  - Supplier deletion rules
"""

import pytest


def _create_supplier(client, name="Acme Supplies", is_active=True, **kwargs):
    payload = {"name": name, "is_active": is_active, **kwargs}
    resp = client.post("/api/v1/suppliers/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_supplier(client):
    supplier = _create_supplier(
        client,
        name="Global Beverage Corp",
        contact_name="Alice Smith",
        email="alice@globalbev.com",
        phone="+1 555-0100",
        address="100 Logistics Blvd",
    )
    assert supplier["id"] is not None
    assert supplier["name"] == "Global Beverage Corp"
    assert supplier["contact_name"] == "Alice Smith"
    assert supplier["email"] == "alice@globalbev.com"
    assert supplier["is_active"] is True


def test_create_duplicate_supplier_rejected(client):
    _create_supplier(client, name="Unique Supplier")
    resp = client.post("/api/v1/suppliers/", json={"name": "Unique Supplier"})
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_list_suppliers_and_active_filter(client):
    _create_supplier(client, name="Active 1", is_active=True)
    _create_supplier(client, name="Active 2", is_active=True)
    _create_supplier(client, name="Inactive 1", is_active=False)

    # All suppliers
    resp_all = client.get("/api/v1/suppliers/")
    assert resp_all.status_code == 200
    assert len(resp_all.json()) == 3

    # Active only
    resp_active = client.get("/api/v1/suppliers/?active_only=true")
    assert resp_active.status_code == 200
    names = [s["name"] for s in resp_active.json()]
    assert "Active 1" in names
    assert "Active 2" in names
    assert "Inactive 1" not in names


def test_get_supplier_by_id(client):
    supplier = _create_supplier(client, name="Target Supplier")
    resp = client.get(f"/api/v1/suppliers/{supplier['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Target Supplier"


def test_get_nonexistent_supplier(client):
    resp = client.get("/api/v1/suppliers/99999")
    assert resp.status_code == 404


def test_update_supplier(client):
    supplier = _create_supplier(client, name="Original Name", is_active=True)
    resp = client.patch(
        f"/api/v1/suppliers/{supplier['id']}",
        json={"name": "Updated Name", "is_active": False},
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["name"] == "Updated Name"
    assert updated["is_active"] is False


def test_delete_supplier_without_orders(client):
    supplier = _create_supplier(client, name="Disposable Supplier")
    resp = client.delete(f"/api/v1/suppliers/{supplier['id']}")
    assert resp.status_code == 204

    # Verify gone
    resp_check = client.get(f"/api/v1/suppliers/{supplier['id']}")
    assert resp_check.status_code == 404
