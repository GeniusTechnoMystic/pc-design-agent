# PC Design Agent

A source-grounded PC recommendation and compatibility system for component selection, workload-aware optimization, Linux and firmware visibility, lifecycle analysis, and New Zealand / Australia pricing intelligence.

This repository is intentionally structured around a canonical data model, strict provenance, and deterministic compatibility logic rather than ad hoc inference. The goal is to help evaluate hardware with evidence, not just model guesses.

## Why this project exists

Building a good PC recommendation engine is not just a product selection problem. It is a data-quality, compatibility, and evidence problem.

This project is designed to:

- model CPU, GPU, motherboard, RAM, storage, PSU, chassis, and peripheral compatibility with explicit rules
- score recommendations against workload profiles such as gaming, Linux workstation, homelab virtualization, AI inference, and storage-heavy builds
- keep Linux compatibility, firmware openness, lifecycle risk, and repairability visible in every recommendation
- compare NZ and AU retail pricing as well as used-market pricing with landed-cost awareness
- preserve source provenance for every material fact and recommendation

## Mission

Build and operate a source-grounded PC design agent that models component compatibility, workload-aware optimization, Linux and firmware support, lifecycle awareness, and NZ/AU retail and used pricing.

## Core principles

The repository follows a disciplined operating model:

- Treat the canonical data layer as the system of record.
- Preserve provenance for every important fact.
- Prefer deterministic compatibility logic over ad hoc inference.
- Use the model for orchestration, trade-off explanation, and missing-data detection.
- Keep firmware openness, Linux support, repairability, and lifecycle visible in recommendations.
- Prefer small, testable increments over broad speculative rewrites.

## Repository architecture

The repository is organized to separate planning, data pipelines, source documents, and operating guidance:

- `docs/` — design docs, plan reviews, architecture notes, and implementation guidance
- `data/` — raw, staging, and curated datasets with clear lifecycle boundaries
- `schemas/` — contracts for source facts, entity records, and recommendation outputs
- `engine/` — recommendation and compatibility logic when implemented
- `scraper/` and related source adapters — ingestion paths for external data sources
- `linux-compat/` — Linux hardware compatibility data collection and normalization
- `.agents/` — reusable operating rules, roles, workflows, and best practices
- root-level status files (`PROGRESS.md`, `STREAMS.md`, `ARCHITECT.md`, `ROADMAP.md`) — project state and handoff context

## Canonical design

The project is designed around a hybrid architecture:

- PostgreSQL-first canonical data store for products, facts, pricing, compatibility, firmware, and lifecycle metadata
- graph-style relationship modeling for compatibility and dependency traversal
- provenance-first source ingestion from vendor pages, benchmark datasets, Linux hardware sources, and marketplace listings
- recommendation logic that separates hard constraints from soft heuristics
- evidence-backed outputs with source links, confidence, caveats, and landed NZD-cost awareness

## Key technical goals

### Compatibility and recommendations

The system must reason about:

- socket, chipset, memory, PCIe, storage, and PSU compatibility
- physical fit and tower clearance
- BIOS/firmware support floors and upgrade constraints
- Linux driver coverage, Wi-Fi, audio, and network support
- workload alignment across gaming, workstation, home lab, inference, and storage scenarios

### Data quality and provenance

Every important claim should include:

- source name and source URL
- retrieval timestamp
- extraction method
- confidence score
- effective date
- raw capture reference
- superseded-by linkage when newer facts replace older ones

### Pricing and lifecycle intelligence

The system is designed to account for:

- NZ and AU retail pricing
- used-market price discovery
- shipping and landed-cost normalization
- performance-per-dollar and value comparisons
- maintainability, repairability, and component lifecycle indicators

## Source strategy

This project explicitly prefers trustworthy, source-grounded evidence over opaque model guesses. Source priorities include:

