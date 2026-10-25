## Why

The project's central goal is to run without depending on a third-party cloud, but today the application only exists as two local development processes started via `make dev`. There is no way to run it on the owner's own hardware.

We build the deployment path now, as a walking skeleton, while the application is still only a `/health` endpoint and a frontend scaffold. Every later feature then inherits a working deployment, and assumptions that break a deploy (paths, permissions, origins) surface immediately instead of accumulating until the end of the project.

Closes #2.

## What Changes

- Add a multi-stage `Dockerfile` that builds the frontend with Node and produces a single Python runtime image containing both the built frontend and the backend. The same file must build on `linux/amd64` (development machine) and `linux/arm64` (Raspberry Pi).
- Add a `docker-compose.yml` that mounts a persistent volume for application data and supplies configuration through environment variables.
- The backend serves the built frontend as static files, so the user interface and the API are reachable on a single port from the same origin. CORS is no longer needed for operation and becomes development-only configuration.
- The database location becomes deployment-configurable through the existing `RECIPEBOOK_DATABASE_PATH` environment variable, pointing at the mounted volume inside the container.
- Add a container `HEALTHCHECK` that reuses the existing `GET /health` endpoint.
- Document a step-by-step deployment procedure in the README that does not require `make` on the target device.
- Add an ADR recording the single-container topology decision, and update the arc42 Deployment View, which currently describes only the local two-process setup.

Explicitly out of scope, tracked as separate issues: file uploads and their volume (#4), and operation on a public VPS including authentication and TLS (#5). This change targets the home network only.

## Capabilities

### New Capabilities

- `deployment`: How the application is packaged, configured, and run on the owner's own hardware — single-container topology, same-origin delivery of frontend and API, configurable data location, data persistence across restarts, and container health reporting.

### Modified Capabilities

None. The `health-check` capability keeps its requirements unchanged: the `/health` endpoint is reused by the container health check, and its CORS requirement is already scoped to the frontend development origin.

## Impact

- **New files**: `Dockerfile`, `.dockerignore`, `docker-compose.yml`, ADR under `docs/adr/`.
- **Backend**: `app/main.py` gains static-file delivery of the frontend build; `app/core/config.py` gains a setting for the frontend build directory. `app/db/session.py` currently creates the data directory at *import* time, which fails before FastAPI starts if the mounted volume is not writable — this must move to a point where the failure is diagnosable.
- **Frontend**: built with `npm run build` during the image build; no source changes expected.
- **Dependencies**: static file delivery uses Starlette's `StaticFiles`, which ships with FastAPI, so no new backend runtime dependency is expected. Docker and Docker Compose become prerequisites on the target device.
- **Documentation**: README deployment section; `docs/arc42/adoc/07_deployment_view.adoc`; `docs/arc42/adoc/09_architecture_decisions.adoc`.
- **Follow-up coupling**: from #3 onward the container start must be able to run database migrations. The entrypoint is designed so this can be added without reworking the image layout.
