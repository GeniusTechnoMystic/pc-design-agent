# STREAMS.md

## Stream S1: Repository foundations

- Objective: establish project structure, docs, schemas, and agent operating rules
- Status: paused
- Dependencies: none
- Current next step: none
- Handoff: foundations are stable; continue in data ingestion and database-definition streams

## Stream S2: Data ingestion foundations

- Objective: prepare raw, staging, and schema contracts for benchmark and pricing ingestion
- Status: next
- Dependencies: S1
- Current next step: copy local datasets into `data/raw/` and add schema examples
- Handoff: begin with local files before adding remote parsers

## Stream S3: Recommendation engine foundations

- Objective: define SQL structures, compatibility edges, and recommendation payloads
- Status: queued
- Dependencies: S2
- Current next step: draft SQL DDL and add missing schemas after schema examples are in place
- Handoff: start with CPU and GPU proof-of-concept entities and offers

## Stream S4: Marketplace pricing strategy

- Objective: decide how Trade Me and AU source ingestion should be executed
- Status: queued
- Dependencies: S1
- Current next step: compare browser-assisted collection versus coded adapters versus hybrid mode
- Handoff: record the decision in `ARCHITECT.md` and update roadmap dependencies

## Handoff notes

- Root-level status files are now the fast context surface.
- The broad design remains in `docs/`, but active execution state now lives in `PROGRESS.md`, `STREAMS.md`, and `ROADMAP.md`.
- The project is paused to control token spend.
- The highest-value next implementation work is raw dataset import, schema examples, SQL DDL, and parser foundations.
