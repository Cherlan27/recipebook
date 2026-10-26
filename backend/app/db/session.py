import asyncio
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.migrate import run_migrations

engine = create_async_engine(settings.database_url)
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
