# 8. Alembic migrations applied at application start, with a backup copy

Date: 2026-10-26

## Status

Accepted

## Context

Issue #3 introduces the first domain model (recipes, tags, and their n:m link). Since #2 (ADR-7), the deployed SQLite file lives in a bind-mounted directory on the Raspberry Pi and survives restarts and rebuilds. From the first real recipe on, a schema change can no longer be made by deleting the database and recreating its tables with `create_all()`: every change has to evolve a database that contains data.

Three constraints shape the decision:

- The backend uses async SQLAlchemy with `aiosqlite` (ADR-1). ADR-1 already noted that migrations would need "a sync-driver workaround or an async-capable `env.py`".
- The container starts Uvicorn with a plain `CMD` and copies only `backend/app/` (plus the lock files) into the image (ADR-7). There is no entrypoint script.
- The Pi has no backup of the database at all, and SQLite's `ALTER TABLE` support is limited, so non-trivial migrations recreate tables — a failed migration can leave a half-migrated file.

## Decision

Manage the schema with **Alembic** and apply pending migrations **automatically at application start**, before any request is served.

- **Where they run.** `init_db()`, already called from the FastAPI `lifespan`, creates the database directory and then runs the migrations. Local development (`make backend`), tests, and the container all use this one path; there is no entrypoint script and no manual migrate command.
- **How they run.** Migrations use the synchronous `sqlite3` driver and are executed in a worker thread (`asyncio.to_thread`). Alembic's async `env.py` template calls `asyncio.run()`, which cannot run inside the already running `lifespan` event loop, and migrations gain nothing from async I/O.
- **Where they live.** The migration environment and revisions live inside the application package (`backend/app/db/migrations/`), so the existing `Dockerfile` copies them without change. The runtime configures Alembic in code; `backend/alembic.ini` exists only for the developer CLI (`uv run alembic revision --autogenerate`).
- **Backup copy.** If the database file already existed before this start and has pending migrations, it is copied to `<name>.bak-<revision>` in the same directory before any migration runs — on the Pi that is the mounted data directory. `<revision>` is the schema version the copy contains (`base` for a database that was never migrated). No copy is made when nothing is pending or when the database is created on this start. An existing copy of the same name is never overwritten, so a failed, partially applied migration cannot replace the last good copy on the next start; the skip is logged as a warning naming the copy. The copy is written under a temporary name, flushed to disk, and only then renamed, so an interrupted copy (full disk, power loss) never occupies the final name.
- **Failure.** If the backup cannot be written or a migration fails, startup aborts with an error that states that a database migration failed, names the database (or backup) path, and includes the underlying cause. Uvicorn then exits with a non-zero status, and the container does not become healthy.
- **Foreign keys during migrations.** The application enables SQLite foreign-key enforcement on its own connections; the migration connection switches it off explicitly, because recreating a table in batch mode would otherwise cascade-delete its link rows. On every start, also when nothing was migrated, `PRAGMA foreign_key_check` must return no rows, otherwise startup fails with a neutral "Database has foreign key violations" error that names the rows and the next step (restore a backup copy or repair the rows). Running it on every start keeps the automatic restart (`restart: unless-stopped`) from bringing the instance up after a refused start, and it also catches rows orphaned by edits outside the application.
- **Logging.** The current and target revision and every backup written or skipped are logged through the `uvicorn.error` logger, because Uvicorn configures only its own loggers and the container log would otherwise show nothing about a successful migration.

## Consequences

- Schema changes become reviewable, versioned files in the repository. A model change without a revision is caught by a test that compares the migrated schema with the models.
- Deploying stays `git pull && docker compose up -d --build`; the first start after #3 migrates the existing empty `app.db` on the Pi and leaves `app.db.bak-base` next to it; that copy of the empty database can be deleted once the start has been checked.
- A broken migration makes the instance unavailable instead of running against an outdated schema. Recovery is to restore the copy named after the revision of the release being returned to (the oldest copy the failed deployment wrote), **rename that copy** afterwards (to `app.db.bak-<revision>.restored-<YYYYMMDD>`, so a repeated restore cannot replace an earlier renamed copy) so its name is free for the next deployment's backup, and start the previous release; Alembic downgrades are not part of the operational path.
- Backup copies accumulate in the data directory, one per migrated release. Cleaning them up is deliberately out of scope for now.
- The pre-migration copy is a safety net for migrations, not a general backup: it does not protect against storage failure or volume removal (see arc42 §11).
- The backup is a plain file copy. That is consistent only while no other process writes the database during startup and the rollback journal is used; enabling WAL mode or running several processes would require SQLite's online backup API instead.
- Migrations run on every start, also under `uvicorn --reload`. With a single process this is harmless; running several workers would need a lock or a separate migration step.
- Alternatives rejected: an **entrypoint script** running `alembic upgrade head` before Uvicorn (a second start path that local development would not share, so the two could drift); a **manual migrate command** (easy to forget on the Pi, leaving the app on an outdated schema); **`create_all()` plus hand-written `ALTER`s** (cannot safely evolve a populated schema); **migrations outside the `app` package** (the image would need extra `COPY` lines whose omission only shows as a failed start on the Pi).
