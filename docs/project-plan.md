# PC Design Agent Project Plan

> For agentic workers: use task decomposition, provenance-first ingestion, and verification at each stage. Track work with checklists and preserve source URLs in all research and documentation outputs.

## Objective

Create a private, source-grounded PC design platform that ingests component specs, benchmark data, Linux and firmware support evidence, and NZ/AU price data into a canonical database and compatibility graph, then generates workload-aware recommendations.

## Architecture summary

The project will use a canonical data layer, an ingestion pipeline, and a scoring and traversal layer. Current source priorities are informed by the unofficial regional part-data wrapper [JonathanVusich/pcpartpicker](https://github.com/JonathanVusich/pcpartpicker), benchmark sources [PassMark CPU Benchmarks](https://www.cpubenchmark.net), [PassMark VideoCard Benchmarks](https://www.videocardbenchmark.net), and [Phoronix Test Suite](https://github.com/phoronix-test-suite/phoronix-test-suite), Linux support evidence from [linuxhw/hw-probe](https://github.com/linuxhw/hw-probe) and [Linux Hardware Database](https://linux-hardware.org), and firmware openness signals from [coreboot/coreboot](https://github.com/coreboot/coreboot) and [LVFS](https://fwupd.org).

## Deliverables

- Design document in `docs/design-document.md`
- Project plan in `docs/project-plan.md`
- Plan review in `docs/project-plan-review.md`
- Agent operating guidance in `AGENTS.md` and `.agents/`
- Private GitHub repository scaffold
- Initial backlog of next jobs

## Workstreams

### 1. Foundations

- Create repository layout
- Establish documentation standards
- Establish provenance and citation standards
- Define naming conventions for entities and source adapters

### 2. Data model

- Define core entities
- Define fact tables and relationship tables
- Define provenance fields
- Define raw-capture storage model
- Define first-pass schema migrations

### 3. Source adapters

Priority adapters:

- vendor specs
- pcpartpicker
- passmark cpu
- passmark gpu
- phoronix
- hw-probe
- linux hardware database
- coreboot
- fwupd
- trademe
- ebay au

Each adapter must emit normalized facts, raw captures, and source metadata.

### 4. Entity resolution and reconciliation

- alias matching
- MPN or UPC normalization
- model-family grouping
- duplicate detection
- conflict preservation and confidence scoring

### 5. Compatibility and scoring engine

- hard compatibility checks
- soft heuristic checks
- workload profiles
- weighted ranking
- risk and caveat generation

### 6. Interface and orchestration

- internal query API
- recommendation orchestration layer
- explanation generator
- comparison output format

## Phased implementation

### Phase 0: Project setup

- create repository
- create docs and agent operating files
- define coding standards and contribution flow
- create initial issues and milestones

### Phase 1: Schema and seed data

- design schema
- create migrations
- load local benchmark files from Space
- ingest a seed set of CPUs, GPUs, motherboards, RAM, SSDs, and PSUs

### Phase 2: External ingestion

- connect structured retail and benchmark sources
- add Linux support and firmware sources
- add used-market ingestion
- normalize landed-cost model for NZ

### Phase 3: Recommendation engine

- implement hard-constraint compatibility engine
- implement workload profiles
- implement multi-objective scoring
- implement explanation templates and evidence links

### Phase 4: Operations

- add scheduled refresh jobs
- add anomaly detection for major price moves or source regressions
- add QA dashboards for entity resolution and source freshness

## Acceptance criteria

- All stored facts include source URL and retrieval metadata.
- At least one full build path can be computed from CPU to case and PSU with compatibility checks.
- At least one workload profile can rank builds using benchmark and price data.
- Linux-support and firmware-support evidence is visible in recommendation outputs.
- NZ landed-cost calculations are available for at least one retail and one used-market source.

## Backlog candidates

### Schema

- canonical entity ID format
- spec attribute registry
- compatibility-edge schema
- provenance schema

### Adapters

- parse official CPU spec pages
- parse motherboard support lists
- import GPU benchmark CSV
- ingest PCBuild workbook
- ingest XFX workbook
- create Trade Me listing normalizer
- create AU shipping normalizer

### Engine

- socket and memory constraint solver
- PCIe lane and slot model
- VRM adequacy heuristic
- Linux confidence scorer
- firmware openness scorer
- lifecycle decay scorer

### QA

- source freshness tests
- entity resolution review queue
- benchmark outlier detection
- missing-spec audit

## Immediate next jobs

1. Define the canonical schema and adapter contracts.
2. Import local Space files into the raw and staging layers.
3. Create the initial GitHub issues for schema, ingestion, and scoring.
4. Decide whether graph traversal should start in PostgreSQL tables or a dedicated graph engine.
5. Build the first benchmark-and-price proof of concept around CPUs and GPUs.
