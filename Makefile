.PHONY: backend frontend dev install test lint demo

# Backend
backend:
	cd backend && .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend  
frontend:
	cd frontend && npm run dev

# Run both concurrently
dev:
	@echo "Starting GENESIS..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@make backend & make frontend

# Install all dependencies
install:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
	cd frontend && npm install

# Run all tests
test:
	cd backend && .venv/bin/python -m pytest -v

# Lint & format
lint:
	cd backend && .venv/bin/ruff check app/ tests/ && .venv/bin/ruff format --check app/ tests/
	cd frontend && npx tsc --noEmit

# Quick demo test via curl
demo:
	curl -s -X POST http://localhost:8000/api/demo | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'✓ {d[\"total_variants\"]} variants, {d[\"total_claims\"]} claims, {d[\"supported_claims\"]} supported, {len(d[\"conflicts\"])} conflicts')"
