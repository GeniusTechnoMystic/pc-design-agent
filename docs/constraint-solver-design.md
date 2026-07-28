# Constraint Solver — Mission-Profile Build Design

**Date:** 2026-07-25
**Status:** Draft
**Supersedes:** N/A

## Problem Statement

Given a set of mission requirements (workloads, budget, form factor, platform preferences),
generate an ordered list of compatible PC builds ranked by fitness to those requirements.
The solver sits above the existing `CompatibilityEngine` — it consumes its `ValidationResult`
as a hard gate and adds workload-specific scoring.

## Architecture

```
                     ┌──────────────────────────────┐
                     │     MissionProfile            │
                     │  { workloads, budget, form,   │
                     │    platform, preferences }     │
                     └──────────┬───────────────────┘
                                │
                    ┌───────────▼───────────────┐
                    │    ConstraintSolver        │
                    │  ┌─────────────────────┐   │
                    │  │ PartSelector         │   │
                    │  │ (DB query → cand.)   │   │
                    │  └──────────┬──────────┘   │
                    │  ┌──────────▼──────────┐   │
                    │  │ CompatibilityGate    │   │
                    │  │ (CompatibilityEng.)  │   │
                    │  └──────────┬──────────┘   │
                    │  ┌──────────▼──────────┐   │
                    │  │ WorkloadScorer       │   │
                    │  │ (profile→score fn)   │   │
                    │  └──────────┬──────────┘   │
                    │  ┌──────────▼──────────┐   │
                    │  │ BuildRanker          │   │
                    │  │ (pareto sort)        │   │
                    │  └─────────────────────┘   │
                    └────────────────────────────┘
```

**Components:**

1. **PartSelector** — queries component DB for candidates matching mission constraints (socket, TDP range, form factor, price range). Returns a filtered set.

2. **CompatibilityGate** — calls `CompatibilityEngine.validate()` on each candidate build. Drops any that fail hard constraints (score < 0.5). Inherits all existing CPU↔MB, GPU↔PSU, cooler↔case, etc. checks.

3. **WorkloadScorer** — applies per-workload weight profiles to score remaining builds. Each workload defines weight dimensions (GPU compute, CPU single-thread, CPU multi-thread, RAM bandwidth, storage IOPS, power efficiency, price/performance). Builds are scored against the profile.

4. **BuildRanker** — applies Pareto front over weighted score + total cost + power efficiency. Returns top-N builds with per-dimension breakdown and trade-off documentation.

## Mission Profile Schema

```python
@dataclass
class MissionProfile:
    name: str                          # e.g., "Budget Gaming", "LLM Inference Workstation"
    workloads: list[WorkloadWeight]
    budget_nzd: float                  # max total
    form_factor: str                   # ATX, mATX, ITX
    platform_bias: Optional[str]       # AMD, Intel, NVIDIA, None
    gpu_required: bool = True
    storage_min_gb: int = 500
    ram_min_gb: int = 16
    include_os: bool = True
    include_monitor: bool = False

@dataclass
class WorkloadWeight:
    name: str               # "gaming", "llm-inference", "video-edit", "compile", "general"
    gpu_weight: float       # 0.0 - 1.0
    cpu_st_weight: float
    cpu_mt_weight: float
    ram_bw_weight: float
    storage_iops_weight: float
    power_eff_weight: float
    price_perf_weight: float
```

### Predefined Workload Profiles

| Workload | GPU | CPU-ST | CPU-MT | RAM BW | IOPS | PwrEff | Price/Perf |
|----------|-----|--------|--------|--------|------|--------|-----------|
| Gaming | 0.35 | 0.25 | 0.10 | 0.10 | 0.05 | 0.05 | 0.10 |
| LLM Inference | 0.50 | 0.05 | 0.05 | 0.15 | 0.05 | 0.10 | 0.10 |
| Video Editing | 0.25 | 0.10 | 0.25 | 0.20 | 0.05 | 0.05 | 0.10 |
| Software Compile | 0.05 | 0.05 | 0.40 | 0.15 | 0.15 | 0.05 | 0.15 |
| General Purpose | 0.15 | 0.15 | 0.15 | 0.10 | 0.10 | 0.15 | 0.20 |
| AI Training | 0.45 | 0.05 | 0.15 | 0.20 | 0.05 | 0.05 | 0.05 |
| Home Server | 0.00 | 0.05 | 0.20 | 0.05 | 0.10 | 0.35 | 0.25 |

## Scoring Formula

For each compatible build, compute:

```
workload_score = Σ(w_i × component_score_i)   for i in workload dimensions
total_score = 0.7 × workload_score + 0.3 × price_score
```

Where:
- `component_score_i` is derived from benchmark data normalized 0-100
- `price_score` is 100 × (1 - actual_cost / budget), capped at 100
- Missing benchmark data for a component triggers a 10% uncertainty penalty
- A build with zero price data (all unknown) gets price_score = 50

## Implementation Plan

### Phase 1: Profile Schema + Scorer (this task)
- Define `MissionProfile` and `WorkloadWeight` dataclasses in `engine/mission_profile.py`
- Define predefined profiles as module-level constants
- Implement `WorkloadScorer` class with profile×component scoring

### Phase 2: Part Selection
- Implement `PartSelector` that queries from component DB or JSON seed data
- Support budget filtering, platform preference, socket/pcie filtering

### Phase 3: Solver Orchestration
- Wire PartSelector + CompatibilityGate + WorkloadScorer + BuildRanker
- Produce ranked output with per-dimension breakdown
- Generate "trade-off notes" explaining why build B was ranked below build A

## Integration Points

- **CompatibilityEngine** (existing) — hard constraint gate, unchanged
- **PartSpec dataclasses** (existing) — extended with benchmark/price fields
- **MissionProfile** (new) — input schema, user-facing
- **BuildRanker output** (new) — JSON/markdown report, kanban-trackable
