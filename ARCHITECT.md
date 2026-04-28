# ARCHITECT.md

## Mission

Build a source-grounded PC design agent that models component compatibility, workload-aware optimization, Linux support, firmware openness, lifecycle signals, repairability, and NZ/AU retail and used pricing.

## System shape

- Canonical data layer in PostgreSQL-first form
- Graph-style relationship model for compatibility and dependency traversal
- Provenance-first ingestion from specs, pricing sources, benchmark sites, Linux compatibility databases, and firmware ecosystems
- Recommendation layer that separates hard constraints from soft heuristics
- Evidence-backed outputs with source links, confidence, caveats, and landed NZD cost views

## Repo structure

- `docs/` for design, plans, reviews, sources, and architecture notes
- `schemas/` for machine-readable contracts
- `data/raw/` for immutable imported source artifacts
- `data/staging/` for normalized intermediate data
- `data/curated/` for validated and reconciled outputs
- `.agents/` for reusable agent operating guidance

## Architectural rules

- Canonical facts require provenance.
- Hard compatibility rules should be deterministic.
- Linux support, firmware openness, lifecycle, and repairability must remain visible in recommendation outputs.
- Marketplace pricing should be normalized to landed NZD where practical.
- Preserve ambiguity rather than invent false precision.

## Current decisions

- Start PostgreSQL-first, with graph capability deferred until query complexity justifies it.
- Treat local Space benchmark files as seed datasets.
- Use root-level status files as the fast-load project context surface.

## Current unresolved decisions

- Exact marketplace ingestion mode for Trade Me and AU sources
- First lifecycle and repairability field set
- First SQL DDL layout for entities, facts, edges, offers, and listings
