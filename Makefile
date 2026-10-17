.PHONY: install up down bootstrap migrate seed run test lint ci help

PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTHON_BIN := $(VENV)/bin/python

install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt

up:
	docker compose -f docker-compose.dev.yml up -d

down:
	docker compose -f docker-compose.dev.yml down -v

bootstrap: up
	@echo "Waiting for Postgres and MinIO to become healthy..."
	@bash scripts/bootstrap-db.sh
	@$(PYTHON_BIN) scripts/seed_data.py

migrate:
	@if command -v alembic >/dev/null 2>&1; then \
		$(VENV)/bin/alembic upgrade head; \
	else \
		echo "Alembic not installed in the current environment; install requirements first."; \
	fi

seed:
	$(PYTHON_BIN) scripts/seed_data.py

run:
	$(PYTHON_BIN) -m uvicorn engine.api:app --reload --host 0.0.0.0 --port 8000

lint:
	$(PYTHON_BIN) -m ruff check .
	$(PYTHON_BIN) -m black --check .

test:
	$(PYTHON_BIN) -m pytest -q

ci: lint test

help:
	@echo "Available targets:"
	@echo "  install     Create a venv and install project dependencies"
	@echo "  up          Start local Postgres and MinIO services"
	@echo "  down        Stop and remove local dev services"
	@echo "  bootstrap   Start services, initialize DB, seed raw data"
	@echo "  migrate     Run database migrations if Alembic is configured"
	@echo "  seed        Seed raw/example data"
	@echo "  run         Start the API or engine"
	@echo "  test        Run the project test suite"
	@echo "  lint        Run formatter and linting checks"
