# 9. Vue Router in hash mode

Date: 2026-10-30

## Status

Accepted

## Context

Issue #8 adds the first two views: an overview and a recipe detail view. The frontend has no routing yet. Users need deep links (`/#/recipes/5`) and a working browser back button.

The backend serves the frontend build as static files at `/`, mounted after all routers (ADR-7). A router in history mode would send paths such as `/recipes/5` to the server. On a reload the server would have to answer them with `index.html`, without shadowing `/api`.

## Decision

Use Vue Router in **hash mode**. Addresses look like `/#/recipes/5`. The server only ever sees `/`, so deep links and reloads work with the existing static mount.

Routes: `/` (overview) and `/recipes/:id` (detail). The address uses the recipe `id`, not `nr`.

## Consequences

- ADR-7 is unchanged. The backend needs no SPA fallback route.
- ADR-3 stays valid. The router holds no shared data; each view loads its own data. Pinia is still deferred.
- Rejected: **history mode**. It needs a fallback route in the backend that must not shadow `/api`, and a second rule to keep in sync with future API paths.
- Rejected: **no router**. It gives no deep links and no back button.
- Hash URLs look less clean. This is accepted for a home-network app.
- Switching to history mode later is a local change: the `createWebHashHistory` call in `src/router.ts` plus a backend fallback route.
