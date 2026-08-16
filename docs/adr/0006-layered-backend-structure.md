# 6. Layered backend structure

Date: 2026-08-15

## Status

Accepted

## Context

Issue #1 only requires a `GET /health` endpoint, so a single `app/main.py` file would technically be enough to satisfy the acceptance criteria. However, this is the project's first backend code, and every future issue (recipe CRUD, etc.) will build directly on whatever structure is chosen here.

## Decision

Give the backend a layered structure from the start, even though Issue #1 itself only needs a single endpoint:

- `app/api/routes` — HTTP endpoints
- `app/core` — configuration (CORS origin, DB path, ...) via settings
- `app/db` — SQLAlchemy engine/session management, declarative base
- `app/models` — SQLAlchemy models (empty placeholder in Issue #1)

## Consequences

- Follow-up issues that add real endpoints, config, or models can slot into the existing layers instead of restructuring the backend first.
- Slightly more scaffolding than a minimal `app/main.py` for a project that currently has exactly one endpoint.
- The alternative (single-file `app/main.py`, splitting into layers only when a second endpoint is added) was considered and rejected: it would force a restructure on the very next issue, on code that is not yet under test in its final shape.
