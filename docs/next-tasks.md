# Next Tasks and Jobs

## Priority 1

- Define canonical entity IDs and naming conventions.
- Define adapter output schema and recommendation output schema.
- Create `schemas/` directory with JSON schemas for source facts, entity candidates, and recommendation results.
- Initialize PostgreSQL schema design for entities, facts, relationships, provenance, and pricing.

## Priority 2

- Import `GPU_UserBenchmarks.csv` into a raw and staging workflow.
- Import `PCBuild.xlsx` and `AMD Radeon XFX Graphics Cards Analysis 04/11/2025.xlsx` into the raw layer.
- Build initial parsers for CPU and GPU benchmark sources.
- Create a gold dataset of 20 to 50 parts for end-to-end validation.

## Priority 3

- Build first-pass adapters for vendor specs, PCPartPicker, PassMark CPU, PassMark GPU, hw-probe, Linux Hardware Database, coreboot, and fwupd.
- Design the Trade Me listing normalizer and AU shipping normalizer.
- Add source freshness policy and conflict review queue.

## Priority 4

- Implement hard compatibility checks for socket, memory generation, form factor, clearances, PSU connectors, and PCIe slot sufficiency.
- Implement first workload profile scoring for Linux workstation and homelab virtualization.
- Define recommendation output payload with evidence links, confidence, and caveats.

## Suggested first issues

1. Canonical schema and provenance model
2. Adapter contracts and JSON schemas
3. Import local benchmark files from Space
4. CPU and GPU benchmark proof of concept
5. Linux support evidence ingestion
6. Firmware openness and lifecycle ingestion
7. NZ retail and Trade Me price ingestion proof of concept
