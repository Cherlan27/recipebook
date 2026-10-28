---
title: The workflow plugin is enabled in the project settings because Orca workers do not load plugins themselves
author: Lukas
date: 2026-10-28
branch: workflow/enable-plugin
cost: { minutes: 1, tokens: 1373 }
id: l-b92df63a
scope: repo
status: active
src: agent
---

## Decided
The agent-workflow plugin is enabled at project scope, with its marketplace listed, so every session and every Orca worker in a recipebook worktree gets the /agent-workflow:* skills. Orca starts workers as plain `claude --dangerously-skip-permissions`, without plugin options, so a worker only sees plugins that Claude Code itself has enabled.

## Watch out
Claude Code installs the plugin from the marketplace's default branch, not the version recipebook's workflow.yaml was written for. Stacked plugin PRs can leave that branch behind: if the lower PR is squash-merged first, the upper PR merges only into the old base branch and the release never reaches the default branch. After a plugin release, check that the bumped version is on the default branch before relying on it here.

In the code:
- .claude/settings.json: `enabledPlugins` and `extraKnownMarketplaces`
- .claude/workflow.yaml: the contract the plugin version must support
- installed version: `installed_plugins.json` under ~/.claude/plugins, entry `agent-workflow@agent-workflow`
- update: `/plugin marketplace update agent-workflow`, then `/plugin update agent-workflow@agent-workflow`
