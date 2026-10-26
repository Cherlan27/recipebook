import logging
import os
import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.db.migrate import run_migrations

FIXTURES = Path(__file__).parent / "fixtures"
OK_SCRIPTS = FIXTURES / "migrations_ok"
FAILING_SCRIPTS = FIXTURES / "migrations_failing"
LOGGER_NAME = "uvicorn.error"


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


class PartialCopy:
    """Stands in for shutil.copy2: writes part of the file, then fails like a full disk."""

    def __call__(self, source, destination, **kwargs):
        data = Path(source).read_bytes()
        Path(destination).write_bytes(data[: len(data) // 2])
        raise OSError("No space left on device")


def test_interrupted_backup_copy_is_not_mistaken_for_a_backup_on_the_next_start(tmp_path, monkeypatch):
    database_path = tmp_path / "app.db"
    upgrade_to(database_path, OK_SCRIPTS, "r1")
    content_before = database_path.read_bytes()
    monkeypatch.setattr("app.db.migrate.shutil.copy2", PartialCopy())

    with pytest.raises(RuntimeError):
        run_migrations(database_path, script_location=OK_SCRIPTS)

    assert sorted(path.name for path in tmp_path.iterdir()) == ["app.db"]
    monkeypatch.undo()

    run_migrations(database_path, script_location=OK_SCRIPTS)

    assert (tmp_path / "app.db.bak-r1").read_bytes() == content_before
    assert current_revision(database_path) == "r2"


def test_leftover_partial_copy_from_a_killed_start_is_overwritten_by_the_next_start(tmp_path):
    database_path = tmp_path / "app.db"
    upgrade_to(database_path, OK_SCRIPTS, "r1")
    content_before = database_path.read_bytes()
    # A kill or power cut during the copy runs no cleanup and leaves the temporary file behind.
    leftover = tmp_path / "app.db.bak-r1.partial"
    leftover.write_bytes(content_before[: len(content_before) // 2] + b"stale")

    run_migrations(database_path, script_location=OK_SCRIPTS)

    assert (tmp_path / "app.db.bak-r1").read_bytes() == content_before
    assert not leftover.exists()
    assert current_revision(database_path) == "r2"


def test_backup_copy_is_flushed_to_disk_before_it_gets_its_final_name(tmp_path, monkeypatch):
    database_path = tmp_path / "app.db"
    upgrade_to(database_path, OK_SCRIPTS, "r1")
    partial = tmp_path / "app.db.bak-r1.partial"
    final = tmp_path / "app.db.bak-r1"
    events: list[tuple[str, bool, bool, bool]] = []
    real_fsync, real_replace = os.fsync, os.replace

    def recording_fsync(fd):
        on_partial = partial.exists() and os.path.samestat(os.fstat(fd), partial.stat())
        events.append(("fsync", on_partial, partial.exists(), final.exists()))
        real_fsync(fd)

    def recording_replace(source, destination):
        events.append(("replace", Path(source) == partial, partial.exists(), final.exists()))
        real_replace(source, destination)

    monkeypatch.setattr("app.db.migrate.os.fsync", recording_fsync)
    monkeypatch.setattr("app.db.migrate.os.replace", recording_replace)

    run_migrations(database_path, script_location=OK_SCRIPTS)

    # (call, concerns the .partial file, .partial exists, final name exists) at call time
    assert events == [("fsync", True, True, False), ("replace", True, True, False)]


def test_migration_progress_and_backup_are_logged(tmp_path, caplog):
    database_path = tmp_path / "app.db"
    upgrade_to(database_path, OK_SCRIPTS, "r1")

    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        run_migrations(database_path, script_location=OK_SCRIPTS)

    messages = [record.getMessage() for record in caplog.records if record.name == LOGGER_NAME]
    assert any("r1" in message and "r2" in message for message in messages)
    assert any("written" in message and str(tmp_path / "app.db.bak-r1") in message for message in messages)


def test_skipped_backup_copy_is_logged_as_warning_naming_the_existing_copy(tmp_path, caplog):
    database_path = tmp_path / "app.db"
    upgrade_to(database_path, OK_SCRIPTS, "r1")
    backup = tmp_path / "app.db.bak-r1"
    backup.write_bytes(b"older good copy")

    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        run_migrations(database_path, script_location=OK_SCRIPTS)

    warnings = [
        record for record in caplog.records if record.name == LOGGER_NAME and record.levelno == logging.WARNING
    ]
    assert len(warnings) == 1
    assert str(backup) in warnings[0].getMessage()


def test_migration_connection_has_foreign_keys_off_even_if_a_global_listener_enables_them(tmp_path):
    def enable_foreign_keys(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    event.listen(Engine, "connect", enable_foreign_keys)
    try:
        database_path = tmp_path / "app.db"
        run_migrations(database_path, script_location=FIXTURES / "migrations_fk_probe")
    finally:
        event.remove(Engine, "connect", enable_foreign_keys)

    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT enabled FROM fk_state").fetchall() == [(0,)]


def test_migration_leaving_orphaned_rows_aborts_startup(tmp_path):
    database_path = tmp_path / "app.db"

    with pytest.raises(RuntimeError) as exc_info:
        run_migrations(database_path, script_location=FIXTURES / "migrations_orphan")

    message = str(exc_info.value)
    assert "Database has foreign key violations" in message
    assert "children" in message


def test_foreign_key_violations_abort_every_start_not_only_the_one_that_migrated(tmp_path):
    database_path = tmp_path / "app.db"
    scripts = FIXTURES / "migrations_orphan"

    with pytest.raises(RuntimeError):
        run_migrations(database_path, script_location=scripts)

    # The database is stamped at head now, but the dangling row is still there.
    with pytest.raises(RuntimeError) as exc_info:
        run_migrations(database_path, script_location=scripts)

    message = str(exc_info.value)
    assert "Database has foreign key violations" in message
    assert "children" in message
    assert str(database_path) in message
    assert "migration failed" not in message


def test_foreign_key_violations_created_outside_the_application_abort_startup(tmp_path):
    database_path = tmp_path / "app.db"
    run_migrations(database_path, script_location=OK_SCRIPTS)
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE parents (id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE children (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parents(id))")
        connection.execute("INSERT INTO children (id, parent_id) VALUES (1, 99)")

    with pytest.raises(RuntimeError) as exc_info:
        run_migrations(database_path, script_location=OK_SCRIPTS)

    assert "Database has foreign key violations" in str(exc_info.value)
