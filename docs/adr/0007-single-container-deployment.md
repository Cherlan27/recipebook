# 7. Single-container deployment with the backend serving the frontend

Date: 2026-09-20

## Status

Accepted

## Context

Issue #2 requires the application to run on hardware the owner controls (a Raspberry Pi in the home network), without depending on an external cloud. Until now the application only existed as two local development processes: Vite on port 5173 and Uvicorn on port 8000, bridged by CORS.

Moving to a deployed environment forces a decision that local development never had to make: the frontend is no longer a dev server but a static build, and something has to serve it. Three topologies were available, and the choice affects configuration, the number of moving parts, and how failures present themselves.

The deployment is built now, while the application is still only a `/health` endpoint and a frontend scaffold, so that every later feature inherits a working deployment path.

## Decision

Deploy the application as a **single container**. A multi-stage build compiles the frontend with Node and copies the resulting `dist/` into a Python runtime image, where the backend serves it as static files alongside the API. One port is published; the user interface and the API share an origin.

Supporting decisions made together with the topology:

- **Built on the target device** from source (`git pull` followed by a build). No image is pushed to a registry, which would reintroduce the third-party dependency this issue exists to remove.
- **Application data lives in a bind-mounted host directory**, with the database location supplied through the existing `RECIPEBOOK_DATABASE_PATH` setting. The container runs as a non-root user whose UID/GID is configurable, defaulting to `1000:1000`.
- **Operational configuration lives in `docker-compose.yml`** (volume, environment, published port, restart policy, health check), so deployment is a single reviewable command.
- **Scope is the home network.** TLS, authentication, and public exposure are deliberately excluded and tracked separately in issue #5.

## Consequences

- CORS is no longer required for operation and becomes development-only configuration. The existing `health-check` requirement covering the frontend development origin stays valid and unchanged.
- The alternative of **two containers behind a reverse proxy** was considered and rejected: it is the right split when frontend and backend are released independently, which is not the case here — both live in one repository and ship together. It would add a third component and a proxy configuration without buying separation the project uses.
- The alternative of **two containers with CORS in production** was rejected outright. The allowed origin would have to contain the concrete home-network address, which is unknown at build time, changes with DHCP, and differs between IP, hostname, and mDNS access. Its failure mode is silent: the interface loads and shows no data.
- A frontend-only change requires rebuilding the whole image. This is accepted; the Node stage is layered so dependency installation stays cached across source-only changes.
- A bind mount exposes the database as an ordinary file that can be inspected and copied, at the cost of host/container UID alignment. A named Docker volume would avoid that cost but hide the file behind Docker-managed storage. The one-time `chown` is documented in the deployment instructions.
- Surviving restarts is not a backup. The data outlives container restarts and image rebuilds, but not volume removal or storage failure. Backup remains a separate, unaddressed concern.
- The database must sit on local storage; SQLite file locking is unreliable on NFS/SMB shares.
- From issue #3 onward the container start will have to run database migrations. The image uses a plain `CMD` today; adding an `ENTRYPOINT` later is a local change that does not disturb the image layout.
