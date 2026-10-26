# Review: recipe-data-model

## Round 1

Base `origin/main` @ 2599a2c · Head bbfca34 · 2026-10-26 · Reviewer: claude-opus-5-5

### Summary

The change introduces Alembic migrations that run in a worker thread from `init_db()` at every start, a pre-migration file copy `<name>.bak-<revision>`, and the first revision with `recipes`, `tags` (casefolded `name_key`), and `recipe_tags` (composite PK, `ON DELETE CASCADE`). It follows the design and ADR-8 closely. Every scenario in both delta specs has a test that would fail without the implementation, the tests run against the real migrated schema (drift test included), all tasks are done, and `make check` passes. The migrated schema has correctly named constraints (`ck_recipes_kid_friendly`, `uq_tags_name_key`, `fk_recipe_tags_*`), and no `Dockerfile`/compose change is needed (migrations ship inside `app/`, `.dockerignore` excludes nothing relevant, Alembic/Mako are pure Python for arm64). The weak spot is the backup safety net, and it matters because `docker-compose.yml` has `restart: unless-stopped`, so a failed start is retried automatically with no human involved. Two realistic paths leave a migration running without a usable copy: a partially written copy (R1) and the documented rollback followed by a redeploy (R2). The remaining findings concern observability and restore guidance on the Pi, tag normalization, and test strength.

### Verification

| `make check` step | Result |
|---|---|
| `uv run pytest` | ✅ 45 passed (1 warning: Starlette `httpx` deprecation, already on `main`) |
| `npm test` | ✅ 1 passed |
| `npm run build` | ✅ |
| `openspec validate --all --strict` | ✅ 3 passed |

Extra probes, run as throwaway scripts (since deleted) against this branch's code:

- A copy that fails after writing part of the file (simulated `ENOSPC`), followed by a second start: the second start migrates `r1 → r2`, and `a.db.bak-r1` is 100 bytes ("database disk image is malformed").
- Rollback as documented in the README (copy `bak-r1` back over `app.db`), then 5 new rows, then a redeploy: `bak-r1` still has 0 rows and the database has 5. No copy of the new rows was made before the migration ran.
- Failing fixture (`r1` ok, `r2` raises) started twice on an existing empty file: the database is stamped `r1` after the first failure, and the second start adds `a.db.bak-r1` next to `a.db.bak-base`.
- `run_migrations()` under `uvicorn.config.LOGGING_CONFIG` prints nothing, even though a `bak-base` copy was written and the schema was upgraded.
- The NFC and NFD forms of `"Österreichisch"` are both accepted as separate tags. `"Maße"` and `"Masse"` collide.
- Appending a tag to a stored recipe and committing leaves `updated_at` unchanged.
- `test_updated_at_advances_when_recipe_is_changed` was run 25 times on Windows/Python 3.12 with no failures (clock resolution about 0.5 ms), so it is not flaky.

### Findings

#### R1 · MAJOR · `backend/app/db/migrate.py:69-74`

**A failed or interrupted backup copy leaves a truncated file behind, and the next start skips the backup because of it.** `shutil.copy2` writes straight to the final name `<name>.bak-<revision>`. If it fails part-way, the partial file stays: a full SD card (`ENOSPC`) on the Pi, an I/O error, or the container being killed or losing power during the copy. `BackupError` correctly aborts the first start. But `restart: unless-stopped` (`docker-compose.yml:13`) restarts the container within seconds. On that second start `backup_path.exists()` is true, so the backup is skipped and `command.upgrade` runs with only a corrupt copy in place. The probe above reproduces this: the database reached head, and the "backup" was 100 bytes and unreadable. This is the data-loss case the copy exists to prevent. The copy is also not `fsync`ed before the migration starts changing `app.db`, so a power cut on the Pi during the migration can leave both files damaged.

