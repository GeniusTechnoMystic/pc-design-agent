# Schemas

This directory contains the first formal contracts for ingestion and recommendation payloads.

## Included schemas

- `entity-candidate.schema.json` for adapter and entity-resolution candidate outputs
- `source-fact.schema.json` for normalized, provenance-rich facts emitted by adapters
- `recommendation-output.schema.json` for final build and comparison outputs

## Design intent

These contracts are designed to keep the project provenance-first. Every important fact should carry source identity, retrieval timing, and confidence. Recommendation outputs should expose both scores and evidence links so recommendations remain inspectable.

## Current source assumptions

The unofficial PCPartPicker wrapper documents regional support including NZ and AU and returns structured part data with timestamps at [JonathanVusich/pcpartpicker](https://github.com/JonathanVusich/pcpartpicker). Phoronix Test Suite documents automated benchmarking, batch mode, and OpenBenchmarking-linked profiles and suites at [phoronix-test-suite/phoronix-test-suite](https://github.com/phoronix-test-suite/phoronix-test-suite). Linux Hardware Database presents Linux compatibility evidence across hundreds of thousands of tested systems and parts at [linux-hardware.org](https://linux-hardware.org). LVFS documents vendor firmware uploads and the fwupd ecosystem at [fwupd.org](https://fwupd.org).

## Next schema additions

- adapter-run manifest schema
- entity-resolution review schema
- price-offer schema
- shipping-quote schema
- compatibility-edge schema
- lifecycle and repairability schemas
