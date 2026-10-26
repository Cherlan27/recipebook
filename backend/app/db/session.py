import asyncio
from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.migrate import run_migrations


def create_engine_with_foreign_keys(url: str) -> AsyncEngine:
    """SQLite enforces foreign keys only per connection, so switch them on for every new one.

    Only application connections do this; the migration connection deliberately does not
    (see app/db/migrations/env.py).
    """
    engine = create_async_engine(url)

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = create_engine_with_foreign_keys(settings.database_url)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    """Ensure the database directory exists, then bring the schema up to date (see ADR-8)."""
    try:
        settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(
            f"Cannot create database directory at {settings.database_path.parent}: {exc}"
        ) from exc

    # Alembic is synchronous and must not run on the event loop's thread.
    await asyncio.to_thread(run_migrations, settings.database_path)
