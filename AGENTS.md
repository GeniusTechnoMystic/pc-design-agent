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

- Save design and planning docs in `docs/`.
- Save reusable operating guidance in `.agents/`.
- Include source URLs in all research-heavy docs.
- Flag uncertain or conflicting facts instead of silently collapsing them.

## Repository conventions

- `docs/` for design docs, plans, reviews, and architecture decisions.
- `.agents/rules/` for mandatory operating rules.
- `.agents/skills/` for reusable agent procedures.
- `.agents/roles/` for persona or role instructions.
- `.agents/workflows/` for multi-step operating flows.
- `.agents/best-practices/` for reference guidance.

## Initial operating loop

1. Ingest or update source data.
2. Resolve entities and reconcile facts.
3. Validate compatibility rules and derived metrics.
4. Run recommendation or comparison workflows.
5. Record caveats, missing data, and next improvements.
