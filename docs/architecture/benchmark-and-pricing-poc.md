# Benchmark and Pricing Proof of Concept

## Goal

Build the first narrow vertical slice around CPUs and GPUs, combining benchmark and pricing evidence with provenance.

## CPU proof of concept

### Sources

- [PassMark CPU Benchmarks](https://www.cpubenchmark.net)
- local benchmark workbook data from `PCBuild.xlsx`

### Desired outputs

- canonical CPU entities
- normalized benchmark facts
- score dimensions for single-thread and multi-thread where available
- retail or reference price facts
- value score derived from normalized performance and cost

## GPU proof of concept

### Sources

- [PassMark VideoCard Benchmarks](https://www.videocardbenchmark.net)
- local benchmark file `GPU_UserBenchmarks.csv`
- local pricing and cross-reference workbook `AMD Radeon XFX Graphics Cards Analysis 04/11/2025.xlsx`
- NZ used or retail spot checks from [Trade Me components](https://www.trademe.co.nz/a/marketplace/computers/components)

### Desired outputs

- canonical GPU entities
- benchmark aggregates and source links
- vendor-model alias map
- pricing rows normalized to NZD
- used vs retail comparison fields

## Proposed metrics

- benchmark_score_raw
- benchmark_score_normalized
- sample_count
- price_nzd
- shipping_nzd
- landed_nzd
- value_score
- confidence_score

## Key risks

- local files may use inconsistent product naming across benchmark sources
- benchmark methodologies differ and require source-specific normalization
- Trade Me data is listing-based rather than sold-price-based in many cases

## Success criteria

- at least 20 CPU entities normalized with provenance
- at least 20 GPU entities normalized with provenance
- at least one cross-source alias mapping table created
- at least one value ranking output for CPUs and one for GPUs
