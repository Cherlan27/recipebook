## 1. Backend Project Setup

- [x] 1.1 Initialize `backend/` with `uv init` and `pyproject.toml`; add dependencies `fastapi`, `uvicorn`, `sqlalchemy[asyncio]`, `aiosqlite`, `pytest`, `httpx`
- [x] 1.2 Create the layered package structure: `app/api/routes/`, `app/core/`, `app/db/`, `app/models/` (per ADR-6)
- [x] 1.3 Add `backend/data/.gitkeep` and ignore `backend/data/*.db` in `.gitignore`

## 2. Backend: Configuration & Database Layer

- [x] 2.1 Add `app/core/config.py` with settings for the CORS allowed origin (`http://localhost:5173`) and the SQLite file path (`backend/data/app.db`)
- [x] 2.2 Add `app/db/session.py`: create the async engine (`sqlite+aiosqlite:///...`) and `AsyncSession` factory, ensuring `backend/data/` exists before the engine touches the file (per ADR-1)
- [x] 2.3 Add `app/db/base.py` with the SQLAlchemy declarative base, for future models

## 3. Backend: Health Endpoint (TDD)

- [x] 3.1 Write a failing test in `backend/tests/test_health.py` asserting `GET /health` returns `200 OK` (red)
- [x] 3.2 Add `app/api/routes/health.py` with the `GET /health` route returning `200 OK` (green)
- [x] 3.3 Wire the health router and CORS middleware (allowing the frontend dev origin) into `app/main.py`; confirm the test still passes
- [x] 3.4 Refactor if needed while keeping the test green (e.g. extract router registration)

## 4. Frontend Project Setup

- [x] 4.1 Scaffold `frontend/` with Vite's `vue-ts` template (Vue 3 + TypeScript)
- [x] 4.2 Add Vitest as a dev dependency with a minimal config aligned with the Vite config (per ADR-5)
- [x] 4.3 Confirm the default scaffolded component uses `<script setup lang="ts">` (per ADR-2)

## 5. Local Development Orchestration

- [x] 5.1 Add a root `Makefile` with a `backend` target running `uv run uvicorn app.main:app --reload` from `backend/`
- [x] 5.2 Add a `frontend` target running `npm run dev` from `frontend/`
- [x] 5.3 Add a `dev` target that starts both targets in parallel (per ADR-4)

## 6. Documentation

- [x] 6.1 Update the root `README.md` with local setup steps and all start commands (`make backend` / `make frontend` / `make dev`, plus the underlying `uv run uvicorn ...` / `npm run dev` commands)
- [x] 6.2 Note the Windows `make` prerequisite (Git Bash/MinGW) in the README

## 7. Verification

- [x] 7.1 Run `pytest` in `backend/` and confirm `test_health.py` passes
- [x] 7.2 Run `make dev` and confirm the SQLite file is created at `backend/data/app.db` and both servers start
- [x] 7.3 From the running frontend dev server, confirm a request to `GET /health` succeeds without a CORS error in the browser console
