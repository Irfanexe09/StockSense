"""
StockSense — Category service.

All database operations for categories live here, keeping the API
endpoint files thin and focused on HTTP concerns only.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def get_categories(db: Session, skip: int = 0, limit: int = 100) -> list[Category]:
    """Return a paginated list of categories."""
    stmt = select(Category).offset(skip).limit(limit).order_by(Category.name)
    return list(db.scalars(stmt).all())


def get_category(db: Session, category_id: int) -> Category | None:
    """Return a single category by ID, or None if not found."""
    return db.get(Category, category_id)


def get_category_by_name(db: Session, name: str) -> Category | None:
    """Return a category by its exact name, or None."""
    stmt = select(Category).where(Category.name == name)
    return db.scalars(stmt).first()


def create_category(db: Session, data: CategoryCreate) -> Category:
    """Insert a new category and return it."""
    category = Category(name=data.name, description=data.description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(
    db: Session, category: Category, data: CategoryUpdate
) -> Category:
    """Apply partial updates to an existing category."""
    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category: Category) -> None:
    """Delete a category from the database."""
    db.delete(category)
    db.commit()
