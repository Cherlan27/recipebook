from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

import app.models  # noqa: F401  (registers the models on Base.metadata)
from app.core.config import settings
from app.db.base import Base

config = context.config

# Only when started from alembic.ini (developer CLI). Applying it inside Uvicorn
# would replace Uvicorn's logging configuration.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def run_migrations_online() -> None:
    url = config.get_main_option("sqlalchemy.url") or f"sqlite:///{settings.database_path}"
    # Foreign-key enforcement stays off (SQLite's default) on this connection on purpose:
    # batch migrations drop and recreate tables, and with enforcement on, dropping
    # `recipes` would cascade-delete every row in `recipe_tags`. See design D7.
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations_online()
