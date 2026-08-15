# 2. Use the Composition API instead of the Options API

Date: 2026-08-15

## Status

Accepted

## Context

The frontend (Issue #1, project scaffold) is set up with Vue 3 and TypeScript. Vue 3 supports two styles for structuring component logic: the classic Options API (`data`, `methods`, `computed`, ... as object fields) and the newer Composition API (`ref`, `reactive`, `computed`, ... composed inside `<script setup>`).

## Decision

Write Vue components with the Composition API, using `<script setup lang="ts">`.

## Consequences

- Component logic is grouped by feature/concern rather than by option type, which scales better as components grow.
- Significantly better TypeScript type inference than the Options API.
- Reusable logic can be extracted into composables (e.g. a future `useRecipes()`), instead of mixins.
- Contributors need to be familiar with the Composition API style; this is the current Vue 3 default and recommended approach, so onboarding cost is low.
