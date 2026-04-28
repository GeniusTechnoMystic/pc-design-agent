# PROGRESS.md

## Current milestone

Milestone: Foundations and execution primitives

## Completed

- [x] Created private repository and initial docs
- [x] Added `AGENTS.md` and `.agents/` operating files
- [x] Added design document, project plan, review notes, and next-task docs
- [x] Added source map and canonical data-model notes
- [x] Added first JSON schemas for entity candidates, source facts, and recommendation outputs
- [x] Created raw import manifest and staging plan
- [x] Created initial GitHub issues for schema, ingestion, and scoring
- [x] Added status protocol integration design

## Active

- [>] Start the local data ingestion baseline
- [>] Prepare schema examples and SQL foundations

## Queued

- [ ] Copy local Space datasets into `data/raw/`
- [ ] Add example payloads for current schemas
- [ ] Draft SQL DDL for entities, facts, edges, offers, and listings
- [ ] Add parser stubs for CSV and XLSX imports
- [ ] Add compatibility-edge and price-offer schemas
- [ ] Decide first marketplace ingestion mode

## Success criteria

- [x] Root-level status files provide a compact project control surface
- [x] Agents can identify current milestone, active loops, blockers, and next steps without reading the full docs tree
- [x] The next implementation pass can begin from `PROGRESS.md`, `STREAMS.md`, and `ROADMAP.md`

## Blockers and open loops

- Raw dataset copy into `data/raw/` is still pending
- Example schema payloads are still missing
- SQL DDL has not yet been drafted
- Marketplace ingestion mode is still undecided
- Lifecycle and repairability field definitions are still incomplete

## Immediate next actions

1. Copy local Space datasets into `data/raw/`
2. Add example payloads for the current schemas
3. Draft SQL DDL for entities, facts, edges, offers, and listings