Suggested fix: copy to a temporary name in the same directory (e.g. `<name>.bak-<revision>.partial`), `fsync` it, then `os.replace` it onto the final name, and delete the temporary file on failure. Only a complete copy ever has the final name, so the "never overwrite" rule (D5) stays as it is. Add a test where `copy2` writes part of the file and then raises, followed by a successful second run that must leave a byte-identical copy.

- Decision: fix
- Status: fixed

#### R2 · MAJOR · `backend/app/db/migrate.py:69-70`, `README.md:133-136`

**After the documented rollback, the next deploy migrates without copying the data entered since the rollback.** The rule "an existing copy is never overwritten" (spec *A backup copy with the same name already exists*, D5) protects against a half-migrated file replacing the good copy. It does not account for the restore procedure in the README, ADR-8, and arc42 §11: "replace `data/app.db` with the matching `data/app.db.bak-<revision>` … start the previous release". After a copy-based restore, `app.db.bak-<revision>` is still there. The household keeps entering recipes on the previous release. The fixed release is then deployed and runs the migration that failed last time, and the backup is skipped because the name is taken. The probe confirms it: the copy holds 0 rows and the database 5. So the riskiest moment, retrying a migration that already failed once, is exactly when no current copy is made.

This needs a human decision because the spec mandates the skip. Options:
- (a) Change the restore instructions (README, ADR-8 Consequences, arc42 §11) to *move* the copy out of the way after restoring, e.g. rename it to `app.db.bak-<revision>.restored`, so the name is free for the next deploy. Smallest change.
- (b) When a copy with the name exists, write an additional timestamped copy unless the existing one is byte-identical to the current file. This protects the data even if the procedure is not followed. Requires a spec and design update, and has to avoid writing a new copy on every crash-loop restart (see R4).

Whichever option is chosen, also log a warning naming the existing copy when the backup is skipped (see R3).

- Decision: fix (option a: change restore instructions to rename the old copy after restoring, plus the warning log from R3)
- Status: fixed

#### R3 · MINOR · `backend/app/db/migrate.py:55-57`, `backend/app/db/migrations/env.py:12-15`

**Successful migrations and backup copies leave no trace in `docker compose logs`.** `env.py` rightly skips `fileConfig` under Uvicorn, but Uvicorn only configures its own `uvicorn.*` loggers. Alembic's INFO lines ("Running upgrade … -> aee96801fd95") therefore go nowhere, and `migrate.py` logs nothing itself (probe: no output). On the Pi the operator cannot tell from the logs whether a migration ran, from which revision, or which backup file was written or skipped. That information is needed to pick the right copy (R4) and to notice R1/R2. The Gate 3 check can only confirm that there was "no migration error" in the logs. Suggested fix: log at WARNING or INFO through a logger that reaches the console (e.g. `uvicorn.error`, or a module logger with a handler) for: current revision → head, backup written (path), backup skipped because one exists (path).

- Decision: fix
- Status: fixed

#### R4 · MINOR · `README.md:133-136`, `docs/adr/0008-alembic-migrations-at-startup.md` (Consequences)

**"Restore the matching copy" is ambiguous once a release contains more than one revision.** Alembic commits each revision separately on SQLite, so a failure in revision N+2 leaves the database stamped at N+1, possibly with part of N+2's DDL already applied. The automatic restart then writes `app.db.bak-<N+1>` from that partly migrated file, next to the real pre-deploy copy `app.db.bak-<N>`. The fixture probe shows the same thing with `bak-base` plus `bak-r1`. An operator choosing "the matching" or the newest copy restores the wrong state. Today there is only one revision, so this is guidance for the future, but the README is the operational runbook for the Pi. Suggested wording: restore the copy named after the revision of the release you go back to, i.e. the oldest copy written by the failed deployment. Name where the operator can look that revision up (the release's newest file in `app/db/migrations/versions/`, or `SELECT version_num FROM alembic_version` on the copy).

- Decision: fix
- Status: fixed

#### R5 · MINOR · `backend/app/models/tag.py:28-33`

