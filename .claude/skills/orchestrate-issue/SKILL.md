---
name: orchestrate-issue
description: Coordinate one GitHub issue through the OpenSpec phases in CONTRIBUTING.md (propose → apply → review analysis → review fixes → archive & PR) by starting one supervised Orca worker per phase with the prescribed model and stopping at the human gates. Use when asked to coordinate, orchestrate, or drive an issue end to end in this repository.
---

# Orchestrate an issue

You are the **coordinator** for one issue. You start workers, check their
results, and stop at every gate. **You do not write code, specs, or docs.** You
only edit `Decision:` lines in `review.md` and `workflow-log.md`.

Input: the issue number.

Worker mechanics (run, `worker-start`, `check --wait`, ack, release, recovery):
run `orca skills get orchestration` once and follow it.

## Style

- Talk to the human in their language. Be short: a gate summary has at most 10 lines.
- Heartbeat deliveries: ack with one command, answer in one line at most.
- Wait with `--types worker_done,escalation,question`.

## 0. Preconditions

Stop and tell the human if one fails:

- Branch name contains `issue-<n>-` (a `<user>/` prefix added by Orca is fine) and you are in the issue worktree, not the main checkout.
- `gh issue view <n>` is open and has no `refinement needed` label.
- `backend/.venv` and `frontend/node_modules` exist; if not, run `uv sync --directory backend && npm ci --prefix frontend`.
- If the issue or `tasks.md` mentions Docker or a container run, `docker info` must work before phase 2. If not, ask the human to start Docker Desktop.

Then:

```bash
orca orchestration run-create --objective "Issue #<n>: <title>" --json
orca worktree set --worktree active --workspace-status in-progress --comment "phase 1: propose" --json
```

Update the worktree comment at each phase change.

## Track

Before phase 1, pick a track from the issue and CONTRIBUTING.md (*Tracks*), tell
the human in two lines, and let them confirm or change it. In doubt, take the
higher track. If a change turns out to need an ADR, a dependency, or a migration,
stop and move it up.

- **Full**: all phases below.
- **Small**: 3 workers.
  1. `claude` `sonnet`: `/opsx:propose` then `/opsx:apply <c>` in one session. Proposal, spec, and tasks only, no `design.md`. Accept as in phases 1 and 2. If the human wants the local model, split it: sonnet proposes, `opencode` applies.
  2. `claude` `opus`: `/review-change <c>`, one round, no round 2.
  3. `claude` `sonnet`: fix `Decision: fix` findings, then `/opsx:archive <c>`, push, and `gh pr create`. Accept as in phases 4 and 5.
  No Gate 1. Gate 2 only if the review has a CRITICAL or MAJOR finding; otherwise show the recommendations in one line, apply them, and go on. Gate 3 as usual.
- **Trivial**: no OpenSpec change and no review. One `claude` `sonnet` worker (or the human) edits on branch `issue-<n>-<name>`, runs `make check`, and opens the PR with `Closes #<n>`. Accept: `make check` passes and the PR exists. Only Gate 3.

Log the chosen track and every change of it in the workflow log (Trivial: in the PR description).

## Workflow log

Append one line per event to `openspec/changes/<c>/workflow-log.md` (under
`archive/` after phase 5): phase start/end with worker, model, outcome; each
gate decision; each retry, fallback, failed acceptance check, and manual
intervention, each with its reason. Add timestamps.
**Commit the log only at Gate 1, at Gate 2, and before phase 5**, not after
every phase. `/adjust-workflow` reads it.

## Phases

One phase at a time; all workers share the worktree. Start each worker with
`--worktree current` and a self-contained `--spec`: issue, change, the one phase,
and the ending *"Do only this phase. When done, report in at most 5 lines and send worker_done."*
Tell workers to keep artifacts short (see Style in `openspec/config.yaml`).

| Phase | Worker | Spec starts with | Accept when |
|---|---|---|---|
| 1 Propose | `claude` `opus` | `/opsx:propose` + issue goal, acceptance criteria, DoD | all artifacts `done` in `openspec status --change <c> --json`, and `openspec validate <c> --strict` passes |
| ⏸ Gate 1 | human | | approved |
| 2 Apply | `claude` `sonnet`; small change only: `opencode` `ollama/qwen3.8:27b` | `/opsx:apply <c>` (opencode: `/opsx-apply <c>`) | no `- [ ]` in `tasks.md`; `make check` passes |
| 3 Review | `claude` `opus` | `/review-change <c>` | `review.md` has a new round and is committed |
| ⏸ Gate 2 | human | | every finding has a decision |
| 4 Fixes | `claude` `sonnet` | fix the findings with `Decision: fix` | each has `Status: fixed`; `make check` passes **twice in a row** |
| 5 Archive & PR | `claude` `sonnet` | `/opsx:archive <c>`, push, `gh pr create` with `Closes #<n>` | change is under `archive/`; PR exists |
| ⏸ Gate 3 | human | | merge and deploy approved |

Check *Accept when* yourself after each `worker_done`; the report is not proof.
If it fails, send the worker the concrete failure once. If it fails again, ask
the human. Do not create extra workers for tiny leftovers a running worker can fix.

## Gate 1

Summarize in at most 10 lines: what changes, requirement and scenario count,
task groups, ADR yes/no. If the proposal shows the change is smaller or bigger
than the chosen track, say so. Ask: approve? and apply with sonnet or locally
(only for a small change)?

**Local model:** only for a small change. If the human asks for it on a bigger
change, say once that the rules say no, then do it. If the worker has made no
commit and ticked no task after 10 minutes, switch to a sonnet worker with
`/opsx:apply <c>` and a note on what the local attempt left behind. `worker-stop`
cannot close a tab owned by the user: ask the human to close it and wait until
the worktree is quiet before the next worker starts.

## Gate 2

Show findings as a table (ID, severity, location, one line, **recommended
decision**). Ask: "approve the recommendations? exceptions?" Write the answers
to the `Decision:` lines (fix / skip / defer) and commit
`docs: review decisions for <c>`. All skip/defer: go to phase 5. Propose a
follow-up issue for each `defer`.

After phase 4, run **one scoped review round** (phase 3, only the fix commits,
see `review-change`) if a CRITICAL or MAJOR finding was fixed. At most two rounds
in total; after that the human decides.

## Gate 3

Show the PR link and the `make check` result. Only after explicit approval:

```bash
gh pr merge <pr> --merge
```

Deploying to the Raspberry Pi needs its own approval (it restarts a shared service):

```bash
ssh pi 'cd ~/recipebook && git pull --ff-only && docker compose up -d --build'
curl -s -o /dev/null -w "%{http_code}\n" http://192.168.178.101:8090/health
```

## Finish

- Delete the remote branch (`git push origin --delete <branch>`).
- Set the worktree status to `completed` with a final comment.
- Report: PR, merge commit, deploy result, deferred findings, and that the worktree can be removed in Orca (not the one you run in).
- Suggest `/adjust-workflow <n>`.
