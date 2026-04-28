# Review of Next Implementation Pass

## Completed in this pass

- Added formal JSON schemas for entity candidates, source facts, and recommendation outputs.
- Added canonical data-model guidance and a current source map.
- Added data-layer layout and an import manifest for local Space datasets.
- Added a staging plan for initial benchmark and pricing imports.
- Added a benchmark-and-pricing proof-of-concept plan for CPU and GPU data.
- Added issue drafts and created live GitHub issues for the first execution backlog.

## What changed structurally

New top-level directories:

- `schemas/`
- `data/`
- `docs/architecture/`
- `docs/issues/`
- `docs/sources/`

## Strengths

- The repository now has explicit machine-readable contracts for ingestion and recommendation payloads.
- The data layer now has a clear separation between raw, staging, and curated zones.
- The backlog has been converted from notes into live GitHub issues.
- Source assumptions are now documented with URLs and stated limitations.

## Open loops

### 1. Raw file copy is still pending

The import manifest points to the existing Space files, but the files have not yet been copied into `data/raw/`.

### 2. Example payloads are still missing

The schemas exist, but example JSON payloads should be added next to make adapter implementation faster and reduce ambiguity.

### 3. SQL DDL is still missing

The canonical model is documented, but the first SQL tables or migrations have not yet been written.

### 4. Compatibility-edge and offer schemas are still missing

The current schema set is enough to start, but compatibility edges, retail offers, shipping quotes, lifecycle, and repairability still need their own contracts.

### 5. Data-collection mode for marketplaces is unresolved

A decision is still needed on whether Trade Me and AU marketplace collection should begin with browser-assisted workflows, coded adapters, or a hybrid approach.

### 6. Graph timing is unresolved

The project still needs a decision on PostgreSQL-only first versus adding graph capabilities early.

## Recommendation

The next pass should focus on execution primitives rather than more planning. The best order is:

1. Copy the local Space datasets into `data/raw/`
2. Add example payloads for all current schemas
3. Draft SQL DDL for entities, facts, relationships, and offers
4. Add parser stubs for CSV and XLSX imports
5. Add compatibility-edge and price-offer schemas

## Outcome

This pass successfully converted the project from a design-only repo into a structured execution repo with schema contracts, source planning, and an actionable backlog.
