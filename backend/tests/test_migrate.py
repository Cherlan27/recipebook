import sqlite3
from pathlib import Path

import pytest

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.db.migrate import run_migrations

FIXTURES = Path(__file__).parent / "fixtures"
OK_SCRIPTS = FIXTURES / "migrations_ok"
FAILING_SCRIPTS = FIXTURES / "migrations_failing"


def current_revision(database_path: Path) -> str | None:
    with sqlite3.connect(database_path) as connection:
        row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    return row[0] if row else None


def head_revision(script_location: Path) -> str | None:
    config = Config()
    config.set_main_option("script_location", str(script_location))
    return ScriptDirectory.from_config(config).get_current_head()


def schema_snapshot(database_path: Path) -> list[tuple]:
    with sqlite3.connect(database_path) as connection:
        return connection.execute("SELECT type, name, sql FROM sqlite_master ORDER BY name").fetchall()


def upgrade_to(database_path: Path, script_location: Path, revision: str) -> None:
    config = Config()
    config.set_main_option("script_location", str(script_location))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
    command.upgrade(config, revision)


def test_creates_missing_database_at_head_revision(tmp_path):
    database_path = tmp_path / "app.db"

    run_migrations(database_path, script_location=OK_SCRIPTS)

    assert database_path.is_file()
    assert current_revision(database_path) == head_revision(OK_SCRIPTS) == "r2"


def test_second_run_applies_nothing(tmp_path):
    database_path = tmp_path / "app.db"
    run_migrations(database_path, script_location=OK_SCRIPTS)
    revision_before = current_revision(database_path)
    schema_before = schema_snapshot(database_path)

    run_migrations(database_path, script_location=OK_SCRIPTS)

    assert current_revision(database_path) == revision_before
    assert schema_snapshot(database_path) == schema_before


def test_pending_migration_keeps_existing_rows(tmp_path):
    database_path = tmp_path / "app.db"
    upgrade_to(database_path, OK_SCRIPTS, "r1")
    with sqlite3.connect(database_path) as connection:
        connection.executemany("INSERT INTO items (label) VALUES (?)", [("a",), ("b",), ("c",)])
    rows_before = sqlite3.connect(database_path).execute("SELECT id, label FROM items").fetchall()

    run_migrations(database_path, script_location=OK_SCRIPTS)

    assert current_revision(database_path) == "r2"
    with sqlite3.connect(database_path) as connection:
        rows_after = connection.execute("SELECT id, label FROM items").fetchall()
    assert rows_after == rows_before
    assert len(rows_after) == 3


def test_backup_copy_is_named_after_previous_revision(tmp_path):
    database_path = tmp_path / "app.db"
    upgrade_to(database_path, OK_SCRIPTS, "r1")
    content_before = database_path.read_bytes()

    run_migrations(database_path, script_location=OK_SCRIPTS)

    backup = tmp_path / "app.db.bak-r1"
    assert backup.is_file()
    assert backup.read_bytes() == content_before


def test_backup_copy_for_unversioned_database_is_named_base(tmp_path):
    database_path = tmp_path / "app.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE legacy (id INTEGER PRIMARY KEY)")
    content_before = database_path.read_bytes()

    run_migrations(database_path, script_location=OK_SCRIPTS)

    backup = tmp_path / "app.db.bak-base"
    assert backup.is_file()
    assert backup.read_bytes() == content_before


def test_no_backup_copy_when_nothing_is_pending(tmp_path):
    database_path = tmp_path / "app.db"
    run_migrations(database_path, script_location=OK_SCRIPTS)

    run_migrations(database_path, script_location=OK_SCRIPTS)

    assert [path.name for path in tmp_path.iterdir()] == ["app.db"]


def test_no_backup_copy_when_database_is_created(tmp_path):
    database_path = tmp_path / "app.db"

    run_migrations(database_path, script_location=OK_SCRIPTS)

    assert [path.name for path in tmp_path.iterdir()] == ["app.db"]


def test_existing_backup_copy_is_not_overwritten(tmp_path):
    database_path = tmp_path / "app.db"
    upgrade_to(database_path, OK_SCRIPTS, "r1")
    backup = tmp_path / "app.db.bak-r1"
    backup.write_bytes(b"older good copy")

    run_migrations(database_path, script_location=OK_SCRIPTS)

    assert backup.read_bytes() == b"older good copy"
    assert current_revision(database_path) == "r2"


def test_unwritable_backup_copy_aborts_before_any_migration(tmp_path, monkeypatch):
    database_path = tmp_path / "app.db"
    upgrade_to(database_path, OK_SCRIPTS, "r1")

    def failing_copy(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("app.db.migrate.shutil.copy2", failing_copy)

    with pytest.raises(RuntimeError) as exc_info:
        run_migrations(database_path, script_location=OK_SCRIPTS)

    assert str(tmp_path / "app.db.bak-r1") in str(exc_info.value)
    assert current_revision(database_path) == "r1"


def test_failing_migration_raises_diagnosable_error(tmp_path):
    database_path = tmp_path / "app.db"

    with pytest.raises(RuntimeError) as exc_info:
        run_migrations(database_path, script_location=FAILING_SCRIPTS)

    message = str(exc_info.value)
    assert "Database migration failed" in message
    assert str(database_path) in message
    assert "boom from fixture revision r2" in message
    assert isinstance(exc_info.value.__cause__, Exception)
