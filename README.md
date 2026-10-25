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

### What persists, and what doesn't

The `data/` directory is bind-mounted into the container, so the database
survives `docker restart` and `docker compose up -d --build` (rebuilding the
image and recreating the container). It does **not** survive
`docker compose down -v`, deleting the `data/` directory, or storage failure
(e.g. an SD card dying on the Raspberry Pi). Surviving restarts is not a
backup — there is currently no backup mechanism for this data.

## Documentation

- Architecture: [docs/arc42/arc42-template.adoc](docs/arc42/arc42-template.adoc)
- Architecture Decision Records: [docs/adr](docs/adr)
