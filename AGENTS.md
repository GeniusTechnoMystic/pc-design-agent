# AGENTS.md

## Mission

Build and operate a source-grounded PC design agent that models component compatibility, workload-aware optimization, Linux and firmware support, lifecycle awareness, and NZ/AU retail and used pricing.

## Core principles

- Treat the canonical data layer as the system of record.
- Preserve provenance for every important fact.
- Prefer deterministic compatibility logic over ad hoc model inference.
- Use the language model for orchestration, trade-off explanation, and missing-data detection.
- Keep open firmware, Linux support, repairability, and lifecycle visible in recommendations.
- Prefer small, testable increments.

## Required outputs

- Read `PROGRESS.md`, `STREAMS.md`, `ARCHITECT.md`, and `ROADMAP.md` before starting substantial work.
- Save design and planning docs in `docs/`.
- Save reusable operating guidance in `.agents/`.
- Include source URLs in all research-heavy docs.
- Flag uncertain or conflicting facts instead of silently collapsing them.
- Update root-level status files in the same commit as meaningful work changes.

## Repository conventions

- `docs/` for design docs, plans, reviews, and architecture decisions.
- `.agents/rules/` for mandatory operating rules.
- `.agents/skills/` for reusable agent procedures.
- `.agents/roles/` for persona or role instructions.
- `.agents/workflows/` for multi-step operating flows.
- `.agents/best-practices/` for reference guidance.

## Initial operating loop

1. Read root-level status files and identify the active stream.
2. Ingest or update source data.
3. Resolve entities and reconcile facts.
4. Validate compatibility rules and derived metrics.
5. Run recommendation or comparison workflows.
6. Record caveats, missing data, next improvements, and status-file updates.
