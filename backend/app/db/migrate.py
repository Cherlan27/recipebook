import shutil
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import URL, create_engine

from app.core.config import settings

DEFAULT_SCRIPT_LOCATION = Path(__file__).resolve().parent / "migrations"


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
    script_location: Path = DEFAULT_SCRIPT_LOCATION,
) -> None:
    """Upgrade the database to the latest revision (synchronous; see ADR-8).

    An existing database with pending migrations is copied to
    ``<name>.bak-<revision>`` first, unless that copy already exists.
    """
    database_path = database_path or settings.database_path
    config = build_config(database_path, script_location)

    # Must be decided before any connection is opened: connecting creates the file.
    existed = database_path.exists()

    try:
        head = ScriptDirectory.from_config(config).get_current_head()
        current = current_revision(database_path)
        if existed and current != head:
            backup_before_upgrade(database_path, current)
        command.upgrade(config, "head")
    except BackupError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Database migration failed for {database_path}: {exc}") from exc



def backup_before_upgrade(database_path: Path, revision: str | None) -> None:
    backup_path = database_path.with_name(f"{database_path.name}.bak-{revision or 'base'}")
    # Keep the first copy: a failed upgrade can leave a half-migrated file at the same
    # revision (SQLite DDL is not transactional), which must not replace the good copy.
    if backup_path.exists():
        return
    try:
        shutil.copy2(database_path, backup_path)
    except OSError as exc:
        raise BackupError(f"Cannot write database backup copy {backup_path}: {exc}") from exc
