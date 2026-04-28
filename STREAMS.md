# STREAMS.md

## Stream S1: Repository foundations

- Objective: establish project structure, docs, schemas, and agent operating rules
- Status: active
- Dependencies: none
- Current next step: finalize root-level status protocol files and handoff rules
- Handoff: once status protocol files are in place, shift focus to raw data import and schema examples

## Stream S2: Data ingestion foundations

- Objective: prepare raw, staging, and schema contracts for benchmark and pricing ingestion
- Status: queued
- Dependencies: S1
- Current next step: copy local datasets into `data/raw/` and add schema examples
- Handoff: begin with local files before adding remote parsers

## Stream S3: Recommendation engine foundations

- Objective: define SQL structures, compatibility edges, and recommendation payloads
- Status: queued
- Dependencies: S2
- Current next step: draft SQL DDL and add missing schemas
- Handoff: start with CPU and GPU proof-of-concept entities and offers

## Stream S4: Marketplace pricing strategy

- Objective: decide how Trade Me and AU source ingestion should be executed
- Status: queued
- Dependencies: S1
- Current next step: compare browser-assisted collection versus coded adapters versus hybrid mode
- Handoff: record the decision in `ARCHITECT.md` and update roadmap dependencies

## Handoff notes

- Root-level status files are becoming the fast context surface.
- The broad design remains in `docs/`, but active execution state should now live in `PROGRESS.md`, `STREAMS.md`, and `ROADMAP.md`.
- The highest-value next implementation work is still raw dataset import plus SQL and parser foundations.
