---
name: review-change
description: Review the current branch's OpenSpec change before it is archived and merged — spec conformance, test evidence, project rules, correctness, security, and deployment impact — and write numbered findings to openspec/changes/<change>/review.md. Use for phase 3 (review analysis) in CONTRIBUTING.md, or when asked to review a branch, change, or PR in this repository. Does not modify code.
---

# Review a change

You are the reviewer, not the author. Find the problems that matter before this
branch is merged, prove each one, and record them so a human can decide what
gets fixed. **Do not modify source code, tests, specs, or docs.** The only file
you write is `review.md`.

Input: an optional base ref (default `origin/main`) and an optional change name.

## 1. Establish scope

```bash
git fetch -q origin
git log --oneline origin/main...HEAD
git diff --stat origin/main...HEAD
git diff origin/main...HEAD
```

Find the active change: the directory under `openspec/changes/` (not `archive/`)
that this branch adds or modifies, or the name you were given. If there is none,
review the diff anyway, skip the spec checks, and report in chat instead of
writing `review.md`.

## 2. Understand the intent before judging the code

Read, in this order:

1. `CLAUDE.md` and `openspec/config.yaml` — project rules.
2. The change: `proposal.md`, `design.md`, `tasks.md`, and every delta spec under `specs/`.
3. The GitHub issue named in `Closes #<n>` (`gh issue view <n>`) — its acceptance criteria and Definition of Done.
4. Any ADR the change adds or references in `docs/adr/`.

## 3. Read the code in context

For every changed file, read the **whole file**, not just the hunk. Also read
the tests that exercise it and the direct callers of anything whose signature
or behavior changed.

## 4. Run the verification

```bash
make check
```

It runs the backend tests, the frontend tests, the type-checked build, and
`openspec validate --all --strict`. A failure is a CRITICAL finding; quote the
relevant output.

## 5. Review checklist

**A. Spec conformance and test evidence** — the most important section.

- Every scenario of every ADDED/MODIFIED requirement is implemented.
- Every scenario has a test that would fail without the implementation. Name the test; a scenario without one is MAJOR.
- Nothing is implemented that no spec, task, or design decision asks for.
- Every ticked task in `tasks.md` is actually done. A false tick is MAJOR.
- The issue's acceptance criteria and Definition of Done are covered or explicitly deferred.

**B. Project rules**

- An architecture decision has an ADR with status "Accepted" and matching updates in `docs/arc42/adoc/`.
- Artifacts, docs, and code comments are in English.
- Backend layering: routers in `app/api/routes/`, settings in `app/core/config.py` with the `RECIPEBOOK_` prefix, models in `app/models/`.
- Frontend: Composition API with `<script setup lang="ts">`; no state library without a feature that needs shared state.
- New dependencies are justified and the lock files (`backend/uv.lock`, `frontend/package-lock.json`) are updated.

**C. Correctness and robustness**

- Logic, edge cases, wrong assumptions, off-by-one errors.
- Errors at system boundaries (request input, filesystem, database) are handled; no swallowed exceptions or silent failures.
- Async code: no blocking I/O in async paths; sessions and connections are closed.
- Database: constraints and indexes the specs imply, no N+1 queries, every schema change comes with a migration that also works on a database holding data.

**D. Security**

- Injection (SQL, command, path traversal), unsafe file handling, secrets in code or config, CORS widened beyond the development origin, missing auth where a spec requires it.

**E. Contracts and deployment**

- Breaking changes to API responses, routes, config variables, or the schema.
- `Dockerfile` and `docker-compose.yml`: still builds for `linux/amd64` and `linux/arm64`; new persistent data lives on the mounted volume; new environment variables are documented in the README.

**F. Leftovers**

- Debug output, commented-out code, unused imports, TODOs without an issue.

## 6. Verify before you report

For each candidate finding, go back to the code and confirm it. Drop anything
you cannot point to with a file and line, anything that is an intentional
decision recorded in the design or an ADR, and pure style preferences. If a
finding depends on an assumption, state the assumption.

Severity:

- **CRITICAL** — failing verification, data loss, security hole, or behavior that contradicts a spec. Must be fixed before merge.
- **MAJOR** — a scenario without implementation or test, a false task tick, a violated project rule, or a likely bug in a realistic edge case.
- **MINOR** — robustness or maintainability problems that are worth fixing but do not block the merge.

## 7. Write `openspec/changes/<change>/review.md`

If the file already exists, append a new `## Round <n>` section instead of
overwriting earlier rounds. Use this structure:

```markdown
# Review: <change-name>

## Round 1

Base `origin/main` @ <short-sha> · Head <short-sha> · <YYYY-MM-DD> · Reviewer: <model>

### Summary

One paragraph: what the change does and your overall assessment.

### Verification

| `make check` step | Result |
|---|---|
| `uv run pytest` | ✅ 12 passed |
| `npm test` | ✅ 3 passed |
| `npm run build` | ✅ |
| `openspec validate --all --strict` | ✅ |

### Findings

#### R1 · MAJOR · `backend/app/api/routes/recipes.py:42`

What is wrong and why it matters. Suggested fix, if it is not obvious.

- Decision: pending
- Status: open

### Nits

- N1 · `path:line` — short note.
```

Number findings `R1`, `R2`, … continuing across rounds. Leave `Decision:
pending` and `Status: open`: the human sets the decision (fix / skip / defer)
at Gate 2, and the fixer sets the status. Omit empty sections.

Commit only `review.md`, with the message `docs: review round <n> of <change-name>`.

## 8. Report in chat

Finish with the counts per severity, the IDs of all CRITICAL and MAJOR
findings, and the path of `review.md`.
