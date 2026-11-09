"""
Shared test fixtures for the StockSense backend.

The key fixture here is `client` — it creates a fresh SQLite database
in memory for every test, overrides FastAPI's `get_db` dependency to
use that database, and yields a TestClient so tests can call endpoints
without needing PostgreSQL running.

Why SQLite for tests?
  SQLite runs entirely in memory — no Docker, no server, no cleanup.
  This makes tests fast and self-contained.  The production app still
  uses PostgreSQL; only the test suite swaps the database.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

# Import models so Base.metadata knows about all tables.
from app.models import Batch, Category, Product  # noqa: F401

# In-memory SQLite engine.
# StaticPool ensures every connection shares the same underlying
# database — without this, create_all and the session would each
# get their own (empty) in-memory database.
TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=TEST_ENGINE, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db():
    """Yield a clean database session for one test, then tear down all tables."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def client(db: Session):
    """Yield a TestClient with the database dependency overridden."""

    def _override_get_db():
        try:
            yield db
        finally:
            pass  # session is managed by the `db` fixture

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()
