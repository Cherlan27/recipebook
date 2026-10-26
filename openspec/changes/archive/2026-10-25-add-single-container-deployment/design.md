## Context

Today the application only exists as two local processes started by the root `Makefile`: Vite on `:5173` and Uvicorn on `:8000`, with CORS bridging them. `backend/app/core/config.py` derives the database path from the source layout (`BACKEND_ROOT / "data" / "app.db"`) but already exposes it as a `pydantic-settings` field, so a `RECIPEBOOK_DATABASE_PATH` override works without code changes. `backend/app/db/session.py` creates that directory at *module import* time.

`/health` already exists from #1 and is the natural health signal for a supervisor.

See `proposal.md` — Why for motivation, and `specs/deployment/spec.md` for the behavior this must satisfy.

## Goals / Non-Goals

**Goals:**

- One deployable artifact that runs unchanged on the development machine and on the Raspberry Pi.
- The deployment is verifiable locally before it touches the target device.
- Configuration that later features (migrations, uploads) can extend without reworking the image layout.

**Non-Goals:**

- Automated builds, a registry, or any hosted CI — that would reintroduce the third-party dependency this change exists to avoid.
- Backup or restore. A volume surviving a restart is not a backup; that is a separate concern.
- TLS, authentication, and exposure beyond the home network — see #5.
- Multi-architecture *manifests*. The same source builds on both architectures; we do not publish a combined image.

## Decisions

### D1: One container, with the backend serving the frontend build

The Node build stage produces `dist/`, which is copied into the Python runtime image and served by the backend as static files. One published port, one process, same origin.

*Alternatives considered:*

- **Two containers behind a reverse proxy (nginx).** The conventional split, and the right answer if frontend and backend were released independently. Here they live in one repository and ship together, so the split buys separation we do not use, while adding a third component and a proxy configuration to the set of things that can be misconfigured.
- **Two containers, no proxy, CORS in production.** Rejected outright. `cors_allowed_origins` would have to contain the concrete home-network address, which is not known at build time, changes with DHCP, and differs between IP, hostname, and mDNS access. The failure mode is silent: the interface loads and shows no data.

*Consequence:* CORS becomes development-only configuration. The existing `health-check` requirement about the dev origin stays valid and is not changed.

### D2: Build on the target device from source

Deployment is `git pull` followed by a build on the Pi. No image is pushed anywhere.

*Alternative:* building `linux/arm64` on the development machine via emulation and transferring the image with `docker save` / `docker load` over SSH — a second, divergent path to maintain. Not adopted: build times on the target device are confirmed acceptable, so the simpler single path stands. Pushing to a registry is excluded by the project's independence goal.

### D3: Static files are mounted last, and only when the build directory exists

Route registration order matters: a catch-all static mount at `/` registered before the API routers would swallow `/health`. The static mount is therefore added after `include_router`.

The directory is also made optional. `make backend` runs the backend without ever building the frontend, and mounting a non-existent directory raises at startup. Making the mount conditional keeps the existing development workflow working unchanged instead of forcing every developer to run a frontend build first.

The location comes from a new `RECIPEBOOK_FRONTEND_DIST` setting, defaulting to the path used inside the image.

### D4: Bind-mounted host directory for data, container runs as a non-root user

Application data lives under a fixed path inside the container (`/app/data`), bind-mounted from a directory next to `docker-compose.yml`. `RECIPEBOOK_DATABASE_PATH` points into it.

*Alternative:* a named Docker volume. It sidesteps host/container UID mismatch entirely, which is the main cost of the bind mount. Rejected because the owner will want to see, copy, and eventually back up the database file as an ordinary file on the Pi, and a named volume hides it behind Docker-managed storage.

Running as root would also avoid the UID problem, at the price of root-owned files appearing on the host. Instead the container runs as a non-root user, and compose sets `user:` to a configurable UID/GID defaulting to `1000:1000` — the default account on Raspberry Pi OS. The deployment instructions include the one-time `chown` of the data directory.

### D5: Directory creation moves out of import time

