"""
StockSense — Supplier service.

Business logic for managing suppliers and vendors.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.purchase_order import PurchaseOrder
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate


def create_supplier(db: Session, data: SupplierCreate) -> Supplier:
    existing = get_supplier_by_name(db, data.name)
    if existing:
        raise ValueError(f"Supplier with name {data.name!r} already exists.")

    supplier = Supplier(
        name=data.name.strip(),
        contact_name=data.contact_name.strip() if data.contact_name else None,
        email=data.email.strip() if data.email else None,
        phone=data.phone.strip() if data.phone else None,
        address=data.address.strip() if data.address else None,
        is_active=data.is_active,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def get_supplier(db: Session, supplier_id: int) -> Supplier | None:
    return db.get(Supplier, supplier_id)


def get_supplier_by_name(db: Session, name: str) -> Supplier | None:
    stmt = select(Supplier).where(Supplier.name.ilike(name.strip()))
    return db.scalar(stmt)


def list_suppliers(
    db: Session,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[Supplier]:
    stmt = select(Supplier)
    if active_only:
        stmt = stmt.where(Supplier.is_active.is_(True))
    stmt = stmt.order_by(Supplier.name.asc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def update_supplier(db: Session, supplier: Supplier, data: SupplierUpdate) -> Supplier:
    update_fields = data.model_dump(exclude_unset=True)

    if "name" in update_fields and update_fields["name"]:
        new_name = update_fields["name"].strip()
        if new_name.lower() != supplier.name.lower():
            existing = get_supplier_by_name(db, new_name)
            if existing and existing.id != supplier.id:
                raise ValueError(f"Supplier with name {new_name!r} already exists.")
        supplier.name = new_name

    for field in ("contact_name", "email", "phone", "address"):
        if field in update_fields:
            val = update_fields[field]
            setattr(supplier, field, val.strip() if isinstance(val, str) else val)

    if "is_active" in update_fields and update_fields["is_active"] is not None:
        supplier.is_active = update_fields["is_active"]

    db.commit()
    db.refresh(supplier)
    return supplier


def delete_supplier(db: Session, supplier: Supplier) -> None:
    # Check if there are associated purchase orders
    stmt = select(PurchaseOrder.id).where(PurchaseOrder.supplier_id == supplier.id).limit(1)
    has_orders = db.scalar(stmt) is not None
    if has_orders:
        raise ValueError(
            f"Cannot delete supplier '{supplier.name}' because purchase orders exist for them. "
            "Deactivate the supplier instead."
        )

    db.delete(supplier)
    db.commit()
