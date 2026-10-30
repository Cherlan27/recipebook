## Context

The backend has `GET /health`, the async session dependency `get_db` (`app/db/session.py`), and the `Recipe`/`Tag` models with tags loaded eagerly (`selectin`). The static frontend is mounted at `/` after all routers (ADR-7). The frontend is still the Vite scaffold, without routing. Motivation: see proposal.md.

## Goals / Non-Goals

**Goals:** the first real API endpoints and the first two views, with a layout that #9 (editing) and #10 (filtering) extend.

**Non-Goals:** writing endpoints, filter or query parameters, pagination, shared frontend state, styling beyond readable defaults.

## Decisions

**D1 Vue Router in hash mode (ADR-9).** Addresses look like `/#/recipes/5`. The server only ever sees `/`, so deep links and reloads work with the existing static mount and ADR-7 stays untouched. Rejected: history mode (needs an SPA fallback route in the backend that must not shadow `/api`); no router (no deep links, no browser back button).

**D2 `/api` prefix and Vite dev proxy.** Recipe routes live under `/api`; `vite.config.ts` proxies `/api` to `http://localhost:8000`. The frontend uses relative URLs, the same in development and in the container. Rejected: absolute backend URL over CORS in development, which differs from production. `/health` keeps its path.

**D3 Pydantic response schemas in `app/schemas/recipe.py`.** `RecipeListItem` and `RecipeDetail` with `from_attributes`; `tags` is converted to sorted names by a validator. Routes declare `response_model`, so the API shape does not follow model changes by accident. Rejected: returning hand-built dicts from routes.

**D4 Routes read through `get_db`.** Tests override the dependency with a session on a temporary database built by the real migrations (like the existing `db_session` fixture). Rejected: a repository layer, which adds an abstraction for two queries.

**D5 Lines are split in the frontend.** The API returns `ingredients` and `steps` as stored text; one pure function `toLines(text)` splits on `\r?\n`, trims, and drops empty lines. Rejected: arrays in the API, which #9 would have to turn back into text.

**D6 No Pinia, a small fetch module.** Each view loads its data itself through `src/api/recipes.ts`, which throws a distinct `NotFoundError` for `404` and a `BackendUnavailableError` for network errors and `5xx`. ADR-3 stays valid. Rejected: Pinia, as no state is shared between views yet.

## Risks / Trade-offs

- [Hash URLs look less clean] → Accepted for a home-network app; ADR-9 records how to switch to history mode later.
- [No pagination] → Home data volume is a few hundred recipes; the full list stays small. Revisit if it grows.
- [Tags are loaded per recipe with `selectin`] → One extra query for all tags of the list; acceptable.

## Migration Plan

No schema change. Deploy as usual (`git pull`, build, `docker compose up -d`). Rollback: redeploy the previous commit.
