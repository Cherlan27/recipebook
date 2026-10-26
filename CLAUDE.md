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
make check     # backend tests, frontend tests, type-checked build, openspec validate --strict (also run in CI)
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

## Workflow

Full workflow: `CONTRIBUTING.md`. Rules agents need most:

- One issue = one OpenSpec change = one worktree and branch (`issue-<number>-<short-name>`) = one PR with `Closes #<issue>`. Never develop in the main checkout.
- Each phase is its own agent session with a fixed model (propose `opus`, apply `sonnet`, review `opus`, fixes `sonnet`, archive & PR `sonnet`; local `qwen` only for small changes). A `sonnet` coordinator (`/orchestrate-issue`) stops for a human after propose, after review, and before merge/deploy. Do only your phase.
- A phase is done when `make check` passes (twice in a row after apply and fixes). Tick a task only after its test or command passed in your session. Tests must be deterministic (no equality of two clock reads).
- Review (`/review-change`) writes findings to `openspec/changes/<change>/review.md` and changes no code; fixes implement only findings with `Decision: fix`.
- Run `/opsx:archive` on the branch before merging.
- A fresh worktree needs `uv sync --directory backend && npm ci --prefix frontend`.
- Dev servers use fixed ports `8000` and `5173`; do not start them if another worktree has them (`orca ports --json`).
- Never edit generated OpenSpec skills/commands in `.claude/` or `.opencode/`; put project rules in `openspec/config.yaml`.
- Style: simple technical English, short sentences, no filler. Reports at most 5 lines.
- After a shipped issue, `/adjust-workflow <issue>` records workflow changes in `docs/workflow-retros.md`.

## Documentation

- Contribution workflow: `CONTRIBUTING.md`
- Architecture (arc42): `docs/arc42/adoc/` (source files) — see especially `04_solution_strategy.adoc`, `05_building_block_view.adoc`, `09_architecture_decisions.adoc`
- Architecture Decision Records: `docs/adr/`
- This project uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) for spec-driven change planning: active work lives under `openspec/changes/`, completed changes are archived under `openspec/changes/archive/`, and current capability specs live under `openspec/specs/`.
