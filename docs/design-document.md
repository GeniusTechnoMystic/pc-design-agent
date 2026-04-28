# PC Design Agent Design Document

## Purpose

Build a private, agentic PC design system centered on a canonical hardware database and compatibility graph. The system should ingest specs, pricing, benchmarks, Linux compatibility signals, firmware openness signals, lifecycle data, and used-market listings, then traverse those facts with workload-aware algorithms to produce build recommendations.

## Prior context

This design builds on prior project notes captured in [PCDesign_Session_2026-04-22.md](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_d7a6bff8-7b8f-4931-8312-115cb3e5a529/e58ac676-af16-4d69-87aa-05482c6166df/PCDesign_Session_2026-04-22.md), the benchmark-oriented [PCBuild.xlsx](https://ppl-ai-file-upload.s3.amazonaws.com/connectors/google_drive/17Ke-6W8b4Z2sYPTA650yH7_d4kZ8Nq-kvk5JjMIWotQ/cbc44976-e4c9-4469-b3ef-65bddccd1f28/PCBuild.xlsx), the GPU benchmark dataset [GPU_UserBenchmarks.csv](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_d7a6bff8-7b8f-4931-8312-115cb3e5a529/b0ba5bd7-3383-46a0-97a6-7ac6fa388154/GPU_UserBenchmarks.csv), and the pricing-and-benchmark workbook [AMD Radeon XFX Graphics Cards Analysis 04/11/2025.xlsx](https://ppl-ai-file-upload.s3.amazonaws.com/connectors/google_drive/1GN4zWKGT6WtIg5YDu5PygcFHIYd13ULFymEYtXRz_iU/b558d15f-1c5e-4278-acff-02dec86a01ea/AMD-Radeon-XFX-Graphics-Cards-Analysis-04-11-2025.xlsx).

## Goals

- Model PC components, protocols, firmware, drivers, prices, and benchmarks as first-class entities.
- Preserve source provenance for every important fact.
- Support hard compatibility checks plus soft and probabilistic design heuristics.
- Optimize recommendations for diverse workloads including gaming, Linux workstations, AI inference, AI training-light, storage-heavy systems, and homelab virtualization.
- Track NZ and AU retail and used-market prices, with special attention to shipping to New Zealand.
- Surface Linux support, firmware support, open hardware, and right-to-repair signals.

## Non-goals

- Real-time checkout or purchasing in v1.
- Full automatic extraction from every retailer on day one.
- Fully autonomous design changes without review.

## System architecture

The system should use a hybrid data architecture:

- PostgreSQL as the canonical fact store for products, specs, pricing, lifecycle, and benchmark records.
- Graph-style relationship tables first, with an option to add Apache AGE or Neo4j if graph traversal becomes complex.
- Object storage for raw spec sheets, PDFs, product pages, benchmark snapshots, and listing captures.
- Optional vector retrieval for manuals, release notes, and issue threads.
- An agent orchestration layer that translates user goals into constraints, queries the data layer, and explains trade-offs.

## Canonical data model

### Core entities

- Manufacturer
- Product family
- Product SKU
- CPU
- Motherboard
- GPU
- Memory module
- SSD
- HDD
- PSU
- Case
- Cooler
- NIC
- Wi-Fi module
- Firmware record
- Driver record
- Benchmark suite
- Benchmark result
- Retailer
- Marketplace listing
- Lifecycle record
- Repairability record
- Protocol standard
- Socket
- Chipset
- Form factor
- Connector

### Core relationships

- compatible_with
- electrically_supported_by
- physically_fits_in
- firmware_supported_by
- bios_required_for
- driver_supported_by
- benchmarked_in
- priced_at
- alternative_to
- conflicts_with
- requires_adapter
- shares_protocol_with
- open_firmware_option_for
- linux_support_verified_for

## Provenance model

Each fact should include:

- source_name
- source_url
- retrieval_timestamp
- extraction_method
- confidence_score
- effective_date
- raw_capture_reference
- superseded_by

This is mandatory because benchmark sites, product pages, BIOS compatibility lists, and marketplace listings all change over time.

## Source strategy

### Product specs

Preferred order:

1. Vendor official product pages and spec sheets
2. Vendor support pages and manuals
3. Structured part aggregators
4. Community databases and validated issue trackers

### Retail prices

Use NZ and AU retail sources with stable identifiers where possible. The strongest current structured input is the unofficial PCPartPicker API wrapper, which supports multiple part categories and regional storefront coverage including New Zealand and Australia in the project documentation at [JonathanVusich/pcpartpicker](https://github.com/JonathanVusich/pcpartpicker).

### Used prices

Ingest live listings from NZ and AU marketplaces. Trade Me is a critical NZ source for GPUs, CPUs, boards, and systems via [Trade Me components](https://www.trademe.co.nz/a/marketplace/computers/components) and targeted searches such as [Trade Me RTX 3060](https://www.trademe.co.nz/a/marketplace/s/rtx-3060/k2c0-2). AU used-market ingestion should include eBay Australia and other refurbisher inventories, with shipping-to-NZ normalization where possible.

### Benchmarks

Use multiple benchmark layers:

- Aggregate CPU comparisons from [PassMark CPU Benchmarks](https://www.cpubenchmark.net)
- Aggregate GPU comparisons from [PassMark VideoCard Benchmarks](https://www.videocardbenchmark.net)
- Linux-native and workload-specific benchmarks from [Phoronix Test Suite](https://github.com/phoronix-test-suite/phoronix-test-suite)
- OpenBenchmarking-linked results where relevant
- Local user datasets from existing Space files

PassMark states that CPU charts are built from benchmark submissions and internal testing and are updated daily at [PassMark CPU Benchmarks](https://www.cpubenchmark.net). Phoronix Test Suite describes itself as open-source, cross-platform automated benchmarking software with OpenBenchmarking integration at [phoronix-test-suite/phoronix-test-suite](https://github.com/phoronix-test-suite/phoronix-test-suite).

### Linux support

Linux operability and driver-awareness should combine:

- [linuxhw/hw-probe](https://github.com/linuxhw/hw-probe)
- [Linux Hardware Database](https://linux-hardware.org)
- kernel support metadata such as LKDDb
- vendor Linux driver pages
- distro-specific issue records

Linux Hardware Database reports hundreds of thousands of tested systems and parts at [linux-hardware.org](https://linux-hardware.org), making it valuable for real-world compatibility evidence. The hw-probe project explicitly targets hardware probing, operability checks, and driver discovery in [linuxhw/hw-probe](https://github.com/linuxhw/hw-probe).

### Firmware openness and lifecycle

Use:

- [coreboot/coreboot](https://github.com/coreboot/coreboot)
- [fwupd/fwupd](https://github.com/fwupd/fwupd)
- [LVFS](https://fwupd.org)
- openSIL-related references where applicable
- vendor BIOS release history

Coreboot is an important source for open firmware support breadth and board-level support tracking at [coreboot/coreboot](https://github.com/coreboot/coreboot). LVFS matters because it is the Linux firmware delivery ecosystem used by fwupd-supported vendors, as described at [fwupd.org](https://fwupd.org).

## Ingestion pipeline

### Stage 1: Source adapters

Create a dedicated adapter per source:

- adapter_pcpartpicker
- adapter_vendor_specs
- adapter_trademe
- adapter_ebay_au
- adapter_passmark_cpu
- adapter_passmark_gpu
- adapter_phoronix
- adapter_hwprobe
- adapter_linux_hardware_db
- adapter_coreboot
- adapter_fwupd

Each adapter should output:

- normalized entity candidates
- normalized facts
- raw source capture
- retrieval metadata
- source confidence

### Stage 2: Entity resolution

Resolve aliases and duplicates using:

- vendor
- model family
- chipset or GPU die
- UPC, EAN, MPN where available
- PCI IDs or USB IDs where available
- fuzzy name matching
- curated overrides

### Stage 3: Fact reconciliation

Rules:

- Prefer official specs for hard physical and electrical specs.
- Prefer Linux Hardware Database and hw-probe for Linux operability evidence.
- Prefer latest firmware source for BIOS and firmware status.
- Prefer sold-market medians over asking-price snapshots where available.
- Preserve conflicting values if unresolved.

### Stage 4: Derived metrics

Generate:

- performance_per_dollar
- performance_per_watt
- linux_confidence_score
- firmware_openness_score
- repairability_score
- lifecycle_score
- used_value_score
- shipping_adjusted_cost_nzd
- risk_score
- upgrade_path_score

## Recommendation engine

### Hard constraints

- Socket, chipset, and memory-generation compatibility
- Physical fit and clearance
- PCIe slot and lane sufficiency
- PSU connector sufficiency and power headroom
- BIOS support floor
- Required protocol support such as PCIe generation, USB4, ECC, SR-IOV, or NVMe bootability

### Soft constraints

- VRM suitability for sustained CPU load
- Memory topology and training risk
- Acoustic suitability
- Idle power behavior
- Linux niceness of onboard NIC, Wi-Fi, audio, and sensor chips
- Ease of firmware recovery

### Workload profiles

Initial workload templates:

- Gaming
- Linux workstation
- Homelab virtualization
- AI inference
- AI training-light
- Storage server
- HTPC
- Low-power general-purpose

### Optimization approach

Use a multi-objective ranking model rather than one scalar benchmark score. Suggested dimensions:

- Single-thread performance
- Multi-thread performance
- GPU compute capability
- Storage throughput
- Memory bandwidth and latency
- Cost and landed cost to NZ
- Idle power and full-load efficiency
- Linux support confidence
- Firmware openness and repairability
- Platform longevity and upgrade path

## Suggested repository layout

```text
pc-design-agent/
  docs/
    design-document.md
    project-plan.md
    project-plan-review.md
  data/
    raw/
    staging/
    curated/
  schemas/
  src/
    adapters/
    entity_resolution/
    reconciliation/
    scoring/
    graph/
    api/
  tests/
  .agents/
    rules/
    skills/
    roles/
    workflows/
    best-practices/
  AGENTS.md
```

## Initial milestones

### Milestone 1

- Establish schema and canonical IDs
- Ingest CPUs, motherboards, GPUs, RAM, SSDs, and PSUs
- Import current Space benchmark data
- Stand up provenance tracking

### Milestone 2

- Add NZ and AU retail pricing ingestion
- Add Trade Me and AU used-market ingestion
- Add Linux support and firmware sources
- Build entity resolution pipeline

### Milestone 3

- Implement hard compatibility engine
- Implement workload scoring engine
- Implement recommendation explanations and risk flags

### Milestone 4

- Add scheduled refresh jobs
- Add alerting for price or lifecycle changes
- Add graph exploration and design comparison views

## Risks

- Used-market data is noisy and may have inconsistent identifiers.
- Shipping-to-NZ estimation from AU sellers may require browser fallback and heuristic normalization.
- Vendor specs are often inconsistent across regional product pages.
- Newly launched platforms may show benchmark or Linux-support gaps early in lifecycle.

## Immediate next steps

- Finalize canonical schema and entity naming conventions.
- Define the first 10 source adapters and their output contracts.
- Create the private repository and commit the initial docs and agent operating files.
- Write the first implementation issues for schema, ingestion, and scoring foundations.
