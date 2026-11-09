"""
StockSense — Database engine and session factory.

Provides:
  - engine:       The SQLAlchemy async-compatible engine connected to PostgreSQL.
  - SessionLocal:  A session factory for creating database sessions.
  - Base:         The declarative base class that all ORM models will inherit from.
  - get_db():     A FastAPI dependency that yields a session per request.

Why this file exists:
  Every part of the backend that talks to the database needs a "connection".
  Instead of creating connections everywhere, we configure one engine here
  and hand out short-lived sessions through get_db().  FastAPI's dependency
  injection calls get_db() automatically for each request and ensures the
  session is properly closed afterwards — even if an error occurs.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


# --- Engine ---
# The engine is the starting point for all SQLAlchemy database operations.
# It manages a pool of actual database connections behind the scenes.
engine = create_engine(
    settings.database_url,
    # echo=True logs every SQL statement — useful during development.
    # Controlled via the DEBUG setting so it stays quiet in production.
    echo=settings.debug,
)

# --- Session factory ---
# sessionmaker() returns a *class* that creates new Session objects.
# Each Session represents a single "conversation" with the database.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# --- Declarative base ---
# All ORM model classes (Product, Sale, etc.) will inherit from Base.
# SQLAlchemy uses this to keep a registry of all tables.
class Base(DeclarativeBase):
    pass


# --- FastAPI dependency ---
def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session for a single request, then close it.

    Usage in an endpoint:
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
