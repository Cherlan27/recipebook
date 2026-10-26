import pytest

from app.db import session as db_session


@pytest.mark.anyio
async def test_init_db_creates_missing_database_directory(monkeypatch, tmp_path):
    target = tmp_path / "new" / "nested" / "app.db"
    monkeypatch.setattr(db_session.settings, "database_path", target)

    await db_session.init_db()

    assert target.parent.is_dir()


@pytest.mark.anyio
async def test_init_db_raises_diagnosable_error_for_unusable_path(monkeypatch, tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory")
    target = blocker / "sub" / "app.db"
    monkeypatch.setattr(db_session.settings, "database_path", target)

    with pytest.raises(RuntimeError) as exc_info:
        await db_session.init_db()

    assert str(target.parent) in str(exc_info.value)
