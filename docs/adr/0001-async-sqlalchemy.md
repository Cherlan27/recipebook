# 1. Use async SQLAlchemy instead of sync

Date: 2026-08-15

## Status

Accepted

## Context

The backend (Issue #1, project scaffold) needs database access to SQLite. FastAPI is an async framework — request handlers are `async def` and run on a single event loop per worker.

## Decision

Use SQLAlchemy 2.0 in async mode, with `create_async_engine` / `AsyncSession` and the `aiosqlite` driver (`sqlite+aiosqlite:///...`) instead of the default sync `sqlite3` driver.

## Consequences

- Synchronous DB calls in async request handlers would block the event loop; async SQLAlchemy avoids that.
- The migration effort from sync to async SQLAlchemy is low on a greenfield project: a different connection URL, `await` on session calls, and an async dependency (`aiosqlite`).
- FastAPI's `TestClient` works unchanged against async-defined endpoints, so no special test setup is needed.
- Schema migrations (e.g. with Alembic) will later need a sync-driver workaround or an async-capable `env.py`. Not relevant to Issue #1 (no models yet), but should be planned for the first issue that introduces a real domain model.
