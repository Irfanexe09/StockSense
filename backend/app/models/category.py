"""
StockSense — Category database model.

A category groups related products (e.g. "Beverages", "Dairy", "Snacks").
This keeps the product catalog organized and makes filtering/reporting easier.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), default=None)

    # Relationship: one category has many products.
    # back_populates links this to Product.category so you can traverse both ways.
    products: Mapped[list["Product"]] = relationship(
        "Product", back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name!r}>"


# Import here to avoid circular import issues — SQLAlchemy resolves
# the string "Product" in the relationship() lazily.
from app.models.product import Product  # noqa: E402, F401
