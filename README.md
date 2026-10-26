# Recipebook

A recipe management app with a FastAPI backend and a Vue 3 frontend.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python dependency management)
- [Node.js](https://nodejs.org/) 18+ with npm
- `make` — on Windows, install via Git Bash/MinGW (not available natively; see [docs/arc42/adoc/11_technical_risks.adoc](docs/arc42/adoc/11_technical_risks.adoc))

## Local Setup

```
git clone <repo-url>
cd recipebook
```

## Running Backend and Frontend

Start both together:

```
make dev
```

Or start them individually:

```
make backend   # equivalent to: cd backend && uv run uvicorn app.main:app --reload
make frontend  # equivalent to: cd frontend && npm run dev
```

The backend runs at `http://localhost:8000` (health check at `/health`), the frontend dev server at `http://localhost:5173`.

### Database migrations

The database schema is versioned with [Alembic](https://alembic.sqlalchemy.org/)
(see [ADR-8](docs/adr/0008-alembic-migrations-at-startup.md)). Pending migrations
run automatically every time the backend starts, so `make backend` always
brings `backend/data/app.db` up to date; there is no separate command.

After changing a model in `backend/app/models/`, create a revision, review the
generated file in `backend/app/db/migrations/versions/` (constraints, defaults,
`ON DELETE` rules), and commit it together with the model change:

```
cd backend && uv run alembic revision --autogenerate -m "describe the change"
```

If a model change has no revision, the test that compares the migrated schema
with the models fails in `make check`.

## Running Tests

```
cd backend && uv run pytest
cd frontend && npm test
```

## Self-Hosted Deployment (Home Network)

Runs the application as a single Docker container: the backend serves the built
frontend and the API from the same port, so no CORS configuration or reverse
proxy is needed (see [ADR-7](docs/adr/0007-single-container-deployment.md)).
Tested with a Raspberry Pi (`linux/arm64`) as the target device; the same
Dockerfile also builds on `linux/amd64` for local verification.

This is scoped to the home network: there is no authentication and no TLS.
Do not expose the published port to the public internet (see issue #5 for
VPS deployment with authentication).

### Prerequisites on the target device

- [Docker Engine](https://docs.docker.com/engine/install/) with the Compose
  plugin (`docker compose version`). `make` is **not** required — deployment
  does not go through the root Makefile.
- A directory for the database file, on **local storage**. SQLite's file
  locking is unreliable on NFS/SMB shares, so do not point the data directory
  at a NAS share mounted into the host filesystem.

### Steps

1. Clone the repository on the target device:

   ```
   git clone <repo-url>
   cd recipebook
   ```

2. Create the data directory and make it writable by the container's user
   (UID/GID `1000:1000` by default — the default account on Raspberry Pi OS):

   ```
   mkdir -p data
   sudo chown -R 1000:1000 data
   ```

   If the device's primary account uses a different UID/GID, set
   `RECIPEBOOK_UID` and `RECIPEBOOK_GID` before the next step instead of
   `1000:1000`, e.g. `export RECIPEBOOK_UID=$(id -u) RECIPEBOOK_GID=$(id -g)`.
   If the container cannot write to `data/`, it fails at startup with an
   error naming the configured database path — that error is the symptom of
   this mismatch.

3. Build and start the container:

   ```
   docker compose up -d --build
   ```

   The image is built directly on the target device from source; nothing is
   pushed to or pulled from a registry.

4. Open the application from any device in the home network at
   `http://<device-ip>:8090`.

### Database migrations on container start

Every container start applies pending database migrations to
`data/app.db` before the application serves requests; nothing has to be run
by hand. A failing migration keeps the container from starting: the process
exits with a non-zero status and the error ("Database migration failed for
...") is in `docker compose logs`.

Before applying pending migrations to an existing database, the application
copies the file to `data/app.db.bak-<revision>`, where `<revision>` is the
schema version the database had before the migration (`base` if it had none,
e.g. `app.db.bak-base` on the first start after this feature was introduced).
Copies are only written when migrations are pending, an existing copy is never
overwritten (the log then says `Database backup skipped` and names the file),
and they are never cleaned up automatically — delete old ones by hand when you
no longer need them. The migration progress and each copy written or skipped
are logged (`docker compose logs`). The `app.db.bak-base` left by the first
start after this feature was introduced is a copy of the empty database from
before it; it can be deleted once you have checked that start in the logs.

On every start, also when nothing was migrated, the application checks the
database for rows that point at rows that no longer exist (`PRAGMA
foreign_key_check`). If it finds any, it does not start and the log says
`Database has foreign key violations: ...` followed by the offending rows. A
migration can cause this, and so can a delete made directly in the database
with the `sqlite3` tool, which does not enforce foreign keys by default. Either
repair the listed rows or restore a copy as described below; the container keeps
failing its start until one of the two is done.

To restore a copy after a failed or unwanted migration:

1. Stop the container (`docker compose down`).
2. Pick the copy named after the revision of the release you go back to. If the
   failed deployment wrote more than one copy, that is the oldest of them (a
   later start may have copied a half-migrated file). The revision of a release
   is the newest file in its `backend/app/db/migrations/versions/`. For a copy,
   this one-liner (the `sqlite3` command-line tool is not installed on the Pi or
   in the image) prints its revision:

   ```
   python3 -c "import sqlite3, sys; print(sqlite3.connect('file:' + sys.argv[1] + '?mode=ro', uri=True).execute('SELECT version_num FROM alembic_version').fetchone())" data/app.db.bak-<revision>
   ```

   A `bak-base` copy was never migrated and has no `alembic_version` table, so
   the command fails with `no such table: alembic_version`; that is the answer
   (`base`).
3. Replace `data/app.db` with that copy, then **rename the copy** with a unique
   suffix, for example `app.db.bak-<revision>.restored-<YYYYMMDD>`. Otherwise
   its name stays taken, the next deployment skips its backup, and the data
   entered in between is not copied before the migration runs again. The date
   keeps a repeated restore from replacing an earlier renamed copy.
4. Check out the previous release and start it again with
   `docker compose up -d --build`.

### What persists, and what doesn't

The `data/` directory is bind-mounted into the container, so the database
survives `docker restart` and `docker compose up -d --build` (rebuilding the
image and recreating the container). It does **not** survive
`docker compose down -v`, deleting the `data/` directory, or storage failure
(e.g. an SD card dying on the Raspberry Pi). Surviving restarts is not a
backup: the only copies the application makes are the migration copies
described above, and they live on the same storage as the database. Back up
`data/` yourself to protect against storage failure.

### Troubleshooting

**Container does not start after a system update (`Unable to enable DNAT rule`).**
If the kernel or Docker was upgraded (e.g. `pacman -Syu` on Arch Linux ARM)
and the device was not rebooted, the kernel modules Docker needs for port
forwarding may no longer be loadable, because the modules of the still-running
kernel have been replaced. Starting the container then fails with
`failed to set up container networking: ... Unable to enable DNAT rule`, and
Docker does not retry it on the next boot. Containers using host networking are
not affected, which makes this easy to miss. Reboot the device right after
kernel or Docker upgrades; if the container is still down after the reboot,
recreate it:

```
docker compose up -d --force-recreate
```

## Documentation

- Contribution workflow: [CONTRIBUTING.md](CONTRIBUTING.md)
- Architecture: [docs/arc42/arc42-template.adoc](docs/arc42/arc42-template.adoc)
- Architecture Decision Records: [docs/adr](docs/adr)
