"""
StockSense — Category Pydantic schemas.

These classes define the exact shape of JSON data that the API
accepts (request bodies) and returns (responses).

Why separate from SQLAlchemy models?
  - Models describe *database tables*.
  - Schemas describe *API contracts* — what the client sends and receives.
  Keeping them separate lets you expose only what the client needs
  and validate input without leaking internal database details.
"""

from pydantic import BaseModel, ConfigDict, Field


# --- Request schemas (what the client sends) ---


class CategoryCreate(BaseModel):
    """Fields required to create a new category."""

    name: str = Field(min_length=1, max_length=100, examples=["Beverages"])
    description: str | None = Field(
        default=None, max_length=500, examples=["Drinks and liquid refreshments"]
    )


class CategoryUpdate(BaseModel):
    """Fields that can be updated on an existing category.

    All fields are optional — the client sends only what changed.
    """

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


# --- Response schemas (what the API returns) ---


class CategoryResponse(BaseModel):
    """A category as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
