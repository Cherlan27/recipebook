# Contributing

How changes are made in this repository, by humans and by coding agents alike.

The project-wide rules (English for all artifacts, Test-Driven Development, an
accepted ADR plus updated arc42 docs before any architecture decision) live in
[`openspec/config.yaml`](openspec/config.yaml) and are summarized in
[`CLAUDE.md`](CLAUDE.md). This document describes the workflow around them.

## One issue, one change, one branch

Every piece of work starts from a GitHub issue and maps one-to-one onto
(Trivial track: no OpenSpec change, see *Tracks*):

- an **OpenSpec change** under `openspec/changes/<change-name>/`,
- a **git worktree** and **branch** sharing one name, `issue-<number>-<short-name>`,
  e.g. `issue-3-recipe-model`,
- a **pull request** that says `Closes #<issue>`.

Issues labelled `refinement needed` are refined first: open questions answered,
acceptance criteria and Definition of Done verifiable.

Commit messages follow the Conventional Commits style used in the history
(`feat:`, `fix:`, `docs:`, `chore:`, …).

## Workspace layout

- The **main checkout stays on `main`**. Nothing is developed there; it is used
  to pull, compare, and look things up.
- Each issue is worked on in **its own worktree**, branched from `origin/main`.
  With Orca, create it together with its coordinator agent (see
  [Orchestrating the phases with Orca](#orchestrating-the-phases-with-orca));
  without Orca, `git worktree add ../issue-3-recipe-model -b issue-3-recipe-model origin/main`.
- A fresh worktree has no `.venv` and no `node_modules`. Install both before
  running anything (in Orca, configure this once as the repo's **setup script**
  so it runs automatically for every new worktree):

  ```
  uv sync --directory backend && npm ci --prefix frontend
  ```

## Lifecycle of a change

Each phase runs as its own agent session with the model that fits the work.
Separate sessions keep each phase's context clean: the reviewer in particular
must not be the agent that wrote the code.

| # | Phase | What happens | Agent · model |
|---|---|---|---|
| 1 | **Propose** | `/opsx:propose` creates proposal (`Closes #<issue>`), delta specs, design, and tasks. If the change involves an architecture decision, the ADR in `docs/adr/` and the `docs/arc42/adoc/` updates are written here, *before* implementation. | `claude` · `opus` |
| | ⏸ **Gate 1** | A human approves the proposal and decides whether the change counts as small (see below). | human |
| 2 | **Apply** | `/opsx:apply`, task by task, red → green → refactor, one commit per task group, until `make check` passes. | `claude` · `sonnet`; the local model via `--local` (see *Local flow*) |
| 3 | **Review analysis** | `/agent-workflow:review-change`: checks the branch against `main` for spec conformance, test evidence, project rules, correctness, security, and deployment impact. Writes numbered findings to `openspec/changes/<change>/review.md`, changes no code. | `claude` · `opus` |
| | ⏸ **Gate 2** | A human selects which findings to fix. Judgment calls (`Recommendation: decide`) and skipped CRITICAL/MAJOR findings come without a default. | human |
| 4 | **Review fixes** | Implements the selected findings (TDD where behavior changes), marks each one `Status: fixed` in `review.md`, re-runs `make check`. A second review round follows only if a CRITICAL or MAJOR finding was fixed; at most two rounds. Round 2 is scoped: it checks the fix commits only. | `claude` · `sonnet` |
| 5 | **Archive & PR** | `/opsx:archive` on the branch, PR against `main` with `Closes #<issue>`. | `claude` · `sonnet` |
| | ⏸ **Gate 3** | A human approves the merge (merge commit) and the deployment to the Pi; then branch and worktree are cleaned up. | human |

**Verification** – `make check` runs the backend tests, the frontend tests,
the type-checked frontend build, and `openspec validate --all --strict`. It
must pass twice in a row at the end of phases 2 and 4 (the second run catches
flaky tests), and GitHub Actions runs it on every pull request
(`.github/workflows/check.yml`).

**Test integrity** – `make check` also passes once before any code change
(baseline). A pass only counts if the tests still test the behavior: deleting,
skipping, or loosening a test, or weakening the check, fails the phase. The
coordinator checks every result itself; a worker's report is a pointer, not proof.

**Blocked means stop** – a worker that is blocked (tool missing, environment
down, task unclear) stops and reports; it does not work around the blocker. A
phase that runs longer than `limits.phase_minutes` is checked and, if stuck,
handed to the human.

**Code map** – `code_map: trail` is set: workers find code with the Trail Code
CLI (`trail ask`, `trail skeleton`, `trail callers`) before reading whole files,
and the reviewer runs `trail check` against `.trail/learnings/`. Learnings hold
code facts only; workflow rules stay in this file, `openspec/config.yaml`, and
`CLAUDE.md`. Changed learnings are reviewed like docs.

**Style** – workflow artifacts, agent reports, and review findings use simple
technical English: short sentences, no filler. Reports are at most 5 lines,
findings at most 6, gate summaries at most 10. The coordinator talks to the
human in the human's language.

Changes that affect packaging or deployment are additionally verified on the
Raspberry Pi from the branch (see the deployment section in the
[README](README.md)).

**Tracks** – the coordinator proposes a track before phase 1 and the human
confirms it. In doubt, take the higher track. If a change turns out to need an
ADR, a dependency, or a migration, it moves up.

| Track | When | Flow | Gates |
|---|---|---|---|
| **Full** | everything that is not small | phases 1–5 above | 1, 2, 3 |
| **Small** | no ADR, no new dependency, no migration, at most about 5 tasks, one side only (backend *or* frontend) | 3 workers: `sonnet` propose + apply in one session (proposal, spec, tasks; no `design.md`), `opus` review (one round, no round 2), `sonnet` fixes + archive + PR | 3; Gate 2 only for a CRITICAL or MAJOR finding |
| **Trivial** | docs, config, typo; at most 2 files; no new behavior; no code under `backend/app` or `frontend/src` | no OpenSpec change, no review: branch, `make check`, PR with `Closes #<issue>`; one `sonnet` worker or the human | 3 |

The Trivial track is the only exception to "one issue, one OpenSpec change".
The Small and Trivial tracks are untried: after the first few issues, check the
workflow logs and move work up a track if the review or CI catches what the
lighter track skipped.

**Local flow (`--local`)** – when the cloud models (`claude`/`codex`) are at
their token limit, run the flow on the local model:
`/agent-workflow:orchestrate-issue <issue> --local`. Every phase -- including
the review -- then runs on `local.model` (`ollama/qwen3.8:27b`, via `opencode`).
Because one weaker local model does both the work and the review, keep
artifacts short (the worker sizes its reads to `local.context_window`, 40000),
do exactly one review round, and let the human at Gate 2 be the safety net.
The Ollama backend must be up first (`local.backend_check`) and the worker runs
at a low `temperature` (~0.1–0.2). Any track up to `local.max_track` may run.
The old "local only on the Small track" restriction is retired; the local flow
is now a first-class track selection, and the per-track contract lives in
[`.claude/workflow.yaml`](.claude/workflow.yaml).

**Archive before merge** – `/opsx:archive` syncs the delta specs into
`openspec/specs/` and moves the change to `openspec/changes/archive/` on the
branch, so `main` never holds a finished-but-unarchived change. The archived
change keeps `review.md` as the record of the review.

**After the merge** – deploy on the Pi with `git pull && docker compose up -d --build`,
then delete the worktree and the branch (locally and on GitHub).

**Retrospective** – the workflow itself is still being tuned. After each
issue, `/agent-workflow:adjust-workflow <issue>` reads the coordinator's `workflow-log.md`,
the review, and the history, proposes small fixes to the workflow files, and
records the approved ones in [`docs/workflow-retros.md`](docs/workflow-retros.md),
each marked *generic* or *project-specific*. Workflow changes go through a PR
like any other change.

## Orchestrating the phases with Orca

A **coordinator** agent (`claude` · `sonnet`) owns one issue. It follows the
`/agent-workflow:orchestrate-issue` skill (agent-workflow plugin): it runs in the
issue's worktree, starts one supervised Orca worker per phase with the model
from the table, checks each result itself instead of trusting the worker's
report, and stops at every gate to ask you. It does not write code. Start it
together with the worktree:

```
orca worktree create --name issue-3-recipe-model --no-parent \
  --reference https://github.com/Cherlan27/recipebook/issues/3 \
  --agent claude --model sonnet --prompt "/agent-workflow:orchestrate-issue 3"
```

Workers share the worktree, so phases never run in parallel. Without a
coordinator, the same phases can be started by hand in the issue worktree, e.g.
`orca agent launch --agent claude --model opus --prompt "/opsx:propose …"`.

## Adapting OpenSpec

The OpenSpec skills and commands in `.claude/` and `.opencode/` are generated
by `openspec init`/`openspec update` and are overwritten on every update — do
not edit them. Project-specific behavior goes into
[`openspec/config.yaml`](openspec/config.yaml): `rules` per artifact
(proposal, specs, design, tasks) and `operations.*.guidance` for apply and
archive. Quote YAML entries that contain `": "` or `" #"` (the rest of the line is dropped as a comment) — otherwise OpenSpec cannot
parse the file and silently ignores all of it. Check with
`openspec instructions tasks --change <name> --json` that the rules arrive.

## Working in parallel

- **Dev server ports are shared.** `make dev` binds `8000` (backend) and `5173`
  (frontend) in every worktree, and CORS only allows `http://localhost:5173`.
  Run dev servers in one worktree at a time; `orca ports --json` shows which
  worktree holds a port. Test suites need no ports and can run anywhere.
- **Each worktree has its own database.** `backend/data/app.db` is git-ignored,
  so schema changes and test data in one worktree do not affect another.
- **Respect issue dependencies.** Issues list what they block and what blocks
  them; do not start blocked work in parallel just because a worktree is cheap.
