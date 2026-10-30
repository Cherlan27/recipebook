## 1. Architecture decision and documentation

- [ ] 1.1 Write `docs/adr/0009-vue-router-hash-mode.md` (Status / Context / Decision / Consequences) with status "Accepted": Vue Router in hash mode (D1), rejected history mode and no router, ADR-7 unchanged, ADR-3 still valid (D6)
- [ ] 1.2 Update `docs/arc42/adoc/09_architecture_decisions.adoc` with an ADR-9 entry
- [ ] 1.3 Update `docs/arc42/adoc/05_building_block_view.adoc`: interface `/api` (relative URLs, dev proxy instead of CORS for `/api`), `app/schemas` and the `recipes` router in the backend white box, frontend building blocks (router, views, `src/api`)

## 2. Recipe list endpoint

Tests use `TestClient` with `get_db` overridden by a session on a temporary migrated database (D4); recipes are created through the models.

- [ ] 2.1 Test, then code, for scenario *Empty database*: add `app/schemas/recipe.py` with `RecipeListItem`, `app/api/routes/recipes.py` with `GET /api/recipes`, and include the router in `app/main.py` before the static mount
- [ ] 2.2 Test, then code, for scenario *List is sorted by number*
- [ ] 2.3 Test, then code, for scenarios *List entries carry the overview fields* (tag names sorted) and *List entry of a recipe with only the required fields*

## 3. Recipe detail endpoint

- [ ] 3.1 Test, then code, for scenario *Detail with all fields* (API): `RecipeDetail` schema and `GET /api/recipes/{id}`, line breaks kept
- [ ] 3.2 Test, then code, for scenario *Unknown id*: `404`
- [ ] 3.3 Refactor routes and schemas while `uv run pytest` stays green

## 4. Frontend setup

- [ ] 4.1 Add the dependency with `npm install vue-router --prefix frontend`; add the `/api` proxy to `http://localhost:8000` in `frontend/vite.config.ts` (D2)
- [ ] 4.2 Test, then code, for the API module `src/api/recipes.ts`: typed `fetchRecipes()` and `fetchRecipe(id)` with relative URLs, `NotFoundError` on `404`, `BackendUnavailableError` on network errors and `5xx` (D6); `fetch` is stubbed with `vi.stubGlobal`
- [ ] 4.3 Test, then code, for `toLines(text)`: splits on `\n` and `\r\n`, trims, drops empty and whitespace-only lines, returns `[]` for `null` (D5)
- [ ] 4.4 Set up the router in hash mode (`/` overview, `/recipes/:id` detail) in `src/router.ts`, use it in `main.ts` and `App.vue` (`<RouterView>`), and remove the scaffold `HelloWorld` component and its test expectations; tests mount with a memory-history router

## 5. Overview

- [ ] 5.1 Test, then code, for scenario *Overview shows recipes sorted by number*: `src/views/RecipeListView.vue`, empty fields hidden
- [ ] 5.2 Test, then code, for scenario *Recipe is opened from the overview*: each entry links to `/recipes/<id>`
- [ ] 5.3 Test, then code, for scenario *Empty-database hint*
- [ ] 5.4 Test, then code, for scenario *Backend-unreachable hint on the overview*

## 6. Detail view

- [ ] 6.1 Test, then code, for scenario *Detail with all fields* (UI): `src/views/RecipeDetailView.vue`
- [ ] 6.2 Test, then code, for scenario *Detail with only the required fields*: empty fields and their labels hidden
- [ ] 6.3 Test, then code, for scenario *Line-wise ingredients and steps*: ingredients as `<ul>`, steps as `<ol>`, using `toLines`
- [ ] 6.4 Test, then code, for scenario *Unknown recipe*: not-found hint with a link to the overview
- [ ] 6.5 Test, then code, for scenario *Backend-unreachable hint on the detail view*
- [ ] 6.6 Refactor views and API module while `npm test --prefix frontend` stays green

## 7. Verification

- [ ] 7.1 Run `make check` (backend tests, frontend tests, type-checked build, `openspec validate --strict`); it passes twice in a row
- [ ] 7.2 Manual check with the dev servers (needs ports 8000 and 5173 free, check `orca ports --json`): overview loads through the proxy; with the backend stopped, the backend-unreachable hint appears
- [ ] 7.3 Manual check for scenario *Empty state on the Raspberry Pi* (needs the Pi and Docker; done by the human after merge): deploy, open the overview from another device, see the empty-database hint; a `/#/recipes/1` reload shows the not-found hint
