## 1. Architecture decision and documentation

- [x] 1.1 Write `docs/adr/0007-single-container-deployment.md` (Status / Context / Decision / Consequences) with status "Accepted", covering the single-container topology (D1), building on the target device (D2), and the bind-mounted data directory with a non-root container user (D4)
- [x] 1.2 Update `docs/arc42/adoc/07_deployment_view.adoc`: keep the local development setup and add the home-network container topology as a second environment
- [x] 1.3 Reference ADR-0007 in `docs/arc42/adoc/09_architecture_decisions.adoc`
- [x] 1.4 Extend `docs/arc42/adoc/02_architecture_constraints.adoc` with the deployment constraints (Docker and Docker Compose on the target device, `linux/amd64` and `linux/arm64`, database on local storage) and add a deployment paragraph to `docs/arc42/adoc/04_solution_strategy.adoc`
- [x] 1.5 Add the deployment risks from `design.md` (SQLite on network storage, no backup, no authentication on the local network, UID mismatch) to `docs/arc42/adoc/11_technical_risks.adoc`

## 2. Database location becomes deployment-configurable

- [x] 2.1 Write a characterization test for `Settings`: `RECIPEBOOK_DATABASE_PATH` overrides the database path, and the documented default applies when it is unset. This codifies existing behavior, so it is expected to pass immediately — note that in the test, do not dress it up as a red step
- [x] 2.2 RED: write a test that `init_db()` creates the configured parent directory when it does not exist. It fails today because `app/db/session.py` does the `mkdir()` at module import against the singleton settings
- [x] 2.3 GREEN: move directory creation out of import time into `init_db()`, restructuring engine/session creation only as far as the test requires
- [x] 2.4 RED: write a test that an unusable configured database path makes startup fail with an error that names the offending path
- [x] 2.5 GREEN: surface that error from `init_db()` so the process exits non-zero with a diagnosable message
- [x] 2.6 REFACTOR: tidy `app/db/session.py` and `app/core/config.py` while keeping `uv run pytest` green

## 3. Backend serves the frontend build

- [x] 3.1 RED: write a test that `GET /` returns the frontend entry document when `RECIPEBOOK_FRONTEND_DIST` points at a directory containing a built frontend
- [x] 3.2 GREEN: add the `RECIPEBOOK_FRONTEND_DIST` setting to `app/core/config.py` and mount the directory as static files in `app/main.py`, after `include_router` so API routes keep precedence (D3)
- [x] 3.3 RED then GREEN: write a test that `GET /health` still answers `200 OK` while the static mount is active, guarding the registration order against regressions
- [x] 3.4 RED then GREEN: write a test that the application starts normally when the configured frontend directory does not exist, so `make backend` keeps working without a frontend build
- [x] 3.5 Confirm `npm run build` in `frontend/` produces `dist/` with the expected entry document; no frontend source change is expected

## 4. Container image

- [x] 4.1 Add `.dockerignore` excluding `node_modules/`, `.venv/`, `backend/data/`, `frontend/dist/`, `.git/`, and test caches
- [x] 4.2 Write the multi-stage `Dockerfile`: a Node stage running `npm ci` and `npm run build` in a layer order that caches dependencies across source-only changes, and a slim Python runtime stage that installs backend dependencies, copies the built frontend, creates a non-root user, sets the `RECIPEBOOK_*` defaults for the in-container paths, and starts Uvicorn bound to `0.0.0.0` via `CMD` (D8)
- [x] 4.3 Add a `HEALTHCHECK` that requests `/health` with `python -c` and `urllib.request`, without installing `curl` (D7)
- [x] 4.4 Build the image on the development machine and confirm the container starts and answers `/health`

## 5. Compose and operational configuration

- [x] 5.1 Write `docker-compose.yml`: build context, published port `8090`, bind mount `./data` to the in-container data path, `RECIPEBOOK_DATABASE_PATH` environment variable, `user:` defaulting to `1000:1000` and overridable, and `restart: unless-stopped`
- [x] 5.2 Add the compose bind-mount directory to `.gitignore` so deployment data never enters the repository
- [x] 5.3 Run `docker compose up -d --build` locally and confirm the container reaches the healthy state

## 6. Deployment documentation

- [x] 6.1 Add a deployment section to `README.md` with step-by-step instructions that do not require `make` on the target device (clone, create and `chown` the data directory, `docker compose up -d --build`, open the address)
- [x] 6.2 Document the UID/GID override for devices whose account is not `1000:1000`, including what the failure looks like
- [x] 6.3 Document that the data directory must be on local storage, because SQLite file locking is unreliable on NFS/SMB shares
- [x] 6.4 State explicitly that surviving restarts is not a backup, so the guarantee is not overread

## 7. Verification on the development machine

- [x] 7.1 Open the application in a browser, confirm the interface loads and `/health` answers `200 OK` on the same port
- [x] 7.2 Write data to the database, restart the container, and confirm the data is still readable
- [x] 7.3 Rebuild the image, recreate the container against the same directory, and confirm the data is still readable
- [x] 7.4 Point the data directory at an unwritable location and confirm the startup error names the path
- [x] 7.5 Confirm `uv run pytest`, `npm test`, `npm run build`, and `make dev` all still work unchanged

## 8. Verification on the Raspberry Pi

- [x] 8.1 Clone the repository on the Pi, create and `chown` the data directory, and run `docker compose up -d --build` on `linux/arm64`
- [x] 8.2 Open the application from another device in the home network via the Pi's IP address
- [x] 8.3 Reboot the Pi and confirm the container comes back and the data is intact
- [x] 8.4 Tick the acceptance criteria and Definition of Done on issue #2
