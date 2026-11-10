"""add suppliers, purchase_orders, and receiving tables

Revision ID: 0003_add_suppliers_and_purchases
Revises: 0002_add_sales
Create Date: 2026-11-10 08:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_add_suppliers_and_purchases'
down_revision: Union[str, None] = '0002_add_sales'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(150), nullable=False, unique=True, index=True),
        sa.Column('contact_name', sa.String(100), nullable=True),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('address', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'purchase_orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_number', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('suppliers.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='DRAFT', index=True),
        sa.Column('order_date', sa.Date(), nullable=False),
        sa.Column('expected_delivery_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.String(1000), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'purchase_order_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('purchase_order_id', sa.Integer(), sa.ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('product_name', sa.String(200), nullable=False),
        sa.Column('product_sku', sa.String(50), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('received_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unit_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('line_total', sa.Numeric(precision=12, scale=2), nullable=False),
    )

    op.create_table(
        'purchase_order_receipts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('purchase_order_id', sa.Integer(), sa.ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('receipt_number', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sa.String(500), nullable=True),
    )

    op.create_table(
        'purchase_order_receipt_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('receipt_id', sa.Integer(), sa.ForeignKey('purchase_order_receipts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('purchase_order_item_id', sa.Integer(), sa.ForeignKey('purchase_order_items.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('batch_id', sa.Integer(), sa.ForeignKey('batches.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('quantity_received', sa.Integer(), nullable=False),
        sa.Column('batch_number', sa.String(100), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('purchase_order_receipt_items')
    op.drop_table('purchase_order_receipts')
    op.drop_table('purchase_order_items')
    op.drop_table('purchase_orders')
    op.drop_table('suppliers')
