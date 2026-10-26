from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.migrate import run_migrations
from app.db.session import create_engine_with_foreign_keys


@pytest.fixture
async def db_session(tmp_path) -> AsyncGenerator[AsyncSession, None]:
    """A session on a temporary database built by the real migrations."""
    database_path = tmp_path / "recipes.db"
    run_migrations(database_path)
    engine = create_engine_with_foreign_keys(f"sqlite+aiosqlite:///{database_path}")
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()
