"""
Alembic environment configuration for StockSense.

This file is executed every time you run an Alembic command
(e.g. `alembic revision --autogenerate` or `alembic upgrade head`).

It tells Alembic two things:
  1. WHERE to connect  — the database URL from our app settings.
  2. WHAT to compare   — our Base.metadata, so autogenerate can detect
                         new tables, columns, or changes in our models.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# -- Alembic Config object (reads alembic.ini) --
config = context.config

# -- Python logging from alembic.ini --
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -- Import our application's database URL and Base metadata --
from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402

# Set the database URL programmatically so it is never hardcoded in alembic.ini.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Import all model modules so that Base.metadata is fully populated
# before Alembic inspects it.
from app.models import Category, Product  # noqa: E402, F401

# This is what Alembic compares against the live database schema.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    Useful for reviewing migration SQL before applying it.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Connects to the database and applies migrations directly.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
