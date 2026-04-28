# Status Protocol Integration

## Goal

Adopt a compact, agent-friendly project status layer using root-level files while preserving the existing design and planning documentation in `docs/`.

## Proposed file roles

### `ARCHITECT.md`

Root-level architecture brief for fast context loading. This should summarize:

- mission and scope
- system architecture
- repo structure
- key rules
- current architectural decisions
- current high-priority constraints

This is the short-form, always-loadable counterpart to the fuller design documents in `docs/`.

### `PROGRESS.md`

Root-level open-loop tracker. This should include:

- current milestone
- completed work
- active work
- queued work
- success criteria
- blockers
- immediate next actions

This becomes the primary status surface for agents before starting work.

### `STREAMS.md`

Root-level stream tracker for parallel work. This should include:

- stream IDs
- objective per stream
- current state
- dependencies
- next handoff step
- handoff notes

This is especially useful if multiple agents or sessions are working in parallel.

### `actions.jsonl`

Chronological machine-readable action log. Each line should record:

- timestamp
- actor
- action_type
- summary
- files_changed
- related_issue
- commit_sha
- status

This acts as the write-ahead operational log.

### `ROADMAP.md`

Root-level roadmap focused on milestones, dependency logic, and sequencing. Include Mermaid dependency graphs for active and near-term work.

### `roadmap.dag`

Optional machine-oriented dependency representation if later automation needs a graph file separate from the Markdown roadmap. For now, `ROADMAP.md` can hold the Mermaid DAG and a plain dependency list.

## Relationship to current repo files

- Keep `AGENTS.md` as the general operating policy.
- Keep `docs/design-document.md` as the comprehensive design narrative.
- Keep `docs/project-plan.md` as the broad implementation plan.
- Keep `docs/review-*.md` as review history.
- Use the new root-level status files for live execution state and handoff context.

## Recommended loading order for future agents

1. `PROGRESS.md`
2. `STREAMS.md`
3. `ARCHITECT.md`
4. `ROADMAP.md`
5. `AGENTS.md`
6. Only then dive into `docs/` as needed.

## Operating rules

- Update `PROGRESS.md` in the same commit as meaningful work changes.
- Update `STREAMS.md` whenever ownership or next-step context changes.
- Append to `actions.jsonl` for each significant execution step.
- Keep root-level status files concise enough to fit comfortably into active agent context.
- Move durable explanation and deep rationale into `docs/`, not into the status files.

## Recommendation

Adopt all five root-level files now. Keep `roadmap.dag` optional but create it as a machine-oriented placeholder so the pattern is present from the start.
