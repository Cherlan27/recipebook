# QWEN.md

## Workflow

This repo runs on the **agent-workflow** plugin (OpenSpec + Orca coordination).
See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full contract and
[`.claude/workflow.yaml`](.claude/workflow.yaml) for the per-track rules, models,
and the local (`--local`) flow.

Use the plugin's slash commands for the orchestration workflow:

- Orchestrate an issue end-to-end: `/agent-workflow:orchestrate-issue <issue>` —
  add `--local` to run the whole flow (review included) on the local model when
  the cloud models are at their token limit.
- Review a change against `main`: `/agent-workflow:review-change`.
- Record a workflow retrospective: `/agent-workflow:adjust-workflow <issue>`
  (writes to [`docs/workflow-retros.md`](docs/workflow-retros.md)).

The OpenSpec phases still use the repo's own commands: `/opsx:propose`,
`/opsx:apply`, `/opsx:archive` (see `.claude/commands/opsx/`).
