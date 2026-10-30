from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.migrate import run_migrations
from app.db.session import create_engine_with_foreign_keys, get_db
from app.main import app


@pytest.fixture
async def db_session(tmp_path) -> AsyncGenerator[AsyncSession, None]:
    """A session on a temporary database built by the real migrations."""
    database_path = tmp_path / "recipes.db"
    run_migrations(database_path)
    engine = create_engine_with_foreign_keys(f"sqlite+aiosqlite:///{database_path}")
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


@pytest.fixture
def client(db_session, tmp_path) -> Generator[TestClient, None, None]:
    """A TestClient whose `get_db` reads the temporary database of `db_session`.

    Seed data through `db_session` and commit before calling the client.
    """
    url = f"sqlite+aiosqlite:///{tmp_path / 'recipes.db'}"

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        engine = create_engine_with_foreign_keys(url)
        try:
            async with async_sessionmaker(engine, expire_on_commit=False)() as session:
                yield session
        finally:
            await engine.dispose()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
