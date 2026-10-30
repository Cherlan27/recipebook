# Review: recipe-list-detail

## Round 1

Base `ae3823b` (= `origin/main`) · Head `9aebf00` · 2026-10-30 · Reviewer: claude-opus-5-5

### Summary
The change implements every scenario of `recipe-api` and `recipe-ui` (except the manual Pi check, which was moved to the PR checklist at Gate 1). Each scenario has a test. ADR-9 is Accepted, arc42 05/09 match, and layering follows ADR 0006. One minor error-handling deviation from D6, plus three nits.

### Verification
| step | result |
|---|---|
| `make check` | ✅ backend 65 passed · frontend 6 files / 28 tests passed · build ok · openspec 5 passed, 0 failed |
| `trail check` | ✅ no conflicts (1 learning, none bears on the change) |
| probe: `TestClient(app).get('/api/recipes/NaN').status_code` | 422 (used for R1) |

### Findings

#### R1 · MINOR · `frontend/src/api/recipes.ts:33`
`getJson` throws `BackendUnavailableError` for every non-ok status except 404, so any 4xx counts as "backend unreachable". D6 and the spec limit that error to network errors and `5xx`. Failure: when a user opens `/#/recipes/abc` (typo, stale link), `RecipeDetailView.vue:19` sends `Number('abc')` → `/api/recipes/NaN`. The backend answers 422 (probe above), and the page says "The backend is not reachable" although the backend is up. Fix: throw `BackendUnavailableError` only for `status >= 500`, and show the not-found hint for an id that is not a positive integer (check in the view, or treat 422 like 404). Add a test for it.

- Recommendation: fix — small change, brings the code back in line with D6.
- Decision: pending
- Status: open

### Nits
- N1 · `frontend/src/views/RecipeDetailView.test.ts:77`, `RecipeListView.test.ts:71` — only the label `Effort` is checked, not the value; `toContain('Effort 2/3')` would catch a missing value.
- N2 · `frontend/src/style.css:171` — scaffold leftovers after removing `HelloWorld`: CSS for `#center`/`#next-steps` and the unused `src/assets/{hero.png,vite.svg,vue.svg}` and `public/icons.svg`.
- N3 · `CLAUDE.md:45` — the backend layer list does not mention the new `app/schemas/` package (arc42 05 does).
