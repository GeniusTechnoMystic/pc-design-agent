# PC Design Agent

A source-grounded PC recommendation and compatibility system for component selection, workload-aware optimization, Linux and firmware visibility, lifecycle analysis, and New Zealand / Australia pricing intelligence.

This repository is intentionally structured around a canonical data model, strict provenance, and deterministic compatibility logic rather than ad hoc inference. The goal is to help evaluate hardware with evidence, not just model guesses.

---

## Quickstart — target audience: technical users and automation (AI)

This section gives the minimal steps to get a local, self-hosted instance running for development or testing. For production, follow the Production considerations section below.

Prerequisites

- Git (clone the repo)
- Docker & Docker Compose (recommended for reproducible local stacks)
- Python 3.10+ and pip
- PostgreSQL 14+ (or run via Docker Compose)
- Optional: MinIO or S3-compatible object storage, Redis (for job queue), and an SMTP server for alerts

Clone

```bash
git clone https://github.com/GeniusTechnoMystic/pc-design-agent.git
cd pc-design-agent
```

Local environment (recommended)

1. Create a .env file from the example

```bash
cp .env.example .env
# edit .env to set DB credentials, object storage endpoint, and secret keys
```

2. Start local services with Docker Compose (Postgres + MinIO skeleton)

```yaml
# (example snippet; save as docker-compose.dev.yml)
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: pcagent
      POSTGRES_PASSWORD: pcagent
      POSTGRES_DB: pcagent
    ports:
      - '5432:5432'
    volumes:
      - db-data:/var/lib/postgresql/data

  minio:
    image: minio/minio
    command: server /data
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio123
    ports:
      - '9000:9000'
    volumes:
      - minio-data:/data

volumes:
  db-data:
  minio-data:
```

```bash
docker compose -f docker-compose.dev.yml up -d
```

3. Create and activate a virtual environment, install Python deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

4. Apply database migrations or create schema (project currently uses SQL DDL drafts)

- If this repo contains migrations (e.g. Alembic), run them. If not, run the provided schema SQLs when available (check `schemas/`).

Example (Alembic):

```bash
alembic upgrade head
```

If no migration framework is present yet, refer to `docs/component-database-data-structures.md` for DDL drafts and run them manually against your Postgres instance.

5. Copy seed data into data/raw/

Place any local benchmark files or JSONL captures in `data/raw/` as a starting point. The repository's `PROGRESS.md` and `ROADMAP.md` indicate the intended seed data.

6. Run an example scraper (linux compatibility)

```bash
cd linux-compat
python linux_hardware_scraper.py --category gpu-nvidia --max-devices 10 --output-dir ../data/raw
```

This will produce JSONL files that you can use as initial raw inputs.

7. Run ingestion/normalization adapters

Adapters live in `scraper/`, `search/`, or `engine/adapters` depending on implementation. Examples:

```bash
python scraper/adapter_linux_hardware_db.py --input data/raw/gpu_nvidia.jsonl --output data/staging/gpu_nvidia.ndjson
```

8. Run entity resolution and reconciliation (high-level)

These are in `src/entity_resolution/` and `src/reconciliation/` once implemented. For now, run scripts under `engine/` or `src/` that implement resolution.

9. Start the recommendation engine / API

Run the engine server if present (e.g. Flask/FastAPI uvicorn command):

```bash
uvicorn engine.api:app --reload --host 0.0.0.0 --port 8000
```

If the engine is not implemented yet, see `docs/design-document.md` for the intended API surface and scoring contracts.

10. Run tests and linters

```bash
pytest -q
ruff check .
black . --check
```

---

## Production considerations (self-hosting)

1. Services to deploy

- PostgreSQL (managed or self-hosted)
- Object storage (S3, MinIO)
- Redis or RabbitMQ for job queues (if used)
- Background worker(s) for scrapers and ingestion
- Web/API service (FastAPI / Flask / Gunicorn / Uvicorn)
- Optional: scheduler (cron, Airflow, or Prefect) for periodic ingest

2. Secrets & configuration

- Use environment variables via your platform’s secret store or HashiCorp Vault.
- Do not commit .env files with production secrets.
- Use database credentials with least privilege.

