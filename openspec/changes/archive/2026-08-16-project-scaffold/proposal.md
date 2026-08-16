## Why

GitHub Issue #1 ("Projekt-Grundgerüst") verlangt ein lauffähiges Grundgerüst mit Backend (FastAPI), Frontend (Vue.js) und Datenbank-Anbindung (SQLite), damit alle weiteren Recipebook-Features darauf aufbauen können. Aktuell besteht das Repository nur aus README, `.git` und `openspec` — es gibt noch keinen Code, kein Tooling und keinen dokumentierten Startablauf.

Closes #1

## What Changes

- Monorepo-Struktur mit `backend/` (FastAPI) und `frontend/` (Vue 3) anlegen
- Backend: FastAPI-App mit geschichteter Struktur (`app/api/routes`, `app/core`, `app/db`, `app/models`), Dependency-Management über `uv`/`pyproject.toml`
- Backend: SQLAlchemy 2.0 async (Treiber `aiosqlite`) mit echter Engine/Session gegen `backend/data/app.db`; Verzeichnis wird beim Start automatisch angelegt, `data/` ist git-ignored mit `.gitkeep`
- Backend: CORS für die Frontend-Dev-Origin `http://localhost:5173` aktivieren
- Backend: `GET /health` liefert `200 OK`, automatisiert getestet via `pytest` + FastAPI `TestClient`
- Frontend: Vue 3 + TypeScript + Composition API (`<script setup>`) über Vite-Scaffold; kein State-Management-Layer (Pinia bewusst zurückgestellt, bis ein Feature echten geteilten State braucht)
- Frontend: Vitest als Test-Framework eingerichtet (Vite-nativ, siehe ADR-5)
- Root: `Makefile` mit Targets `backend`, `frontend` (einzeln starten) und `dev` (beide parallel starten)
- README um lokale Setup-Anleitung und beide Start-Kommandos erweitern

## Capabilities

### New Capabilities
- `health-check`: Backend-API stellt einen `GET /health`-Endpunkt bereit, der `200 OK` liefert, und ist per CORS für die Frontend-Dev-Origin erreichbar

### Modified Capabilities
- (keine — Greenfield-Projekt, keine bestehenden Specs)

## Impact

- Neues Repository-Layout (`backend/`, `frontend/`, root-`Makefile`)
- Neue Backend-Abhängigkeiten: `fastapi`, `sqlalchemy[asyncio]`, `aiosqlite`, `uvicorn`, `pytest`, `httpx`
- Neue Frontend-Abhängigkeiten: `vue`, `typescript`, `vite`, `vitest`
- README wird um Setup-/Start-Anleitung erweitert
- Keine bestehenden Systeme betroffen (erstes Issue im Projekt, keine Abhängigkeiten laut Issue #1)
