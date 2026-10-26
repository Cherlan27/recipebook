.PHONY: backend frontend dev check

backend:
	cd backend && uv run uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

dev:
	$(MAKE) -j2 backend frontend

# Everything a change must pass before review and merge (see CONTRIBUTING.md).
check:
	cd backend && uv run pytest
	cd frontend && npm test
	cd frontend && npm run build
	openspec validate --all --strict --no-interactive
