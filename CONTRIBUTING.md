# Contributing

How changes are made in this repository, by humans and by coding agents alike.

The project-wide rules (English for all artifacts, Test-Driven Development, an
accepted ADR plus updated arc42 docs before any architecture decision) live in
[`openspec/config.yaml`](openspec/config.yaml) and are summarized in
[`CLAUDE.md`](CLAUDE.md). This document describes the workflow around them.

## One issue, one change, one branch

Every piece of work starts from a GitHub issue and maps one-to-one onto:

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
| 2 | **Apply** | `/opsx:apply`, task by task, red → green → refactor, one commit per task group, until `make check` passes. | `claude` · `sonnet`; small changes: `opencode` · `ollama/qwen3.8:27b` (`/opsx-apply`) |
| 3 | **Review analysis** | `/review-change` (`.claude/skills/review-change/`): checks the branch against `main` for spec conformance, test evidence, project rules, correctness, security, and deployment impact. Writes numbered findings to `openspec/changes/<change>/review.md`, changes no code. | `claude` · `opus` |
| | ⏸ **Gate 2** | A human selects which findings to fix. | human |
| 4 | **Review fixes** | Implements the selected findings (TDD where behavior changes), marks each one `Status: fixed` in `review.md`, re-runs `make check`. A second review round follows only if a CRITICAL or MAJOR finding was fixed; at most two rounds. | `claude` · `sonnet` |
| 5 | **Archive & PR** | `/opsx:archive` on the branch, PR against `main` with `Closes #<issue>`. | `claude` · `sonnet` |
| | ⏸ **Gate 3** | A human approves the merge (merge commit) and the deployment to the Pi; then branch and worktree are cleaned up. | human |

**Verification** – `make check` runs the backend tests, the frontend tests,
the type-checked frontend build, and `openspec validate --all --strict`. It
must pass at the end of phases 2 and 4, and GitHub Actions runs it on every
pull request (`.github/workflows/check.yml`).

Changes that affect packaging or deployment are additionally verified on the
Raspberry Pi from the branch (see the deployment section in the
[README](README.md)).

**Small change** – the local model may apply a change only if *all* of these
hold: no architecture decision (no ADR), no new dependency, no database
migration, at most about five tasks, and only one side (backend *or*
frontend) is touched. If its run leaves verification failing, the apply is
handed to `sonnet` instead of retried locally.

**Archive before merge** – `/opsx:archive` syncs the delta specs into
`openspec/specs/` and moves the change to `openspec/changes/archive/` on the
branch, so `main` never holds a finished-but-unarchived change. The archived
change keeps `review.md` as the record of the review.

**After the merge** – deploy on the Pi with `git pull && docker compose up -d --build`,
then delete the worktree and the branch (locally and on GitHub).

**Retrospective** – the workflow itself is still being tuned. After each
issue, `/adjust-workflow <issue>` reads the coordinator's `workflow-log.md`,
the review, and the history, proposes small fixes to the workflow files, and
records the approved ones in [`docs/workflow-retros.md`](docs/workflow-retros.md),
each marked *generic* or *project-specific*. Workflow changes go through a PR
like any other change.

## Orchestrating the phases with Orca

A **coordinator** agent (`claude` · `sonnet`) owns one issue. It follows the
`/orchestrate-issue` skill (`.claude/skills/orchestrate-issue/`): it runs in the
issue's worktree, starts one supervised Orca worker per phase with the model
from the table, checks each result itself instead of trusting the worker's
report, and stops at every gate to ask you. It does not write code. Start it
together with the worktree:

```
orca worktree create --name issue-3-recipe-model --no-parent \
  --reference https://github.com/Cherlan27/recipebook/issues/3 \
  --agent claude --model sonnet --prompt "/orchestrate-issue 3"
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
archive. Quote YAML entries that contain `": "` — otherwise OpenSpec cannot
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
