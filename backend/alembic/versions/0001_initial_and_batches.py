"""create categories, products, and batches tables with stock backfill

Revision ID: 0001_initial_and_batches
Revises:
Create Date: 2026-11-09 21:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial_and_batches'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 2. Products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('cost_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('selling_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reorder_level', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=True)

    # 3. Batches table
    op.create_table(
        'batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('batch_number', sa.String(length=100), nullable=False),
        sa.Column('initial_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('received_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_batches_product_id'), 'batches', ['product_id'], unique=False)
    op.create_index(op.f('ix_batches_batch_number'), 'batches', ['batch_number'], unique=False)
    op.create_index(op.f('ix_batches_expiry_date'), 'batches', ['expiry_date'], unique=False)

    # 4. Data migration: Backfill batches for any existing products with stock_quantity > 0
    # This guarantees Product.stock_quantity == sum(batch.quantity) holds true.
    op.execute(
        """
        INSERT INTO batches (product_id, batch_number, initial_quantity, quantity, expiry_date, received_date, created_at)
        SELECT id, 'INIT-' || sku, stock_quantity, stock_quantity, NULL, CURRENT_DATE, CURRENT_TIMESTAMP
        FROM products
        WHERE stock_quantity > 0
        """
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_batches_expiry_date'), table_name='batches')
    op.drop_index(op.f('ix_batches_batch_number'), table_name='batches')
    op.drop_index(op.f('ix_batches_product_id'), table_name='batches')
    op.drop_table('batches')
    op.drop_index(op.f('ix_products_sku'), table_name='products')
    op.drop_table('products')
    op.drop_table('categories')
