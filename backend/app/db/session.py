from collections.abc import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(settings.database_url)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    """Ensure the database directory exists, then open a connection so the SQLite driver creates the database file."""
    try:
        settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(
            f"Cannot create database directory at {settings.database_path.parent}: {exc}"
        ) from exc

    try:
        async with engine.begin():
            pass
    except SQLAlchemyError as exc:
        raise RuntimeError(
            f"Cannot open database at {settings.database_path}: {exc}"
        ) from exc
