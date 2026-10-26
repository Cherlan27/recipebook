## Context

See `proposal.md` — Why for motivation, and `specs/database-migrations/spec.md` and `specs/recipe-data-model/spec.md` for the behavior this must satisfy.

Current state that shapes the approach:

- `app/db/session.py` creates the async engine (`sqlite+aiosqlite`) at import time from `settings.database_url`. `init_db()` runs in the FastAPI `lifespan`, creates the database directory, and opens one connection so the SQLite driver creates the file. Errors are raised as `RuntimeError` naming the path (deployment spec, *Unusable storage is reported as a diagnosable startup failure*).
- `app/db/base.py` has an empty `DeclarativeBase`; `app/models/` is empty.
- ADR-1 chose async SQLAlchemy and recorded that migrations would need "a sync-driver workaround or an async-capable `env.py`" (also listed in arc42 §11).
- The `Dockerfile` copies only `backend/pyproject.toml`, `backend/uv.lock`, and `backend/app/` into the image, and starts Uvicorn with a plain `CMD` (ADR-7, D8).
- `.gitignore` ignores `backend/data/*.db`, which does not match `app.db.bak-<revision>`.
- On the Pi, `/app/data/app.db` already exists from #2: an empty SQLite file without tables or a version table.
- SQLite does not enforce foreign keys unless `PRAGMA foreign_keys=ON` is set **per connection**. Its built-in `NOCASE` collation and `lower()` only fold ASCII letters.
- Existing tests that use `TestClient(app)` without a `with` block do not run the lifespan, so they do not trigger migrations.

## Goals / Non-Goals

**Goals:**

- One migration mechanism that behaves identically for `make backend`, `uv run pytest`, and the container.
- Integrity rules (unique `nr`, `effort` range, `kid_friendly` values, link cascades) enforced by the database, not only by the ORM.
- Tests exercise the schema produced by the migrations, not a `create_all()` shortcut, so a constraint missing from a migration is caught.

**Non-Goals:**

