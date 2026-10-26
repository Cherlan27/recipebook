## 1. Architecture decision and documentation

- [x] 1.1 Write `docs/adr/0008-alembic-migrations-at-startup.md` (Status / Context / Decision / Consequences) with status "Accepted", covering Alembic (D1), in-process migrations at startup (D2), the sync driver in a worker thread (D3), migrations inside the `app` package (D4), the pre-migration backup copy (D5), and failure handling (D6)
- [x] 1.2 Update `docs/arc42/adoc/04_solution_strategy.adoc` (backend strategy: schema managed by migrations at startup) and `docs/arc42/adoc/09_architecture_decisions.adoc` (ADR-8 entry; ADR-1 consequence points to ADR-8)
- [x] 1.3 Update `docs/arc42/adoc/05_building_block_view.adoc`: `app/models` and `app/db/migrations` in the backend white box, new data model section (`recipes`, `tags`, `recipe_tags`), remove the "migration strategy not yet decided" open issue
- [x] 1.4 Add a "Persistence and schema migrations" concept to `docs/arc42/adoc/08_concepts.adoc` (startup migrations, backup copy, foreign-key enforcement, constraint naming, tag normalization) and a startup runtime scenario to `docs/arc42/adoc/06_runtime_view.adoc`
- [x] 1.5 Update `docs/arc42/adoc/07_deployment_view.adoc` (backup copies in the bind mount) and `docs/arc42/adoc/11_technical_risks.adoc` (replace the async-migrations risk; add non-transactional SQLite DDL, foreign keys during batch migrations, accumulating backups; adjust "No backup of deployment data"); add Alembic, migration/revision, and backup copy to `docs/arc42/adoc/12_glossary.adoc`

## 2. Migration runner with backup copy

Mechanics are tested against small fixture script directories under `backend/tests/fixtures/` (e.g. revision 1 creates a table, revision 2 adds a column), independent of the real schema.

- [x] 2.1 Add the runtime dependency with `uv add alembic`; add `backend/data/*.db.bak-*` to `.gitignore`
- [x] 2.2 RED: test for scenario *Application starts without a database file* — running the migration function on a non-existent temporary path creates the file and records the fixture head revision
- [x] 2.3 GREEN: create `app/db/migrate.py` with a synchronous `run_migrations(database_path, script_location=...)` that builds the Alembic `Config` in code and upgrades to head over a `sqlite:///` URL (D3, D4); create the migration environment in `app/db/migrations/` (`env.py` reading the URL from the config with a fallback to `settings.database_path`, `fileConfig` only when started from an ini file, no foreign-key enforcement on the migration connection with a comment explaining why — D7; `script.py.mako`; empty `versions/`) and `backend/alembic.ini` for the developer CLI
- [x] 2.4 RED then GREEN: test for scenario *Application starts against an up-to-date database* — a second run applies nothing and leaves the revision and `sqlite_master` unchanged
- [x] 2.5 RED then GREEN: test for scenario *Application starts against a database with pending migrations and existing data* — a database at fixture revision 1 with rows is upgraded to head and all rows are unchanged
- [x] 2.6 RED: tests for scenarios *Existing database with pending migrations* (copy `<name>.bak-<revision>` next to the database, byte-identical to the file before the run) and *Existing database without a recorded schema version* (`<name>.bak-base`)
- [x] 2.7 GREEN: record file existence before connecting, compare current revision with head, copy with `shutil.copy2` before upgrading (D5)
- [x] 2.8 RED then GREEN: tests for scenarios *Nothing is pending* and *Database is created on this start* — no backup file appears
- [x] 2.9 RED then GREEN: test for scenario *A backup copy with the same name already exists* — the existing copy keeps its content
- [x] 2.10 RED then GREEN: test for scenario *Backup copy cannot be written* (e.g. `shutil.copy2` patched to raise `OSError`) — `RuntimeError` names the backup path and the revision is unchanged
- [x] 2.11 RED then GREEN: test for scenario *Migration raises an error* at the function level — a fixture revision whose `upgrade()` raises a distinctive message yields `RuntimeError` containing "Database migration failed", the database path, and that message, with the cause chained (D6)
- [x] 2.12 REFACTOR: tidy `app/db/migrate.py` and the tests while `uv run pytest` stays green

## 3. Migrations at application start

- [ ] 3.1 RED: test for scenario *Migration raises an error* at the application level — with `settings.database_path` pointing at a temporary file and the script location pointing at the failing fixture, `with TestClient(create_app())` raises an error containing "Database migration failed" and the cause
- [ ] 3.2 GREEN: `init_db()` keeps creating the directory, then calls `run_migrations` via `asyncio.to_thread` instead of opening a bare connection (D2, D3)
- [ ] 3.3 Confirm the existing tests in `tests/test_db_session.py` (missing directory is created; unusable path is named in the error) and the other test modules still pass unchanged; adjust only if the directory test now needs a migrated database
- [ ] 3.4 REFACTOR: remove code in `app/db/session.py` made dead by 3.2, keeping `uv run pytest` green

