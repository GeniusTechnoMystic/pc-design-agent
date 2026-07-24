# Planned Next Jobs

## Immediate

- Copy imported Space files into `data/raw/` and preserve import provenance.
- Create example payloads for the three current JSON schemas.
- Draft SQL DDL for entities, facts, relationships, and offers.
- Open the first GitHub issues from `docs/issues/initial-issues.md`.

## After that

- Build parser stubs for local CSV and XLSX imports.
- Add compatibility-edge and price-offer schemas.
- Define a gold test dataset for 20 to 50 parts.
- Decide the first execution environment for data processing.

## Open loops

- Need a final decision on PostgreSQL-only first pass versus adding a graph layer early.
- Need a first explicit field list for lifecycle and repairability records.
- Need to choose whether Trade Me and AU marketplace collection should start as browser-assisted workflows or coded adapters.