- Downgrade as an operational path. Each revision keeps Alembic's generated `downgrade()`, but rollback in operation is "restore the backup copy" (see Migration Plan).
- Concurrency control for several processes migrating at once — the deployment runs a single Uvicorn process.
- A get-or-create helper for tags. The data model guarantees uniqueness and keeps the first spelling; resolving `"pasta"` to an existing `"Pasta"` belongs to the API that creates tags (#8/#9).
- Validation of `time_minutes`, `servings`, or `nr` ranges, or of empty `name` strings — not asked for by the issue.

## Decisions

### D1: Alembic as the migration tool

Alembic is SQLAlchemy's own migration tool: it autogenerates revisions from the models, records the current revision in the database (`alembic_version`), and offers *batch mode* to work around SQLite's limited `ALTER TABLE` by recreating tables.

*Alternatives:* hand-written numbered SQL scripts with a homemade version table — reinvents revision tracking and loses autogenerate; `Base.metadata.create_all()` plus manual `ALTER`s — cannot evolve a populated schema safely, which is the problem the issue exists to solve.

### D2: Migrations run in-process from `init_db()`

`init_db()` keeps creating the directory, then runs the migrations instead of merely opening a connection; the migration connection creates the file when it does not exist. Nothing changes in `app/main.py`, the `Dockerfile`, or `docker-compose.yml`.

*Alternatives:* an entrypoint script running `alembic upgrade head && exec uvicorn …` — a second start path that local development would not use, so the two could drift (the issue rules this out); a manual migrate command — easy to forget on the Pi, and the app would then run against an outdated schema.

### D3: Migrations use the synchronous `sqlite3` driver, run in a worker thread

The migration environment (`env.py`) connects with a plain `sqlite:///<path>` URL and runs Alembic's commands synchronously. `init_db()` calls the synchronous migration function via `asyncio.to_thread(...)`, so the running event loop is not blocked and Alembic's own code never sees it. This resolves the open point from ADR-1.

*Alternative:* Alembic's async `env.py` template. It calls `asyncio.run()`, which fails inside the already running `lifespan` event loop; making it work requires nesting loops or a thread anyway. Migrations gain nothing from async I/O at startup.

### D4: Migrations live inside the `app` package; the runtime configures Alembic in code

The migration environment and revisions go to `backend/app/db/migrations/` (`env.py`, `script.py.mako`, `versions/`). Because `app/` is already copied into the image, no `Dockerfile` change is needed and the image cannot silently ship without migrations.

At runtime the migration function builds an Alembic `Config` in code: `script_location` points at the package directory (overridable by a parameter, which the failure test uses), and the database URL is derived from the path it is given — evaluated at call time, not at import, so tests can point it at a temporary file. A `backend/alembic.ini` exists only for the developer CLI (`uv run alembic revision --autogenerate -m "..."`, `uv run alembic upgrade head`) and sets `script_location = %(here)s/app/db/migrations`; when no URL is set in the config, `env.py` falls back to `settings.database_path`. `env.py` applies `logging.config.fileConfig` only when Alembic was started from an ini file, so running migrations inside Uvicorn does not replace Uvicorn's logging configuration.

*Alternative:* the conventional `backend/alembic.ini` + `backend/migrations/` layout used by both CLI and runtime. Rejected because the image would then need two more `COPY` lines, and forgetting them only shows up as a failed start on the Pi.

### D5: Pending detection and backup copy before upgrading

The migration function, in order:

1. Records whether the database file exists **before** any connection is opened. If it does not, the database is "created on this start" and no backup is made.
2. Opens a sync connection, reads the current revision (`MigrationContext.get_current_revision()`, `None` → `base`) and compares it with the head of the script directory. The connection is closed before the copy.
3. If the file existed and the current revision is not the head: copies the file to `<name>.bak-<current revision>` in the same directory — unless a file of that name already exists, in which case it logs a warning naming that copy and moves on. The copy goes to `<name>.bak-<revision>.partial` first, is flushed with `fsync`, and is then renamed with `os.replace`; the temporary file is deleted on failure. Only a complete copy therefore ever has the final name, so an interrupted copy (full SD card, power loss) is not mistaken for a backup by the automatic restart (`restart: unless-stopped`). A failed copy raises a `RuntimeError` naming the backup path; no migration runs.
4. Runs `command.upgrade(config, "head")`, then `PRAGMA foreign_key_check` (see D7).

The steps log through the `uvicorn.error` logger — Uvicorn configures only its own loggers, so a module logger without a handler, or Alembic's own INFO lines, would never reach `docker compose logs`: the revision change (`current -> head`), a backup written (path), and a backup skipped (path, WARNING).

The revision in the file name is the one the database was **at**, i.e. the schema the copy contains, so it tells which release can open it. Not overwriting an existing copy matters on SQLite: Alembic's SQLite DDL is not transactional, so a failed upgrade can leave the database partially migrated at the *same* recorded revision. The next start would then copy the half-migrated file over the good backup. Keeping the first copy keeps the last good state.

The rule has a consequence for the restore procedure: after a copy-based restore the old `app.db.bak-<revision>` still exists, so a later deployment of the fixed release would skip its backup and migrate data that was entered in between without a current copy. The restore instructions (README, ADR-8, arc42 §11) therefore tell the operator to rename the used copy (e.g. to `app.db.bak-<revision>.restored`) so the name is free again, and to restore the copy named after the revision of the release being returned to — the oldest copy the failed deployment wrote, since a restart after a partial failure can write a second copy from a half-migrated file. The warning logged when a backup is skipped is the second line of defence if the procedure is not followed.

The first start on the Pi after this change finds the existing empty `app.db` without a version table and produces `app.db.bak-base` — harmless, and it gives the Pi deployment check something concrete to verify.

*Alternatives:* SQLite's online backup API (`sqlite3.Connection.backup`) — consistent even with a hot journal, but not byte-identical and not needed while nothing else holds a connection during startup (single process, rollback journal); revisit if WAL mode is ever enabled. Copying on every start — fills the volume with identical copies for no gain.

### D6: Every migration failure aborts startup with a diagnosable error

Any exception from steps 2–4 is re-raised as `RuntimeError(f"Database migration failed for {path}: {exc}")` with the original exception chained. The database path stays in the message so the existing deployment requirement (error names the configured path, e.g. a directory that exists but is not writable) still holds after the connection step moved into the migration. The exception propagates out of `lifespan`; Uvicorn logs it and exits non-zero, and `TestClient(create_app())` used as a context manager raises it, which is how the test drives it.

### D7: Foreign keys enforced on application connections only

A `connect` event listener on the application's engine (`engine.sync_engine`) executes `PRAGMA foreign_keys=ON` for every new connection, so `ON DELETE CASCADE` on `recipe_tags` works for ORM deletes and direct SQL deletes alike. The ORM relationship uses `passive_deletes=True` to leave link removal to the database.

The **migration** connection deliberately has foreign-key enforcement off, and `env.py` sets `PRAGMA foreign_keys=OFF` explicitly instead of relying on SQLite's compile-time default, so a future global `Engine` `connect` listener or a differently built SQLite cannot switch it on unnoticed (a test registers such a listener and asserts the migration sees `0`). Batch mode migrates a table by creating a copy, moving rows, dropping the original, and renaming; with enforcement on, dropping `recipes` would cascade-delete every row in `recipe_tags` — silent data loss in exactly the scenario *pending migrations and existing data*. This is documented in `env.py`. Because enforcement is off, a faulty migration could leave dangling `recipe_tags` rows that no later application connection would ever check; after the upgrade `run_migrations()` therefore runs `PRAGMA foreign_key_check` and aborts startup with a `RuntimeError` naming the offending table if it returns rows.

Not yet handled: changing only a recipe's tags writes `recipe_tags` and leaves `recipes.updated_at` untouched (`onupdate` fires only when a column of `recipes` changes). The recipe API in #9 must update `updated_at` itself when it edits a recipe's tags (review R6, deferred).

### D8: Case-insensitive tag uniqueness via a normalized key column

`tags` has `name` (NFC-normalized and stripped, first spelling, displayed) and `name_key` (the same normalized name, `.casefold()`ed, `UNIQUE`, `NOT NULL`). The model computes both from the given name in one place (a `@validates("name")` hook or equivalent) and raises `ValueError` for a name that is empty after stripping; a `CHECK (name_key <> '')` backs this up in the database. A differently cased duplicate violates the unique constraint on `name_key`, so the insert fails with `IntegrityError` and the first spelling stays.

Names are normalized to Unicode **NFC** (`unicodedata.normalize`) before stripping and case folding, because macOS input and copy-paste from PDFs or web pages produce decomposed umlauts (`O` + U+0308) that look identical to the composed `Ö`; without it both would be stored as separate tags. `casefold()` (not `lower()`) is kept **on purpose**: it maps `ß` to `ss`, so `Maße` and `Masse` are the same tag. For German recipe tags that is wanted — a household typing either spelling means the same thing — and it is cheaper to decide now than to merge duplicates later, since changing the key afterwards needs a data migration.

*Alternatives:* `name TEXT COLLATE NOCASE UNIQUE` or a unique index on `lower(name)` — both fold only ASCII in SQLite, so `"Österreichisch"` and `"österreichisch"` would both be accepted, which matters for German tags; the ICU extension — not available in the stock `sqlite3` module.

### D9: Column types and constraints

- **Naming convention.** `Base.metadata` gets an explicit `naming_convention` (`ix`, `uq`, `ck`, `fk`, `pk`). SQLite constraints are otherwise unnamed, and batch mode cannot reliably drop or alter an unnamed constraint later.
- **`recipes`**: `id` integer primary key; `nr` `Integer NOT NULL UNIQUE`; `name` `Text NOT NULL`; `effort` `Integer` with `CHECK (effort BETWEEN 1 AND 3)` (NULL passes a CHECK in SQL, so "optional" needs no extra clause); `time_minutes`, `servings` `Integer`; `kid_friendly` stored as text with a CHECK limited to `yes`, `with_adjustments`, `no` — modelled as a Python `StrEnum` mapped with SQLAlchemy `Enum(..., native_enum=False, create_constraint=True, values_callable=...)` so the database stores the lowercase *values*, not the member names; `ingredients`, `steps` `Text` (lines separated by `\n`, no further structure); `created_at`, `updated_at` `DateTime NOT NULL`.
- **`recipe_tags`**: `recipe_id`, `tag_id`, composite primary key (which also prevents attaching the same tag twice), both foreign keys `ON DELETE CASCADE`.
- **Models**: `app/models/recipe.py` (`Recipe`, `KidFriendly`, the `recipe_tags` table) and `app/models/tag.py` (`Tag`); `app/models/__init__.py` imports them so `Base.metadata` is complete wherever it is used (`env.py`, tests).

### D10: Timestamps are set by the application in UTC, with a database default as fallback

`created_at` and `updated_at` use a Python-side `default` of `datetime.now(UTC)` and `updated_at` an `onupdate` of the same, so ORM and Core writes through the application maintain them with sub-second precision (the "updated_at is later" test needs no sleep). Both also get `server_default=CURRENT_TIMESTAMP`, so rows inserted by a future data migration or by direct SQL are not rejected by `NOT NULL`. SQLite has no time-zone type; values are stored and read as naive UTC, documented on the model. Direct SQL updates do not touch `updated_at` — the spec scopes automatic updates to changes made through the application.

### D11: Tests run against migrated temporary databases

A `conftest.py` fixture creates a temporary database path, runs the real migration function on it, and yields an `AsyncSession` from an engine created the same way as the application's (including the foreign-key listener). Model tests therefore assert against the constraints the migration actually created. Constraint tests that must bypass the ORM (`effort`, `kid_friendly`, duplicate link, direct recipe delete) use `session.execute(text(...))`.

Further tests:

- **Drift**: after migrating an empty database, `alembic.autogenerate.compare_metadata(MigrationContext, Base.metadata)` returns no differences — catches a model change without a migration.
- **No-op**: running the migration function twice leaves the revision and `sqlite_master` unchanged and creates no backup.
- **Data preservation**: with only one revision there is no "previous schema" yet, so preservation is tested twice: (a) an unversioned database file containing an unrelated table with rows keeps those rows after the upgrade; (b) a database at head with recipes and tags keeps them across another start. Future revisions add a test that upgrades from the previous revision with data in place.
- **Failure**: a fixture script directory with a revision whose `upgrade()` raises a distinctive error; `with TestClient(create_app())` is expected to raise `RuntimeError` containing "Database migration failed" and that cause.

## Risks / Trade-offs

- [SQLite DDL is not transactional in Alembic; a failed migration can leave a half-migrated file] → The pre-migration copy is the recovery path, and it is never overwritten (D5). The restore procedure is in the README.
- [Batch-mode migrations combined with foreign-key enforcement would cascade-delete link rows] → Enforcement is explicitly off on the migration connection and checked afterwards with `foreign_key_check` (D7); the data-preservation test pattern guards future revisions.
- [Backup copies accumulate in the volume without cleanup] → Accepted for now (out of scope per the issue). One copy per migrated release is small for a recipe database; the README says so and how to delete old copies.
- [`shutil.copy2` is not consistent if another process writes the file during startup, or if WAL mode is enabled later] → Today there is a single process and the rollback journal; D5 records the online-backup API as the switch if that changes.
- [Startup time grows with migrations] → Negligible at this data size; the Docker health check already has a start period.
- [A developer edits a model without generating a revision] → The drift test fails in `make check`.
- [Two processes start at once and both migrate] → Not possible in the current single-process deployment; would need a lock or a separate migration step if workers are ever added.

## Migration Plan

1. Merge and deploy as usual (`git pull && docker compose up -d --build` on the Pi, Gate 3).
2. On first start the container finds the empty `app.db`, writes `data/app.db.bak-base`, and upgrades to the first revision; `/health` answers `200 OK`.
3. **Rollback** if a later migration fails: stop the container, replace `data/app.db` with the copy named after the revision of the release you go back to (the oldest copy the failed deployment wrote), **rename that copy** (e.g. `app.db.bak-<revision>.restored`) so the next deployment can write a fresh one, check out the previous release, and start it again. Alembic downgrades are not used operationally.
4. Once the first start has been checked in the logs, `data/app.db.bak-base` (a copy of the empty database from #2) can be deleted.
