# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Recipebook: a recipe management app. Monorepo with a FastAPI backend (`backend/`) and a Vue 3 + TypeScript frontend (`frontend/`), sharing a SQLite database.

## Commands

Run from the repo root (`Makefile` orchestrates both sides):

```
make backend   # cd backend && uv run uvicorn app.main:app --reload   (http://localhost:8000)
make frontend  # cd frontend && npm run dev                           (http://localhost:5173)
make dev       # both, in parallel
```

Backend tests:
```
cd backend && uv run pytest
cd backend && uv run pytest tests/test_health.py::test_health_returns_200_ok  # single test
```

Frontend tests:
```
cd frontend && npm test          # vitest run
cd frontend && npm run build     # vue-tsc -b && vite build (also type-checks)
```

Backend dependencies are managed with `uv` (`uv add <pkg>`, `uv add --dev <pkg>`), not pip. Frontend with npm.

`make` is not native on Windows — requires Git Bash/MinGW.

## Architecture

**Backend (`backend/app/`)** is layered on purpose (see `docs/adr/0006-layered-backend-structure.md`), even though it currently only has one endpoint:
- `app/api/routes/` — FastAPI routers (one module per resource, e.g. `health.py`)
- `app/core/config.py` — `pydantic-settings`-based `Settings`, exported as a singleton `settings`; env vars use the `RECIPEBOOK_` prefix
- `app/db/session.py` — async SQLAlchemy engine/session (SQLite via `aiosqlite`, driver URL `sqlite+aiosqlite:///...`). `init_db()` is called from the FastAPI `lifespan` in `app/main.py` specifically to force-open a connection on startup — `create_async_engine` alone does not create the `.db` file, only an actual connection does.
- `app/db/base.py` — SQLAlchemy `DeclarativeBase` for future models
- `app/models/` — SQLAlchemy models (empty so far)
- `app/main.py` — wires the FastAPI app, CORS middleware, and routers together

Routes are added to `app/main.py` via `app.include_router(...)`; new endpoint modules go under `app/api/routes/`.

**Frontend (`frontend/`)** is a standard Vite + Vue 3 + TypeScript scaffold. Components use the Composition API (`<script setup lang="ts">`), not the Options API. No state management library (e.g. Pinia) is set up yet — add one only when a feature needs state shared across components.

**Database**: SQLite file at `backend/data/app.db`, auto-created on backend startup, git-ignored.

## Conventions (from `openspec/config.yaml`)

- All artifacts, documentation, and code comments are written in English.
- Test-Driven Development: write a failing test first, minimal code to pass, then refactor. Backend tests use `pytest` + FastAPI's `TestClient`; frontend tests use Vitest.
- Architecture decisions require an ADR in `docs/adr/` (Status/Context/Decision/Consequences, status "Accepted") *before* the decision is implemented, and the corresponding `docs/arc42/adoc/` sections must be updated to match.

## Documentation

- Architecture (arc42): `docs/arc42/adoc/` (source files) — see especially `04_solution_strategy.adoc`, `05_building_block_view.adoc`, `09_architecture_decisions.adoc`
- Architecture Decision Records: `docs/adr/`
- This project uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) for spec-driven change planning: active work lives under `openspec/changes/`, completed changes are archived under `openspec/changes/archive/`, and current capability specs live under `openspec/specs/`.
