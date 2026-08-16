# Recipebook

A recipe management app with a FastAPI backend and a Vue 3 frontend.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python dependency management)
- [Node.js](https://nodejs.org/) 18+ with npm
- `make` — on Windows, install via Git Bash/MinGW (not available natively; see [docs/arc42/adoc/11_technical_risks.adoc](docs/arc42/adoc/11_technical_risks.adoc))

## Local Setup

```
git clone <repo-url>
cd recipebook
```

## Running Backend and Frontend

Start both together:

```
make dev
```

Or start them individually:

```
make backend   # equivalent to: cd backend && uv run uvicorn app.main:app --reload
make frontend  # equivalent to: cd frontend && npm run dev
```

The backend runs at `http://localhost:8000` (health check at `/health`), the frontend dev server at `http://localhost:5173`.

## Running Tests

```
cd backend && uv run pytest
cd frontend && npm test
```

## Documentation

- Architecture: [docs/arc42/arc42-template.adoc](docs/arc42/arc42-template.adoc)
- Architecture Decision Records: [docs/adr](docs/adr)
