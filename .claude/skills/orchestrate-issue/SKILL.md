---
name: orchestrate-issue
description: Coordinate one GitHub issue through the OpenSpec phases in CONTRIBUTING.md (propose → apply → review analysis → review fixes → archive & ship) by starting one supervised Orca worker per phase with the prescribed model and stopping at the human gates. Use when asked to coordinate, orchestrate, or drive an issue end to end in this repository.
---

# Orchestrate an issue

You are the **coordinator** for one issue. You start workers, check their
results, keep the human informed, and stop at every gate. **You do not write
code, specs, or docs yourself** — the only files you edit are the `Decision:`
lines in `review.md` at Gate 2.

Input: the issue number.

For the mechanics of supervised workers (run, `worker-start`, `check --wait`,
acknowledging deliveries, releasing workers, recovery), follow the Orca
orchestration guide: run `orca skills get orchestration` once and obey it. This
skill only decides *which* worker runs *when*.

## 0. Preconditions

Stop and tell the human if any of these fails:

- You are in a worktree for this issue, not the main checkout: `git branch --show-current` is `issue-<n>-…`.
- `gh issue view <n>` is open and not labelled `refinement needed`.
- Dependencies are installed (`backend/.venv` and `frontend/node_modules` exist); otherwise run `uv sync --directory backend && npm ci --prefix frontend`.

Then create the run and mark the worktree:

```bash
orca orchestration run-create --objective "Issue #<n>: <title>" --json
orca worktree set --worktree active --workspace-status in-progress --comment "phase 1: propose" --json
```

Update the comment at every phase change.

**Keep a workflow log.** Once the change directory exists, append one line per
event to `openspec/changes/<c>/workflow-log.md` (after phase 5 the directory is
under `archive/`): phase start and end with worker, model, and outcome; every
gate with the human's decision; every retry, fallback, or failed acceptance
check with its reason; every manual intervention. Commit it with the phase it
belongs to. `/adjust-workflow` uses this log to improve the workflow.

## Phases

Phases run strictly one after another; all workers share this worktree. Start
each worker with `--worktree current` and a self-contained `--spec` that names
the issue, the change, the single phase to do, and ends with: *"Do only this
phase. When done, report what you did and send worker_done."*

| Phase | Worker | Spec starts with | Accept when |
|---|---|---|---|
| 1 Propose | `--agent claude --model opus` | `/opsx:propose` + the issue's goal, acceptance criteria, DoD | `openspec status --change <c> --json` shows every artifact `done` and `openspec validate <c> --strict` passes |
| ⏸ Gate 1 | human | — | human approves |
| 2 Apply | `--agent claude --model sonnet`, or for a small change `--agent opencode --model ollama/qwen3.8:27b` | `/opsx:apply <c>` (opencode: `/opsx-apply <c>`) | no `- [ ]` left in `tasks.md` and `make check` passes |
| 3 Review analysis | `--agent claude --model opus` | `/review-change <c>` | `review.md` has a new round and is committed |
| ⏸ Gate 2 | human | — | every finding has a decision |
| 4 Review fixes | `--agent claude --model sonnet` | implement the findings of `review.md` with `Decision: fix` | each of them has `Status: fixed` and `make check` passes |
| 5 Archive & PR | `--agent claude --model sonnet` | `/opsx:archive <c>`, push, `gh pr create` with `Closes #<n>` | the change is under `openspec/changes/archive/` and the PR exists |
| ⏸ Gate 3 | human | — | human approves merge and deploy |

Check the *Accept when* column yourself after every `worker_done`; a worker's
own report is not proof. If it fails, send the worker the concrete failure once;
if it fails again, stop and ask the human.

## Gate 1 — after propose

Summarize for the human: what the change does, the requirements and scenario
count, the task groups, whether an ADR was written. Then assess **small
change** against CONTRIBUTING.md: no ADR, no new dependency, no database
migration, at most about five tasks, one side only. Ask:

- approve, or which changes to make (then start a new propose worker with the feedback), and
- apply locally (only if small) or with sonnet.

**Local fallback:** if the opencode worker fails, stalls, or leaves `make check`
failing, do not retry locally. Start a sonnet apply worker with
`/opsx:apply <c>` and a note on what the local attempt left behind.

## Gate 2 — after review analysis

Show the findings as a table (ID, severity, location, one-line summary) and ask
for a decision per finding: **fix**, **skip**, or **defer**. Write the answers
into the `Decision:` lines of `review.md`, commit with
`docs: review decisions for <c>`, then start phase 4. If every finding is
skipped or deferred, go straight to phase 5. For each `defer`, propose a
follow-up issue to the human.

After phase 4, run another review round (phase 3 again) only if a CRITICAL or
MAJOR finding was fixed. At most two review rounds; after that, hand the
decision to the human.

## Gate 3 — merge and deploy

Show the PR link and the final `make check` result. Only after explicit
approval:

```bash
gh pr merge <pr> --merge
```

Deployment to the Raspberry Pi also needs explicit approval, because it
restarts a service other people use:

```bash
ssh pi 'cd ~/recipebook && git pull --ff-only && docker compose up -d --build'
curl -s -o /dev/null -w "%{http_code}\n" http://192.168.178.101:8090/health
```

## Finish

- Delete the remote branch (`git push origin --delete <branch>`).
- Set the worktree status to `completed` with a final comment.
- Report to the human: PR, merge commit, deploy result, deferred findings or
  follow-up issues, and that the worktree can be removed from Orca. Do not
  remove the worktree you are running in.
- Suggest running `/adjust-workflow <n>` while the run is fresh.
