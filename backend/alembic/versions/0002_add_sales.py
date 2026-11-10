"""add sales and sale_items tables

Revision ID: 0002_add_sales
Revises: 0001_initial_and_batches
Create Date: 2026-11-10 08:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_add_sales'
down_revision: Union[str, None] = '0001_initial_and_batches'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sales',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('receipt_number', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('item_count', sa.Integer(), nullable=False, server_default='0'),
    )

    op.create_table(
        'sale_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sale_id', sa.Integer(), sa.ForeignKey('sales.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('product_name', sa.String(200), nullable=False),
        sa.Column('product_sku', sa.String(50), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('line_total', sa.Numeric(precision=12, scale=2), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('sale_items')
    op.drop_table('sales')
