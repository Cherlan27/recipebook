## Why

Recipes can be stored since #3, but nobody can see them. A read-only overview and detail view are the base for capturing (#9) and filtering (#10), which cannot be checked without them. Closes #8.

## What Changes

- Backend: `GET /api/recipes` returns all recipes (`id`, `nr`, `name`, `effort`, `time_minutes`, `kid_friendly`, tag names), sorted by `nr`, without pagination.
- Backend: `GET /api/recipes/{id}` returns one recipe with all fields, including ingredients, steps, and tags; an unknown `id` returns `404`.
- Backend: Pydantic response schemas in a new package `app/schemas/`. `/health` stays unchanged.
- Frontend: Vue Router in hash mode (`/#/recipes/12`). The overview lists all recipes; a click opens the detail view. URLs use `id`; the UI shows `nr`.
- Frontend: the detail view shows ingredients as a bulleted list and steps as a numbered list, one entry per non-empty line, and hides empty fields.
- Frontend: a hint for an empty database and a short hint when the backend is unreachable.
- Development: a Vite proxy forwards `/api` to `:8000`; the frontend uses relative URLs.
- New ADR-9 (Vue Router in hash mode); arc42 sections 05 and 09 updated. No Pinia (ADR-3 stays valid).
- Out of scope: filter state and query parameters (#10), creating and editing (#9).

## Capabilities

### New Capabilities
- `recipe-api`: read-only HTTP endpoints for the recipe list and a single recipe.
- `recipe-ui`: overview and detail view in the frontend, including empty and error states.

### Modified Capabilities

## Impact

- Backend: new `app/schemas/`, new router `app/api/routes/recipes.py`, wired in `app/main.py`. API routes take precedence over the static frontend mount (ADR-7).
- Frontend: new dependency `vue-router`; new views and router setup; `vite.config.ts` gets a dev proxy. The scaffold `HelloWorld` component is replaced.
- Docs: `docs/adr/0009-*.md`, `docs/arc42/adoc/05_building_block_view.adoc`, `docs/arc42/adoc/09_architecture_decisions.adoc`.
- Deployment: no change to the container or compose file; the Pi check covers deployment and the empty state only, because recipes can be created only with #9.
