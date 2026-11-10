"""
Models package — SQLAlchemy ORM models.

Import every model here so that:
  1. `from app.models import Category, Product, Batch, Sale, SaleItem` works everywhere.
  2. Base.metadata is fully populated when Alembic inspects it.
"""

from app.models.batch import Batch
from app.models.category import Category
from app.models.product import Product
from app.models.sale import Sale, SaleItem

__all__ = ["Batch", "Category", "Product", "Sale", "SaleItem"]
