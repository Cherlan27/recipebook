# 4. Use a Makefile for local development orchestration

Date: 2026-08-15

## Status

Accepted

## Context

Issue #1 requires that backend and frontend can each be started locally via a documented command, and it should also be possible to start both together for day-to-day development. Options considered: a root `Makefile`, a `justfile`, or an npm-based approach (e.g. `concurrently`) run from the frontend package.

## Decision

Add a root `Makefile` with targets `backend` (start FastAPI via `uv run uvicorn app.main:app --reload`), `frontend` (start Vite via `npm run dev`), and `dev` (start both in parallel).

## Consequences

- `make` was already installed on the primary development machine (Windows, via Git Bash), so no new tool needed to be introduced.
- Windows does not ship `make` natively; a fresh machine without Git Bash/MinGW cannot use the Makefile out of the box. This is documented as a setup requirement in the README (see also the corresponding risk in the arc42 documentation, section 11).
- `justfile` and `concurrently` were considered as more cross-platform alternatives and can be revisited if the `make` dependency becomes a recurring friction point.
