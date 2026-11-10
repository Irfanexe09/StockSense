"""
StockSense — Purchase Order service.

Implements purchase order creation, line items, status transitions,
and atomic inventory receipt processing with batch creation.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.product import Product
from app.models.purchase_order import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderReceipt,
    PurchaseOrderReceiptItem,
    PurchaseOrderStatus,
)
from app.models.supplier import Supplier
from app.schemas.batch import BatchCreate
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    ReceiveOrderRequest,
)
from app.services.batch_service import create_batch


class PurchaseOrderError(ValueError):
    """Raised when purchase order operation or status transition is invalid."""
    pass


def _generate_po_number(db: Session) -> str:
    today = datetime.now(timezone.utc).date()
    date_str = today.strftime("%Y%m%d")
    prefix = f"PO-{date_str}-"
    count = db.scalar(
        select(func.count(PurchaseOrder.id)).where(
            PurchaseOrder.order_number.like(f"{prefix}%")
        )
    ) or 0
    return f"{prefix}{count + 1:04d}"


def _generate_receipt_number(db: Session) -> str:
    today = datetime.now(timezone.utc).date()
    date_str = today.strftime("%Y%m%d")
    prefix = f"POR-{date_str}-"
    count = db.scalar(
        select(func.count(PurchaseOrderReceipt.id)).where(
            PurchaseOrderReceipt.receipt_number.like(f"{prefix}%")
        )
    ) or 0
    return f"{prefix}{count + 1:04d}"


def create_purchase_order(db: Session, data: PurchaseOrderCreate) -> PurchaseOrder:
    supplier = db.get(Supplier, data.supplier_id)
    if not supplier:
        raise PurchaseOrderError(f"Supplier with id {data.supplier_id} not found.")
    if not supplier.is_active:
        raise PurchaseOrderError(
            f"Cannot create purchase order for inactive supplier '{supplier.name}'."
        )

    if not data.items:
        raise PurchaseOrderError("Purchase order must have at least one line item.")

    po_items: list[PurchaseOrderItem] = []
    total_amount = Decimal("0.00")

    for item_data in data.items:
        if item_data.quantity <= 0:
            raise PurchaseOrderError("Item quantity must be greater than zero.")
        if item_data.unit_cost < Decimal("0.00"):
            raise PurchaseOrderError("Unit cost cannot be negative.")

        product = db.get(Product, item_data.product_id)
        if not product:
            raise PurchaseOrderError(f"Product with id {item_data.product_id} not found.")

        line_total = Decimal(str(item_data.unit_cost)) * item_data.quantity
        total_amount += line_total

        po_items.append(
            PurchaseOrderItem(
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                quantity=item_data.quantity,
                received_quantity=0,
                unit_cost=item_data.unit_cost,
                line_total=line_total,
            )
        )

    initial_status = (
        PurchaseOrderStatus.ORDERED.value
        if data.submit_now
        else PurchaseOrderStatus.DRAFT.value
    )

    order_date = data.order_date or datetime.now(timezone.utc).date()
    order_number = _generate_po_number(db)

    po = PurchaseOrder(
        order_number=order_number,
        supplier_id=supplier.id,
        status=initial_status,
        order_date=order_date,
        expected_delivery_date=data.expected_delivery_date,
        notes=data.notes.strip() if data.notes else None,
        total_amount=total_amount,
        items=po_items,
    )
    db.add(po)
    db.commit()
    db.refresh(po)
    return po


def get_purchase_order(db: Session, po_id: int) -> PurchaseOrder | None:
    return db.get(PurchaseOrder, po_id)


def list_purchase_orders(
    db: Session,
    supplier_id: int | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[PurchaseOrder]:
    stmt = select(PurchaseOrder)
    if supplier_id is not None:
        stmt = stmt.where(PurchaseOrder.supplier_id == supplier_id)
    if status is not None:
        stmt = stmt.where(PurchaseOrder.status == status.upper())
    stmt = stmt.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def update_purchase_order(
    db: Session, po: PurchaseOrder, data: PurchaseOrderUpdate
) -> PurchaseOrder:
    if po.status != PurchaseOrderStatus.DRAFT.value:
        raise PurchaseOrderError(
            f"Cannot edit purchase order in '{po.status}' status. Only DRAFT orders can be edited."
        )

    update_fields = data.model_dump(exclude_unset=True)

    if "supplier_id" in update_fields and update_fields["supplier_id"]:
        supplier = db.get(Supplier, update_fields["supplier_id"])
        if not supplier:
            raise PurchaseOrderError(f"Supplier with id {update_fields['supplier_id']} not found.")
        if not supplier.is_active:
            raise PurchaseOrderError(
                f"Cannot assign inactive supplier '{supplier.name}'."
            )
        po.supplier_id = supplier.id

    if "order_date" in update_fields:
        po.order_date = update_fields["order_date"] or datetime.now(timezone.utc).date()

    if "expected_delivery_date" in update_fields:
        po.expected_delivery_date = update_fields["expected_delivery_date"]

    if "notes" in update_fields:
        po.notes = update_fields["notes"].strip() if update_fields["notes"] else None

    # Rebuild items if provided
    if "items" in update_fields and update_fields["items"] is not None:
        if not update_fields["items"]:
            raise PurchaseOrderError("Purchase order must have at least one line item.")

        po.items.clear()
        total_amount = Decimal("0.00")

        for item_data in data.items or []:
            if item_data.quantity <= 0:
                raise PurchaseOrderError("Item quantity must be greater than zero.")
            if item_data.unit_cost < Decimal("0.00"):
                raise PurchaseOrderError("Unit cost cannot be negative.")

            product = db.get(Product, item_data.product_id)
            if not product:
                raise PurchaseOrderError(f"Product with id {item_data.product_id} not found.")

            line_total = Decimal(str(item_data.unit_cost)) * item_data.quantity
            total_amount += line_total

            po.items.append(
                PurchaseOrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    product_sku=product.sku,
                    quantity=item_data.quantity,
                    received_quantity=0,
                    unit_cost=item_data.unit_cost,
                    line_total=line_total,
                )
            )

        po.total_amount = total_amount

    po.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(po)
    return po


def submit_purchase_order(db: Session, po: PurchaseOrder) -> PurchaseOrder:
    if po.status != PurchaseOrderStatus.DRAFT.value:
        raise PurchaseOrderError(
            f"Cannot submit purchase order in '{po.status}' status. Only DRAFT orders can be ordered."
        )
    po.status = PurchaseOrderStatus.ORDERED.value
    po.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(po)
    return po


def cancel_purchase_order(db: Session, po: PurchaseOrder) -> PurchaseOrder:
    if po.status not in (
        PurchaseOrderStatus.DRAFT.value,
        PurchaseOrderStatus.ORDERED.value,
    ):
        raise PurchaseOrderError(
            f"Cannot cancel purchase order in '{po.status}' status."
        )

    # Prevent cancellation if any items have been received
    if any(item.received_quantity > 0 for item in po.items):
        raise PurchaseOrderError(
            "Cannot cancel purchase order because some items have already been received."
        )

    po.status = PurchaseOrderStatus.CANCELLED.value
    po.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(po)
    return po


def receive_purchase_order_items(
    db: Session, po: PurchaseOrder, request: ReceiveOrderRequest
) -> PurchaseOrderReceipt:
    """
    Atomically receive items for a purchase order.

    Validations:
      1. Order must be in ORDERED or PARTIALLY_RECEIVED status.
      2. Each received item must exist in the PO.
      3. Quantity received must not exceed outstanding unreceived quantity.
      4. Creates a new inventory Batch for each received item and increments
         product stock_quantity.
      5. Updates PO line items and sets PO status (PARTIALLY_RECEIVED or RECEIVED).
      6. Rolls back entirely if any error occurs.
    """
    if po.status not in (
        PurchaseOrderStatus.ORDERED.value,
        PurchaseOrderStatus.PARTIALLY_RECEIVED.value,
    ):
        raise PurchaseOrderError(
            f"Cannot receive items for purchase order in '{po.status}' status. "
            "Order must be ORDERED or PARTIALLY_RECEIVED."
        )

    if not request.items:
        raise PurchaseOrderError("No items specified for receipt.")

    # Map po items by id for fast validation
    item_map = {item.id: item for item in po.items}

    receipt_items: list[PurchaseOrderReceiptItem] = []
    receipt_number = _generate_receipt_number(db)

    receipt = PurchaseOrderReceipt(
        purchase_order_id=po.id,
        receipt_number=receipt_number,
        notes=request.notes.strip() if request.notes else None,
    )
    db.add(receipt)

    try:
        for rcv_input in request.items:
            po_item = item_map.get(rcv_input.purchase_order_item_id)
            if not po_item:
                raise PurchaseOrderError(
                    f"Purchase order item id {rcv_input.purchase_order_item_id} "
                    f"does not belong to purchase order {po.order_number}."
                )

            if rcv_input.quantity_received <= 0:
                raise PurchaseOrderError("Received quantity must be greater than zero.")

            remaining = po_item.remaining_quantity
            if rcv_input.quantity_received > remaining:
                raise PurchaseOrderError(
                    f"Cannot receive {rcv_input.quantity_received} units for '{po_item.product_name}'. "
                    f"Only {remaining} units remain to be received."
                )

            if not rcv_input.batch_number.strip():
                raise PurchaseOrderError("Batch number is required for received items.")

            if not po_item.product_id:
                raise PurchaseOrderError(
                    f"Product for item '{po_item.product_name}' no longer exists in catalog."
                )

            # Create inventory batch without committing immediately
            batch_data = BatchCreate(
                product_id=po_item.product_id,
                batch_number=rcv_input.batch_number.strip(),
                quantity=rcv_input.quantity_received,
                expiry_date=rcv_input.expiry_date,
                received_date=datetime.now(timezone.utc).date(),
            )
            batch = create_batch(db, batch_data, commit=False)

            # Update line item received count
            po_item.received_quantity += rcv_input.quantity_received

            receipt_items.append(
                PurchaseOrderReceiptItem(
                    receipt=receipt,
                    purchase_order_item_id=po_item.id,
                    batch_id=batch.id,
                    quantity_received=rcv_input.quantity_received,
                    batch_number=rcv_input.batch_number.strip(),
                    expiry_date=rcv_input.expiry_date,
                )
            )

        receipt.items = receipt_items

        # Determine new status of the PO
        all_fulfilled = all(item.is_fully_received for item in po.items)
        if all_fulfilled:
            po.status = PurchaseOrderStatus.RECEIVED.value
        else:
            po.status = PurchaseOrderStatus.PARTIALLY_RECEIVED.value

        po.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(receipt)
        db.refresh(po)
    except Exception:
        db.rollback()
        raise

    return receipt
