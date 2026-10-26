# Workflow retrospectives

Changes to the development workflow (see [CONTRIBUTING.md](../CONTRIBUTING.md)),
one entry per retrospective, written by `/adjust-workflow`. *Scope* marks
whether a change is generic (a candidate for a shared workflow plugin) or
specific to this repository.

## 2026-10-26 · Issue #3 · recipe-data-model

Evidence: `workflow-log.md`, `review.md` (2 rounds), 36 commits, PR #11.
Wall time from first commit to PR was about 78 minutes. About 43 minutes of it
were avoidable: local-model attempt 17 min, second review round with fixes 12 min,
flaky-test follow-up 9 min, separate Docker worker 5 min (times from commit
times, approximate). 11 of 36 commits were log commits. Round 1 found two real
MAJOR data-safety problems; round 2 found no MAJOR.

| # | Change | File | Scope | Status |
|---|---|---|---|---|
| A1 | Style rule: simple technical English, reports ≤5 lines, findings ≤6, gate summaries ≤10 | `openspec/config.yaml`, `CONTRIBUTING.md`, `CLAUDE.md`, skills | generic | applied |
| A2 | Review round 2 is scoped to the fix commits, not a full re-review | `review-change`, `orchestrate-issue`, `CONTRIBUTING.md` | generic | applied |
| A3 | Findings: `Recommendation:` line, MINOR only with a concrete failure, ≤3 nits, gate = "approve recommendations?" | `review-change`, `orchestrate-issue` | generic | applied |
| A4 | Local model only for small changes; switch to sonnet after 10 min without commit or tick; closing a user-owned tab is a human step | `orchestrate-issue`, `CONTRIBUTING.md` | generic | applied |
| A5 | Check `docker info` before apply when tasks need Docker; apply worker does the container check itself | `orchestrate-issue`, `openspec/config.yaml` | project | applied |
| A6 | Deterministic tests rule; `make check` twice in a row after apply and fixes | `openspec/config.yaml`, `review-change`, `CONTRIBUTING.md`, `CLAUDE.md` | generic | applied |
| A7 | Commit `workflow-log.md` only at Gate 1, Gate 2, and before phase 5 | `orchestrate-issue` | generic | applied |
| A8 | Heartbeats: ack with one command, one-line answer; wait only for `worker_done,escalation,question` | `orchestrate-issue` | generic | applied |
| A9 | Leaner artifacts: short design (decisions only), one task per behavior instead of RED and GREEN tasks, proposal under one page | `openspec/config.yaml` | generic | applied |
| A10 | Shorter skill and `CLAUDE.md` workflow text (loaded into every worker) | `orchestrate-issue`, `review-change`, `CLAUDE.md` | generic | applied |
| A11 | Lower `--effort` for sonnet apply/fix workers | `orchestrate-issue` | generic | proposed, not applied: no evidence yet that quality holds; try on one issue and compare |
| A12 | Drop the coordinator's own `make check` after each phase | `orchestrate-issue` | generic | rejected: it caught the flaky test in phase 4 |
| A13 | Fix the proposal rule in `config.yaml`: `"Closes #1"` hid the rest of the line as a YAML comment, so the rule reached agents cut off. Quote such entries | `openspec/config.yaml`, `CONTRIBUTING.md` | generic | applied |
