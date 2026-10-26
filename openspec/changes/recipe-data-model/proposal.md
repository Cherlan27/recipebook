## Why

Nearly every upcoming feature (image upload #4, recipe CRUD and filtering #8, #9, #10) needs a shared data model for recipes and their tags, and there is none yet: `app/models/` is empty. Since #2, the deployed SQLite file lives in a persistent volume on the Raspberry Pi, so "change the schema by deleting the database" stops being an option the moment the first real recipe is entered. The schema therefore has to be managed by versioned migrations from its very first table, before real data exists. Closes #3.

## What Changes

- Introduce **Alembic** as the schema migration tool. Migrations are versioned in the repository; the first migration creates the recipe data model. Tables are no longer created implicitly.
- **Pending migrations run automatically at application start**, where `init_db()` opens the database today — identically for `make backend` and in the container, without an entrypoint script. A failing migration prevents startup and the error names the cause.
- **A copy of the existing database file is made before pending migrations run** (`app.db.bak-<revision>` next to the database, i.e. inside the mounted volume on the Pi). No copy is made when nothing is pending or when the database is being created for the first time.
- New table **`recipes`**: `nr` (integer, unique, required), `name` (text, required), `effort` (integer 1–3, enforced by a CHECK constraint), `time_minutes`, `servings` (integers), `kid_friendly` (`yes` / `with_adjustments` / `no`), `ingredients` and `steps` (free text, one line per entry), `created_at` / `updated_at` (set automatically). Only `nr` and `name` are required, so incomplete paper recipes can be captured.
- New table **`tags`**: free-form (no fixed enum), unique case-insensitively, surrounding whitespace trimmed, the spelling of the first creation is stored.
- New n:m link table **`recipe_tags`**: deleting a recipe removes its links; the tags themselves remain.
- New ADR for the migration strategy; arc42 (building block view, concepts, decisions, risks) and README updated: migrations run on container start, where backup copies live.

Out of scope: an image reference on recipes (#4 adds it itself), API endpoints and UI (#8, #9, #10), structured ingredients with quantities, cleanup of old backup copies.

## Capabilities

### New Capabilities
- `database-migrations`: how the database schema is versioned and brought up to date at application start, including the pre-migration backup copy and the behavior when a migration fails.
- `recipe-data-model`: the persisted structure of recipes, tags, and their n:m relation, including the integrity rules the database itself enforces.

### Modified Capabilities
None. The existing `deployment` requirement that unusable storage is reported as a diagnosable startup failure stays valid unchanged; migration failures are specified in `database-migrations`.

## Impact

- **Dependencies**: new backend runtime dependency `alembic` (added with `uv add`).
- **Code**: new `app/models/` modules (recipe, tag, link table); new `app/db/migrate.py` (pending detection, backup copy, upgrade); new migration environment and first revision under `app/db/migrations/`; `app/db/session.py` (`init_db()` runs migrations and makes the backup; SQLite foreign-key enforcement enabled on every connection); `app/main.py` lifespan unchanged in shape. A `backend/alembic.ini` for the developer CLI (`uv run alembic revision --autogenerate`).
- **Deployment**: the container runs migrations on every start; the first start after this change migrates the existing (empty) `app.db` on the Pi and leaves `app.db.bak-base` next to it in the volume (a copy of the empty database; it can be deleted once that start has been checked in the logs). No `Dockerfile` or `docker-compose.yml` change is expected because migrations live inside the copied `app/` package.
- **Docs**: new ADR `docs/adr/0008-alembic-migrations-at-startup.md`; `docs/arc42/adoc/04`–`09`, `11`, `12`; `README.md`; `CLAUDE.md` architecture notes; `.gitignore` gains the backup file pattern.
- **Blocks**: #4, #8, #9, #10 build on this model.