3. Observability

- Export metrics (Prometheus) from the engine and background workers
- Centralize logs (ELK / Loki / Grafana)
- Add alerts for failed ingestion, high error rates, and stalled jobs

4. Scaling

- The ingestion layer is parallelizable — run multiple workers for adapters
- Use batch imports for marketplace crawls and paginated sources
- Scale the database vertically for joins; add read replicas if read-heavy

5. Data lifecycle

- Keep raw imports immutable in `data/raw/` and record retrieval metadata
- Use `data/staging/` for normalized payloads and `data/curated/` for reconciled, authoritative outputs
- Implement retention policies for raw captures as required by storage costs

---

## Configuration reference

Create a `.env` or platform config with the following variables (example):

```
# Database
DATABASE_URL=postgresql://pcagent:pcagent@localhost:5432/pcagent

# Object storage
STORAGE_ENDPOINT=http://localhost:9000
STORAGE_ACCESS_KEY=minio
STORAGE_SECRET_KEY=minio123
STORAGE_BUCKET=pc-agent

# App
SECRET_KEY=replace-with-secure-random
ENV=development

# Scraper behavior
SCRAPER_REQUEST_DELAY=1.5
SCRAPER_USER_AGENT=pc-design-agent/1.0
```

Add a `.env.example` file with the above keys and placeholder values so automation or an AI can populate them.

---

## Automation and AI agent integration

This repository is intentionally agent-friendly. Conventions and artifacts to help automation include:

- Root status files (`PROGRESS.md`, `STREAMS.md`, `ROADMAP.md`) provide a compact control surface an agent can read and act on.
- `.agents/` contains roles, rules, skills, and workflows for reproducible operations.
- `schemas/` define machine-readable contracts for adapters and reconciliation outputs — automation should validate inputs against these schemas.
- Provide `scripts/` (or `make` targets) for common tasks: `scripts/ingest.sh`, `scripts/run-local.sh`, `scripts/bootstrap-db.sh` so an AI can call them predictably.

Recommended simple make targets (put in `Makefile`):

```make
.PHONY: init db-start deps migrate seed run

init:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

db-start:
	docker compose -f docker-compose.dev.yml up -d

migrate:
	alembic upgrade head

seed:
	python scripts/seed_data.py --dir data/raw

run:
	uvicorn engine.api:app --reload
```

An AI operator can call these steps in order to bootstrap a working environment.

---

## Security and ethics

- Respect robots.txt and rate limits when scraping (the linux-compat scraper supports delay and dry-run modes).
- Do not store or publish scraped private data. This project collects only publicly available information.
- Be mindful of target sites’ terms of service.

---

## Tests, CI, and quality gates

- Add unit tests under `tests/` for adapters, entity resolution, and scoring logic.
- Use GitHub Actions to run tests, linters, and build checks on PRs.
- Add IaC and deployment checks if you include Terraform or Kubernetes manifests.

Suggested GitHub Actions matrix:

- Python test matrix (3.10, 3.11)
- Lint (ruff), format check (black --check), type check (mypy) if used
- Build + smoke test for Docker image

---

## Contributing

- Read `PROGRESS.md`, `STREAMS.md`, `ARCHITECT.md`, and `ROADMAP.md` to understand active streams and next steps.
- Open small PRs, reference the relevant stream and PROGRESS.md status updates.
- Include source URLs and provenance when adding facts or data.
- For major schema changes, add migration plans and coordinate reproducible data transformations.

---

## Useful links in this repository

- `docs/design-document.md` — full system design and source strategy
- `docs/component-database-data-structures.md` — data model and DDL guidance
- `PROGRESS.md`, `STREAMS.md`, `ROADMAP.md`, `ARCHITECT.md` — operational control surface
- `.agents/` — agent operating rules and workflows
- `linux-compat/` — scraper and Linux hardware capture code

---

If you want, I can now:

- Add a `docker-compose.dev.yml` and `.env.example` file to the repo
- Create a Makefile with the suggested targets and simple scripts for bootstrap
- Add a GitHub Actions workflow to run tests and linters

Tell me which of those you want me to create and I’ll add them in separate commits.
