# syntax=docker/dockerfile:1

# ---- Frontend build stage -------------------------------------------------
FROM node:22-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ---- Backend runtime stage -------------------------------------------------
FROM python:3.12-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /usr/local/bin/

WORKDIR /app/backend

# Install dependencies in their own layer so they stay cached across
# source-only changes.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY backend/app ./app
RUN uv sync --locked --no-dev

COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

RUN useradd --create-home --uid 1000 --user-group appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

USER appuser

ENV RECIPEBOOK_DATABASE_PATH=/app/data/app.db \
    PATH="/app/backend/.venv/bin:${PATH}"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=2).status == 200 else 1)"

CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
