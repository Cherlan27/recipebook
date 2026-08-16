## Context

See `proposal.md` for motivation (GitHub Issue #1, "Closes #1"). The repository is currently empty aside from README, `.git`, and `openspec` — there is no existing code, dependency setup, or start procedure to build on.

The scaffold is constrained by Issue #1's acceptance criteria: a monorepo with `backend/` (FastAPI) and `frontend/` (Vue.js), `uv`/`pyproject.toml` for backend dependencies, CORS enabled for the Vite dev origin (`http://localhost:5173`), a SQLite file auto-created under `backend/data/app.db`, documented local start commands, and a `GET /health` endpoint that is automatedly testable.

## Goals / Non-Goals

**Goals:**
- Establish a backend/frontend layout and internal backend layering that follow-up issues (e.g. recipe CRUD) can build on directly.
- Wire up the full request path end to end (Vite dev server → CORS → FastAPI → async SQLAlchemy → SQLite) using the `/health` endpoint as the first proof.
- Provide a single local entry point (`Makefile`) for starting backend and frontend, individually or together.

**Non-Goals:**
- No domain models, CRUD endpoints, or business logic (recipes, ingredients, etc.) — that starts with the first feature issue.
- No database migrations tooling (e.g. Alembic) — deferred until a real model exists (see risk below).
- No CI/CD pipeline or production deployment target — local development only.
- No frontend state management (Pinia) — deferred until a feature needs shared state (ADR-3).

## Decisions

- **Async SQLAlchemy with `aiosqlite`** for backend database access — see ADR-1.
- **Composition API (`<script setup>`)** for Vue 3 components — see ADR-2.
- **Pinia deferred**, not part of this scaffold — see ADR-3.
- **Root `Makefile`** with `backend`, `frontend`, `dev` targets for local orchestration — see ADR-4.
- **Vitest** as the frontend test framework — see ADR-5.
- **Layered backend structure** (`app/api/routes`, `app/core`, `app/db`, `app/models`) instead of a single `app/main.py` — see ADR-6.

Concrete wiring for this change, building on those decisions:
- `app/core` holds settings (CORS allowed origins, SQLite file path) loaded via `pydantic-settings`, read once at startup.
- `app/db` creates the async engine and session factory on import and ensures `backend/data/` exists before the engine touches `app.db`, satisfying the "SQLite file auto-created" acceptance criterion without a separate bootstrap script.
- `app/api/routes/health.py` defines the `GET /health` route per `specs/health-check/spec.md`; `app/main.py` wires the FastAPI app, CORS middleware, and this router together.
- `backend/tests/test_health.py` uses FastAPI's `TestClient` against the app, following TDD: the test is written first and fails (no route yet), then `health.py` is added to make it pass.
- Frontend is a standard Vite + Vue 3 + TypeScript scaffold (`npm create vite@latest -- --template vue-ts`) with Vitest added on top; no custom structure beyond Vite's default is introduced, since there is no UI behavior yet beyond what Vite scaffolds.

## Risks / Trade-offs

- [Alembic setup is not trivial with an async engine] → Deferred to the first issue that introduces a real model; not needed while `app/models` is empty (tracked in arc42 section 11).
- [`make` is not available natively on Windows] → Documented as a setup prerequisite in the README (Git Bash/MinGW); `justfile`/`concurrently` remain a fallback if this causes friction (tracked in arc42 section 11 and ADR-4).
- [Layered backend structure adds scaffolding beyond what a single `/health` route strictly needs] → Accepted trade-off; avoids restructuring untested code on the very next issue (ADR-6).
