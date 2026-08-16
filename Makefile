.PHONY: backend frontend dev

backend:
	cd backend && uv run uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

dev:
	$(MAKE) -j2 backend frontend
