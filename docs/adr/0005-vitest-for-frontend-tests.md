# 5. Use Vitest for frontend tests

Date: 2026-08-15

## Status

Accepted

## Context

The backend already has an automated testing approach (pytest + FastAPI `TestClient`, see ADR-1). The frontend (Vue 3 + TypeScript + Vite, see ADR-2) has no test framework decided yet.

## Decision

Use Vitest as the frontend test framework.

## Consequences

- Vitest is Vite-native (shares Vite's config, transform pipeline, and dev-server speed), so no separate bundler/config setup is needed alongside the existing Vite scaffold.
- It has first-class support for Vue 3 + TypeScript and the Composition API, consistent with ADR-2.
- Frontend tests follow the same TDD red-green-refactor practice as the backend (see `openspec/config.yaml`), just with a different runner per side of the stack.
