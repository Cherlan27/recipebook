---
name: review-change
description: Review the current branch's OpenSpec change before it is archived and merged — spec conformance, test evidence, project rules, correctness, security, and deployment impact — and write numbered findings to openspec/changes/<change>/review.md. Use for phase 3 (review analysis) in CONTRIBUTING.md, or when asked to review a branch, change, or PR in this repository. Does not modify code.
---

# Review a change

You are the reviewer, not the author. Find the problems that matter before merge,
prove each one, and record them so a human can decide. **Do not modify source,
tests, specs, or docs.** The only file you write is `review.md`.

Input: optional base ref (default `origin/main`), optional change name, and the
round number (round 2 is scoped, see below).

Style: simple technical English, short sentences. No filler.

## 1. Scope

```bash
git fetch -q origin
git log --oneline origin/main...HEAD
git diff --stat origin/main...HEAD
```

Find the active change under `openspec/changes/` (not `archive/`) or use the name
you were given. Without a change, review the diff, skip spec checks, and report
in chat instead of writing `review.md`.

**Round 2 is scoped:** review only the commits made since round 1
(`git diff <round-1-head>..HEAD`). First check that each `Status: fixed` finding is
really resolved (re-run its probe). Then look for new problems in the fix diff and
in docs changed with it. Do not re-read the whole change and do not re-raise
`defer`red or skipped findings.

## 2. Understand the intent

Read in this order, and only what you need: `CLAUDE.md`, `openspec/config.yaml`;
the change (`proposal.md`, `tasks.md`, delta specs, and `design.md` for decisions
you question); the issue named in `Closes #<n>` (`gh issue view <n>`); ADRs the
change adds.

## 3. Read the code

Read the diff first. Read a whole file only where you suspect a problem or the
hunk lacks context. Read the tests for changed behavior and callers of changed
signatures.

## 4. Verify

```bash
make check
```

A failure is CRITICAL; quote the relevant output.

## 5. Checklist

**A. Spec and tests (most important)**
- Every scenario is implemented and has a test that fails without the implementation. Name the test. A scenario without one is MAJOR.
- Nothing is built that no spec, task, or design decision asks for.
- Every ticked task is really done. A false tick is MAJOR.
- Acceptance criteria and DoD of the issue are covered or explicitly deferred.

**B. Project rules**
- Architecture decision: ADR "Accepted" plus matching `docs/arc42/adoc/` updates.
- English artifacts and comments. Backend layering as in `CLAUDE.md`. Frontend uses `<script setup lang="ts">`.
- New dependencies justified; lock files updated.

**C. Correctness**
- Logic, edge cases, wrong assumptions. Boundary errors handled; no swallowed exceptions.
- Async: no blocking I/O in async paths.
- Database: constraints the specs imply; every schema change has a migration that works on a database with data.
- Tests must not be flaky: no equality between two clock reads, no sleeps for ordering.

**D. Security**: injection, path traversal, unsafe file handling, secrets, widened CORS, missing auth.

**E. Deployment**: breaking API/config/schema changes; `Dockerfile` and `docker-compose.yml` still build for `linux/amd64` and `linux/arm64`; persistent data is on the mounted volume; new env vars are in the README.

**F. Leftovers**: debug output, commented-out code, unused imports, TODOs without an issue.

## 6. Verify before you report

Go back to the code for each candidate. Drop it if you cannot name file and line,
if the design or an ADR records it as intentional, or if it is only taste.
State assumptions.

Severity:
- **CRITICAL**: failing verification, data loss, security hole, contradicts a spec.
- **MAJOR**: scenario without implementation or test, false tick, violated project rule, likely bug in a realistic case.
- **MINOR**: worth fixing, does not block merge. **Report a MINOR only with a concrete failure scenario** ("when X, then Y"). Otherwise drop it.
- **Nits**: at most 3, and only if they cost nothing to fix. Nits get no decision line.

## 7. Write `review.md`

If the file exists, append `## Round <n>`; never overwrite. Keep it short: the
summary has at most 3 sentences, each finding at most 6 lines (what is wrong,
the failure, the fix). Probe scripts go in one line each, not as long tables.

```markdown
# Review: <change-name>

## Round 1

Base `origin/main` @ <sha> · Head <sha> · <YYYY-MM-DD> · Reviewer: <model>

### Summary
<= 3 sentences.

### Verification
| step | result |
|---|---|
| `make check` | ✅ <counts> |

### Findings

#### R1 · MAJOR · `path:line`
What is wrong, when it fails, suggested fix. If the fix needs a human choice, list the options.

- Recommendation: fix | skip | defer — <short reason>
- Decision: pending
- Status: open

### Nits
- N1 · `path:line` — note.
```

Number findings `R1`, `R2`, … across rounds. Give every finding a
`Recommendation:` (default for MINOR without data or safety impact: skip or defer).
The human sets `Decision:` at Gate 2; the fixer sets `Status:`.
Commit only `review.md` as `docs: review round <n> of <change-name>`.

## 8. Report

At most 5 lines: counts per severity, IDs of CRITICAL and MAJOR findings, path of `review.md`.
