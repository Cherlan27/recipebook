# 3. Defer introducing Pinia

Date: 2026-08-15

## Status

Accepted

## Context

Pinia is Vue 3's official state management library (successor to Vuex), providing a central store for state shared across multiple components. The project scaffold (Issue #1) only needs a `/health` check on the frontend side — there is no cross-component state to manage yet.

## Decision

Do not add Pinia in Issue #1. Introduce it only once a feature has a concrete need for state shared across multiple components — most likely the recipe list/detail views.

## Consequences

- Avoids an unused abstraction and dependency in the scaffold.
- The first feature issue that needs shared frontend state (e.g. recipe list) will need to add and wire up Pinia as part of its own scope, not as a scaffold task.
- If it turns out most components only need local state or simple prop/emit passing, Pinia may end up not being needed at all.