- vendor product pages and official manuals
- Linux compatibility and firmware support databases
- benchmark aggregators and public hardware tracking datasets
- NZ/AU marketplace feeds and used-market listings
- raw local benchmark data captured for initial validation and model bootstrapping

Important source references already reflected in the project include:

- linux-hardware.org
- hw-probe
- coreboot/coreboot
- fwupd / LVFS
- PassMark CPU and GPU benchmark datasets
- Trade Me and AU used-market listing ecosystems

## Repository conventions

The repository intentionally follows a durable operating model for agentic work:

- `docs/` for design docs, plans, reviews, and architecture decisions
- `.agents/rules/` for mandatory operating rules
- `.agents/skills/` for reusable procedures
- `.agents/roles/` for role-specific guidance
- `.agents/workflows/` for multi-step execution flows
- `.agents/best-practices/` for shared implementation patterns

This helps keep the project maintainable even as it evolves from architecture to implementation.

## Initial operating loop

The intended execution loop is simple and deterministic:

1. Read root-level status files and identify the active stream.
2. Ingest or update source data.
3. Resolve entities and reconcile facts.
4. Validate compatibility rules and derived metrics.
5. Run recommendation or comparison workflows.
6. Record caveats, missing data, next improvements, and status-file updates.

## Current project status

This repository is currently in its foundational phase. Based on the project status files, the work is focused on establishing the data ingestion baseline, schema contracts, and canonical entity structures before building the recommendation engine itself.

Status summary:

- foundations and execution primitives are in place
- local data ingestion and schema examples are the immediate next implementation priority
- SQL DDL, compatibility edges, and pricing normalization remain active design work
- marketplace ingestion strategy is still intentionally conservative and exploratory

## Recommended contribution standards

To keep this repository healthy and maintainable, contributions should follow these patterns:

- prefer explicit schema and provenance changes over undocumented assumptions
- keep data transformations auditable and traceable
- write small, reviewable changes
- annotate uncertain or conflicting facts rather than hiding them
- separate source ingestion, normalization, reconciliation, and recommendation logic
- prefer deterministic compatibility checks over inferred “best guess” behavior
- document source URLs and evidence trails in research-heavy artifacts

## Roadmap orientation

The project roadmap centers on progressive maturity:

- M1: status and execution control surface
- M2: local data ingestion baseline
- M3: canonical database baseline
- M4: CPU and GPU proof-of-concept
- M5: marketplace ingestion decision and pilot

This sequence reflects the project’s emphasis on correctness and provenance before scaling into shopping and recommendation automation.

## Things to expect from the project

This repository is best understood as a foundation for a serious PC recommendation engine and hardware intelligence layer. It is not a thin “build my PC” prototype; it aims to become a source-grounded system that can explain why a build is valid, where it is risky, and how its value compares to alternatives.

## Contributing

Contributions should match the repository’s architectural and operating expectations:

- start from the active status files and current stream
- keep design work in `docs/`
- keep reusable operating guidance in `.agents/`
- preserve source provenance and track caveats
- prefer evidence-backed changes over speculative shortcuts

## Notes

This repository is structured to support “trustworthy recommendations” rather than “plausible suggestions.” That distinction is central to the project’s purpose.

The project is intentionally careful about uncertainty, missing data, and sourcing quality. Where facts conflict, the right answer is to preserve the ambiguity and show the evidence, not to silently collapse it.

## Summary

The PC Design Agent is a disciplined, source-first platform for building a more reliable PC recommendation system. It aims to merge compatibility logic, Linux/firmware awareness, lifecycle signals, and NZ/AU pricing into a model that can provide transparent, evidence-based guidance rather than black-box recommendations.

If you are contributing here, the guiding pattern is clear: document the evidence, normalize the facts, validate the compatibility rules, and explain the trade-offs.

---

Project status and architecture notes are tracked in:

- `PROGRESS.md`
- `STREAMS.md`
- `ARCHITECT.md`
- `ROADMAP.md`

These files are the canonical operational surface for this repository.