## 4. Recipe data model and first revision

Model tests use a `conftest.py` fixture that runs the real migrations on a temporary database and yields an `AsyncSession` from an engine with the foreign-key listener (D11). Constraint tests that must bypass the ORM use `text(...)`.

- [ ] 4.1 Add the constraint `naming_convention` to `Base.metadata` in `app/db/base.py` (D9)
- [ ] 4.2 RED: test for scenario *Several recipes with tags are stored and read back* — at least three recipes with all fields, multi-line `ingredients`/`steps`, and tags
- [ ] 4.3 GREEN: add `Recipe`, `KidFriendly`, and `recipe_tags` in `app/models/recipe.py` and `Tag` in `app/models/tag.py` with the columns and constraints from D8–D10; import them in `app/models/__init__.py` and in `env.py`; generate the first revision with `uv run alembic revision --autogenerate -m "create recipes and tags"`, review it (CHECK constraints, `ON DELETE CASCADE`, composite primary key, server defaults), and add the conftest fixture
- [ ] 4.4 RED then GREEN: test for scenario *Migrated database matches the application's data model* — `compare_metadata` against an empty migrated database reports no differences
- [ ] 4.5 RED then GREEN: tests for scenarios *Recipe with only the required fields*, *Recipe without a number*, and *Recipe without a name*
- [ ] 4.6 RED then GREEN: test for scenario *Duplicate recipe number* (direct insert rejected, existing recipe unchanged)
- [ ] 4.7 RED then GREEN: tests for scenarios *Effort within range* and *Effort out of range* (0 and 4 via direct SQL)
- [ ] 4.8 RED then GREEN: tests for scenarios *Defined value* and *Undefined value* for `kid_friendly` (`maybe` via direct SQL; stored values are the lowercase enum values)
- [ ] 4.9 RED then GREEN: tests for scenarios *Recipe is created* and *Recipe is changed* (timestamps set, `updated_at` advances, `created_at` unchanged)
- [ ] 4.10 RED then GREEN: tests for scenarios *Tag name with surrounding whitespace*, *Same name in different case*, *Same name in different case with umlauts*, and *Empty tag name* (`name_key` via `casefold()`, `ValueError` for empty names — D8)
- [ ] 4.11 RED then GREEN: tests for scenarios *One tag on several recipes* and *Same tag attached twice to one recipe* (direct insert of a duplicate link rejected)
- [ ] 4.12 RED: tests for scenarios *Recipe is deleted*, *Recipe is deleted directly in the database*, and *Tag is deleted*
- [ ] 4.13 GREEN: enable `PRAGMA foreign_keys=ON` through a `connect` listener on the application engine in `app/db/session.py`, shared with the test fixture; `passive_deletes=True` on the relationship (D7)
- [ ] 4.14 RED then GREEN: test for scenario *Restart of an up-to-date database with stored recipes* — recipes, tags, and links are unchanged after running the migrations again
- [ ] 4.15 RED then GREEN: test for scenario *Application starts against a database with pending migrations and existing data* against the real revisions — an unversioned database file with an unrelated table and rows keeps those rows, reaches head, and leaves `<name>.bak-base`
- [ ] 4.16 REFACTOR: tidy models, fixture, and tests while `uv run pytest` stays green

## 5. Developer and deployment documentation

- [ ] 5.1 README, local development: migrations run automatically on `make backend`; how to create a revision (`cd backend && uv run alembic revision --autogenerate -m "..."`, review the generated file, commit it) and that the drift test fails when a model change has no revision
- [ ] 5.2 README, deployment: migrations run automatically on every container start; a failing migration keeps the container from starting (see `docker compose logs`); backup copies `app.db.bak-<revision>` are written to the mounted `data/` directory only when migrations are pending, are never cleaned up automatically, and how to restore one (stop, replace `app.db`, start the previous release); adjust "What persists" so it no longer says there is no backup mechanism at all
- [ ] 5.3 Update `CLAUDE.md` architecture notes for `app/db/session.py`, `app/db/migrate.py`, `app/db/migrations/`, and `app/models/`

## 6. Verification

- [ ] 6.1 Run `make check` and confirm it passes (backend tests, frontend tests, type-checked build, `openspec validate --all --strict`)
- [ ] 6.2 Run `make backend` against a fresh worktree database: the app starts, `backend/data/app.db` is created at head, no backup file appears; restart and confirm still no backup file
- [ ] 6.3 Build and run the container locally against a `data/` directory containing an empty `app.db` (the state on the Pi): `docker compose up -d --build`, confirm `data/app.db.bak-base` exists, the container is healthy, and `/health` answers `200 OK`; recreate the container and confirm no further backup appears
> **Gate 3 note (post-merge, done by a human, not an apply task):** deploy on the Raspberry Pi with `git pull && docker compose up -d --build` and verify scenario *Container starts on the Raspberry Pi with the database from the previous release* — no migration error in `docker compose logs`, `data/app.db.bak-base` in the volume, `/health` → `200 OK`; then tick the acceptance criteria and Definition of Done on issue #3
