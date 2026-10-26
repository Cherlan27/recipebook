import logging
import os
import shutil
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import URL, create_engine

from app.core.config import settings

DEFAULT_SCRIPT_LOCATION = Path(__file__).resolve().parent / "migrations"

# Uvicorn configures only its own loggers, so this is one that reaches `docker compose logs`.
logger = logging.getLogger("uvicorn.error")


class BackupError(RuntimeError):
    """The pre-migration backup copy could not be written."""


def build_config(database_path: Path, script_location: Path) -> Config:
    config = Config()
    config.set_main_option("script_location", str(script_location))
    url = URL.create("sqlite", database=str(database_path)).render_as_string(hide_password=False)
    # Config values go through ini interpolation, where "%" is special.
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def current_revision(database_path: Path) -> str | None:
    engine = create_engine(URL.create("sqlite", database=str(database_path)))
    try:
        with engine.connect() as connection:
            return MigrationContext.configure(connection).get_current_revision()
    finally:
        engine.dispose()


def run_migrations(
    database_path: Path | None = None,
    script_location: Path | None = None,
) -> None:
    """Upgrade the database to the latest revision (synchronous; see ADR-8).

    An existing database with pending migrations is copied to
    ``<name>.bak-<revision>`` first, unless that copy already exists. Afterwards the
    database must have no foreign-key violations.
    """
    database_path = database_path or settings.database_path
    config = build_config(database_path, script_location or DEFAULT_SCRIPT_LOCATION)

    # Must be decided before any connection is opened: connecting creates the file.
    existed = database_path.exists()

    try:
        head = ScriptDirectory.from_config(config).get_current_head()
        current = current_revision(database_path)
        if current == head:
            logger.info("Database %s is up to date at revision %s", database_path, head)
        else:
            logger.info(
                "Migrating database %s from revision %s to %s", database_path, current or "base", head
            )
            if existed:
                backup_before_upgrade(database_path, current)
            command.upgrade(config, "head")
            check_foreign_keys(database_path)
    except BackupError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Database migration failed for {database_path}: {exc}") from exc


def check_foreign_keys(database_path: Path) -> None:
    """Migrations run with enforcement off, so look for rows they left pointing nowhere."""
    engine = create_engine(URL.create("sqlite", database=str(database_path)))
    try:
        with engine.connect() as connection:
            violations = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
    finally:
        engine.dispose()
    if violations:
        details = ", ".join(f"{table} rowid {rowid} -> {parent}" for table, rowid, parent, _ in violations)
        raise RuntimeError(f"Migrations left foreign key violations: {details}")


def backup_before_upgrade(database_path: Path, revision: str | None) -> None:
    backup_path = database_path.with_name(f"{database_path.name}.bak-{revision or 'base'}")
    # Keep the first copy: a failed upgrade can leave a half-migrated file at the same
    # revision (SQLite DDL is not transactional), which must not replace the good copy.
    if backup_path.exists():
        logger.warning(
            "Database backup skipped: %s already exists and is kept; "
            "rename it after a restore so the next migration gets a fresh copy",
            backup_path,
        )
        return
    # Copy under a temporary name so that only a complete copy ever has the final name:
    # a copy cut short by a full disk or a kill must not look like a backup on the next start.
    partial_path = backup_path.with_name(backup_path.name + ".partial")
    try:
        try:
            shutil.copy2(database_path, partial_path)
            with partial_path.open("r+b") as copy:
                os.fsync(copy.fileno())
            os.replace(partial_path, backup_path)
        except BaseException:
            partial_path.unlink(missing_ok=True)
            raise
    except OSError as exc:
        raise BackupError(f"Cannot write database backup copy {backup_path}: {exc}") from exc
    logger.info("Database backup written: %s", backup_path)
