---
name: adjust-workflow
description: Retrospective after an issue has run through the workflow in CONTRIBUTING.md. Collects evidence of friction (failed or repeated phases, manual interventions, recurring review findings, ignored rules), proposes the smallest concrete edits to the workflow files, labels each as generic or project-specific, applies the ones the human approves, and records them in docs/workflow-retros.md. Use after /orchestrate-issue finishes, or when asked to sharpen, tune, or adjust the workflow.
---

# Adjust the workflow

The workflow is young. Every issue that runs through it is a test of it. Your
job is to turn what happened into small, approved improvements, and to keep a
record of which improvements are generic (they belong in a future shared
workflow plugin) and which are specific to this repository.

Input: the issue number or change name. Optional: the human's own notes.

## 1. Gather evidence

Look for the change under `openspec/changes/` or `openspec/changes/archive/`, then read:

- `workflow-log.md` — the coordinator's log of gates, retries, fallbacks, and manual interventions.
- `review.md` — every round, with severities and decisions.
- `tasks.md` — how the work was cut, and whether ticks were honest.
- `git log --oneline` of the branch or merge — fix-up commits, reverts, how many review rounds.
- `orca orchestration worker-list --include-remote --json` for the run, if it still exists — failed or retried dispatches.
- The PR and its CI runs (`gh pr view <n> --json statusCheckRollup,comments`).

Then ask the human one question: *what was annoying, slow, or surprising?*
Their answer outweighs anything you infer.

## 2. Find the friction

Look for patterns, not one-off accidents:

- A phase that failed, stalled, or had to be repeated, and why.
- A gate where the human had to supply information the workflow should have produced.
- Review findings of the same kind (e.g. "scenario without test") — a rule upstream should prevent them.
- A rule that was ignored or misunderstood — it is unclear or in the wrong place.
- A step that added cost without catching anything — a candidate to drop or shrink.
- A model that did not fit its phase (the local model failed; opus was overkill; sonnet missed something).

## 3. Propose changes

For every friction point, propose the **smallest** change that would have
prevented it, as a table:

| # | Friction (evidence) | Change | File | Scope |
|---|---|---|---|---|
| A1 | R3 and R5 were both "scenario without test" (review.md) | Tasks rule: test task must name the test file | `openspec/config.yaml` | generic |

Files you may change: `CONTRIBUTING.md`, the Workflow section of `CLAUDE.md`,
`openspec/config.yaml` (rules and guidance), `Makefile` (`check`),
`.github/`, and the skills `orchestrate-issue`, `review-change`, and
`adjust-workflow` in `.claude/skills/`. Never edit generated OpenSpec commands
in `.claude/commands/` or `.opencode/`.

**Scope:** *generic* if it would help any repository using this workflow,
*project* if it depends on this repository's stack, deployment, or domain.

Do not propose weakening a safeguard (`make check`, a gate, the reviewer's
independence, archive before merge) unless the evidence shows it cost more than
it caught — and then say so explicitly.

## 4. Apply what the human approves

Ask which changes to apply. Apply only those, keep edits minimal, and verify:

- `openspec/config.yaml` still parses and its rules arrive (`openspec instructions tasks --change <any> --json` on a scratch change, then delete it).
- `make check` still passes.

## 5. Record

Append an entry to `docs/workflow-retros.md` (create it if missing):

```markdown
## <YYYY-MM-DD> · Issue #<n> · <change-name>

| # | Change | File | Scope | Status |
|---|---|---|---|---|
| A1 | … | `openspec/config.yaml` | generic | applied |
| A2 | … | `CONTRIBUTING.md` | project | rejected — <reason> |
```

Commit everything on a branch `workflow/retro-<n>` with
`docs: workflow retro for #<n>` and open a PR — workflow changes go through
review like any other change.