`session.py` currently calls `mkdir()` when the module is imported. On an unwritable mount that fails before FastAPI starts, and the traceback points at an import, not at a permissions problem. It moves into `init_db()`, which already runs in the `lifespan` hook, and gains an error that names the configured path.

This is the one behavior in this change that is genuinely test-driven: it is a plain unit test with a temporary directory.

### D6: `docker-compose.yml` carries the operational configuration

Volume, environment, published port `8090`, restart policy, and health check are declarative in compose rather than a shell script, so the deploy step is `docker compose up -d --build` and the configuration is reviewable in the repository. The bare `Dockerfile` remains usable on its own.

### D7: The health check calls `/health` with Python, not `curl`

The slim Python base image does not ship `curl`, and installing it only for a health check adds an apt layer. A one-line `python -c` using `urllib.request` has no additional dependency.

### D8: Plain `CMD`, no entrypoint script yet

From #3 onward the container start will need to run database migrations. Introducing an entrypoint script now, with nothing in it but `exec uvicorn`, would be scaffolding for a feature that does not exist. `CMD` is used directly; adding an `ENTRYPOINT` later is a local change that does not disturb the image layout.

### D9: Verification is a smoke test, not TDD

A `Dockerfile` cannot be driven red-green-refactor. What can: the `RECIPEBOOK_DATABASE_PATH` override, the startup failure from D5, the conditional static mount, and `GET /` returning the interface — all `pytest` against `TestClient`. The container itself is verified by starting it and checking behavior. This is a deliberate, recorded exception to the project's TDD rule, not an oversight.

### D10: ADR-0007 and arc42 before implementation

The topology decision is recorded as `docs/adr/0007-single-container-deployment.md` with status "Accepted", and `docs/arc42/adoc/07_deployment_view.adoc` is updated from the current two-process development sketch to the container topology, with `09_architecture_decisions.adoc` and `02_architecture_constraints.adoc` reviewed alongside it. Per project rules this happens before the decision is implemented.

## Risks / Trade-offs

- **SQLite on a network filesystem corrupts.** If the bind mount is pointed at an NFS or SMB share, SQLite file locking is unreliable. → The data directory must be on local storage; stated explicitly in the deployment instructions.
- **Frontend changes require a full image rebuild.** The cost of D1. → Acceptable: both sides ship together from one repository. The Node build stage is layered so `npm ci` is cached across source-only changes.
- **The frontend build is the expensive part of rebuilding on the Pi.** Build times on the target device are confirmed acceptable, so this is a cost rather than a blocker. → The Node stage is layered so `npm ci` stays cached across source-only changes, keeping repeat deploys cheap.
- **The home-network address can change.** DHCP may hand the Pi a different IP. → Out of scope for this change, but the instructions recommend a DHCP reservation or a fixed address.
- **Restart-safe is not loss-safe.** The data survives restarts and rebuilds, but not `docker compose down -v`, an accidental deletion, or SD-card failure. → Stated in the instructions so the guarantee is not overread. Backup is a separate concern.
- **No authentication on the local network.** Anyone on the home network can read and write. → Accepted for the home-network scope; #5 covers the case where that is not acceptable.
- **UID mismatch on first deploy.** If the Pi account is not `1000:1000`, the container cannot write until `user:` is adjusted. → The failure is diagnosable by D5, and the instructions cover the `chown` and the override.

## Migration Plan

There is no existing deployment and no existing data, so this is a first installation rather than a migration.

1. Build and run locally on the development machine; verify the interface loads and `/health` answers `200 OK`.
2. Stop the container, start it again, and confirm the database file persists.
3. On the Pi: clone the repository, create and `chown` the data directory, run `docker compose up -d --build`.
4. Verify from another device in the home network via the Pi's address.
5. Reboot the Pi and confirm the container returns and the data is intact.

*Rollback:* `docker compose down` removes the container; the bind-mounted data directory is untouched. Reverting to an earlier commit and rebuilding restores the previous image. Nothing outside the repository and that one directory is modified.