**The tag key is not Unicode-normalized, so visually identical tags can coexist.** `name.strip().casefold()` without normalization treats `"Österreichisch"` in NFC (`Ö` = U+00D6) and NFD (`O` + U+0308) as different (probe: both stored). NFD text comes from macOS input and from copy-paste out of PDFs and web pages, which is plausible when typing in paper recipes. The spec explicitly promises case-insensitive uniqueness for umlauts. Suggested fix: `unicodedata.normalize("NFC", value.strip())` for `name`, and the same normalization before `casefold()` for `name_key`, plus a parametrized test case. Doing it now is cheap. Once tags exist, changing the key needs a data migration and duplicate resolution. Related decision for the human: `casefold()` maps `ß` to `ss`, so `"Maße"` and `"Masse"` collide. That goes beyond "regardless of letter case" in the spec. Either accept it explicitly (design D8) or use `lower()` after NFC normalization.

- Decision: fix (NFC-normalise name and name_key; keep casefold(), ß and ss are deliberately the same tag; document in design D8)
- Status: fixed

#### R6 · MINOR · `backend/app/models/recipe.py:55-61`

**`updated_at` does not change when only a recipe's tags change.** `onupdate=utcnow` fires only when a column of `recipes` changes. Adding or removing a tag writes only `recipe_tags`, so `updated_at` stays the same (probe confirmed). The requirement says `updated_at` is updated "whenever a stored recipe is changed through the application", and in #8/#9 editing tags will be a normal recipe edit. There is no scenario or test for it. Either decide that tag changes do not count (and state it in the spec or design), or deliberately leave it to the recipe API in #9 to touch `updated_at` on tag edits, and record that in the design so #9 does not miss it.

- Decision: defer
- Status: open

#### R7 · MINOR · `backend/app/db/migrations/env.py:22-25`

**Foreign keys being off during migrations depends on an implicit default that no test checks, and orphaned links would go unnoticed.** The safety argument in D7 (batch mode must not cascade-delete `recipe_tags`) depends on the migration connection having `foreign_keys` off. The code gets that only from SQLite's compile-time default (`SQLITE_DEFAULT_FOREIGN_KEYS=0`) and from the listener being attached to the application engine only. A future change, such as a global `Engine` `connect` listener or a SQLite build with a different default, would silently turn on the cascade. Because enforcement is off, a faulty future migration can also leave dangling `recipe_tags` rows, and later application connections do not check existing rows. Suggested fix: run `PRAGMA foreign_keys=OFF` explicitly on the migration connection before the transaction starts. After the upgrade, run `PRAGMA foreign_key_check` and fail startup (or at least log) if it returns rows. Add a test that asserts `PRAGMA foreign_keys` is `0` inside the migration connection.

- Decision: fix
- Status: fixed

#### R8 · MINOR · `backend/tests/test_recipe_model.py:160-166`

**The creation-timestamp test checks neither "time of creation" nor UTC.** `test_timestamps_are_set_on_creation` only asserts `created_at is not None` and `updated_at == created_at`. It would still pass if `utcnow()` returned local time or a constant. The requirement states "Timestamps SHALL be recorded in UTC" and the scenario says "set to the time of creation". Suggested fix: take `datetime.now(UTC).replace(tzinfo=None)` before and after the commit and assert `before <= created_at <= after`. On a CET machine, local time would then fail the test.

- Decision: fix
- Status: fixed

### Nits

- N1 · `backend/app/db/migrate.py:62-64` — three blank lines between `run_migrations` and `backup_before_upgrade` (PEP 8: two).
- N2 · `backend/app/models/tag.py:21` — `name_key` is a public mapped attribute, so `Tag(name="Pasta", name_key="x")` overrides the derived key because constructor kwargs are applied in order. Harmless today, but the API in #8/#9 should never pass it. Consider a comment or setting it only in the validator.
- N3 · `openspec/changes/recipe-data-model/proposal.md` (Deployment) and README — the first Pi start leaves `app.db.bak-base`, a copy of the empty #2 database. Once the copy-retention rules from R2 are settled, mention that this file can be deleted right after the Gate 3 check.
