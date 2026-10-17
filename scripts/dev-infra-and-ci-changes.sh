#!/usr/bin/env bash
# create-files.sh
# Create dev infra files, scripts, Makefile, CI config, and commit to the current branch.
# Usage: run from repository root. Ensure you're on branch "dev-infra-and-ci".
set -euo pipefail

BRANCH="dev-infra-and-ci"

# Ensure we're on the correct branch
current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [ "$current_branch" != "$BRANCH" ]; then
  echo "Switching to branch $BRANCH"
  git checkout -b "$BRANCH"
fi

echo "Creating files..."

cat > docker-compose.dev.yml <<'YAML'
version: '3.8'
services:
  db:
    image: postgres:15
    container_name: pc-design-agent-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-pcagent}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-pcagent}
      POSTGRES_DB: ${POSTGRES_DB:-pcagent}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-pcagent} -d ${POSTGRES_DB:-pcagent}"]
      interval: 10s
      timeout: 5s
      retries: 10

  minio:
    image: minio/minio:RELEASE.2025-02-28T09-55-16Z
    container_name: pc-design-agent-minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minio}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minio123}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio-data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 10

volumes:
  pgdata:
  minio-data:
YAML

cat > .env.example <<'ENV'
# Database
DATABASE_URL=postgresql://pcagent:pcagent@localhost:5432/pcagent
POSTGRES_USER=pcagent
POSTGRES_PASSWORD=pcagent
POSTGRES_DB=pcagent

# Object storage
STORAGE_ENDPOINT=http://localhost:9000
STORAGE_ACCESS_KEY=minio
STORAGE_SECRET_KEY=minio123
STORAGE_BUCKET=pc-agent

# App
SECRET_KEY=replace-with-secure-random-value
ENV=development

# Scrapers
SCRAPER_REQUEST_DELAY=1.5
SCRAPER_USER_AGENT=pc-design-agent/1.0

# Optional runtime tuning
APP_HOST=0.0.0.0
APP_PORT=8000
ENV

cat > Makefile <<'MAKE'
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
MAKE

mkdir -p scripts

cat > scripts/bootstrap-db.sh <<'BASH'
#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

DB_URL="${DATABASE_URL:-postgresql://pcagent:pcagent@localhost:5432/pcagent}"

if ! command -v psql >/dev/null 2>&1; then
  echo "psql is required but not installed. Please install PostgreSQL client tools."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but not installed."
  exit 1
fi

DB_NAME="$(python3 - <<'PY'
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL', 'postgresql://pcagent:pcagent@localhost:5432/pcagent')
parsed = urlparse(url)
print(parsed.path.lstrip('/'))
PY
)"

DB_HOST="$(python3 - <<'PY'
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL', 'postgresql://pcagent:pcagent@localhost:5432/pcagent')
parsed = urlparse(url)
print(parsed.hostname or 'localhost')
PY
)"

DB_USER="$(python3 - <<'PY'
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL', 'postgresql://pcagent:pcagent@localhost:5432/pcagent')
parsed = urlparse(url)
print(parsed.username or 'pcagent')
PY
)"

DB_PASS="$(python3 - <<'PY'
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL', 'postgresql://pcagent:pcagent@localhost:5432/pcagent')
parsed = urlparse(url)
print(parsed.password or 'pcagent')
PY
)"

DB_PORT="$(python3 - <<'PY'
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL', 'postgresql://pcagent:pcagent@localhost:5432/pcagent')
parsed = urlparse(url)
print(parsed.port or 5432)
PY
)"

PGPASSWORD="$DB_PASS" export PGPASSWORD

echo "Checking database connectivity at ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; do
  echo "Postgres not ready yet; retrying in 2 seconds..."
  sleep 2
done

echo "Ensuring database '${DB_NAME}' exists..."
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" | grep -q 1; then
  createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
fi

if [ -d schemas ] && find schemas -maxdepth 1 -type f -name '*.sql' | grep -q .; then
  echo "Found SQL schema files. Running entrypoint scripts if available..."
  for sql_file in schemas/*.sql; do
    echo "Applying ${sql_file}"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$sql_file"
  done
else
  echo "No SQL schema files were found under schemas/."
  echo "This project is still in design / bootstrap phase. The database is initialized and ready for the next schema or migration pass."
fi

echo "Database bootstrap complete."
BASH

chmod +x scripts/bootstrap-db.sh

cat > scripts/seed_data.py <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SEED_FILE = RAW_DIR / "seed_sample_components.jsonl"

SAMPLE_RECORDS = [
    {
        "source": "seed",
        "category": "cpu",
        "vendor": "AMD",
        "model": "Ryzen 7 7800X3D",
        "socket": "AM5",
        "tdp_watts": 120,
        "core_count": 8,
        "thread_count": 16,
        "market": "global",
        "provenance": {
            "source_name": "seed_sample",
            "source_url": "https://example.invalid/seed/cpu/ryzen-7-7800x3d",
            "confidence_score": 0.9,
        },
    },
    {
        "source": "seed",
        "category": "gpu",
        "vendor": "NVIDIA",
        "model": "GeForce RTX 4070 Super",
        "gpu_arch": "AD104",
        "tdp_watts": 220,
        "vram_gb": 12,
        "market": "global",
        "provenance": {
            "source_name": "seed_sample",
            "source_url": "https://example.invalid/seed/gpu/rtx-4070-super",
            "confidence_score": 0.9,
        },
    },
    {
        "source": "seed",
        "category": "motherboard",
        "vendor": "MSI",
        "model": "B650 Tomahawk WiFi",
        "socket": "AM5",
        "chipset": "B650",
        "form_factor": "ATX",
        "market": "global",
        "provenance": {
            "source_name": "seed_sample",
            "source_url": "https://example.invalid/seed/motherboard/b650-tomahawk-wifi",
            "confidence_score": 0.85,
        },
    },
]

if SEED_FILE.exists():
    existing = SEED_FILE.read_text(encoding="utf-8").strip().splitlines()
    if existing:
        print(f"Seed file already exists at {SEED_FILE}. Skipping regeneration.")
        raise SystemExit(0)

with SEED_FILE.open("w", encoding="utf-8") as fh:
    for record in SAMPLE_RECORDS:
        fh.write(json.dumps(record, separators=(",", ":")) + "\n")

print(f"Created seed data at {SEED_FILE}")
PY

chmod +x scripts/seed_data.py

mkdir -p .github/workflows
cat > .github/workflows/ci.yml <<'YML'
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Lint
        run: |
          ruff check .
          black --check .

      - name: Test
        run: pytest -q
YML

cat > requirements.txt <<'REQ'
fastapi
uvicorn[standard]
psycopg[binary]
sqlalchemy
alembic
boto3
requests
beautifulsoup4
pytest
ruff
black
REQ

# Git add, commit, push
git add docker-compose.dev.yml .env.example Makefile scripts .github/workflows/ci.yml requirements.txt

git commit -m "Add dev infra: docker-compose, .env.example, Makefile, bootstrap & seed scripts, CI config, requirements" || {
  echo "No changes to commit or commit failed."
}

echo "Pushing branch $BRANCH to origin..."
git push --set-upstream origin "$BRANCH"

echo "Done. Branch '$BRANCH' pushed with files."
