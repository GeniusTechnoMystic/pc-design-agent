# Project Plan Review

## Review summary

The current project plan is directionally strong and sequenced well for a greenfield build. It correctly starts with schema and provenance rather than trying to implement recommendation logic before the data layer exists.

## Strengths

- Clear separation between foundations, data model, ingestion, scoring, and operations.
- Good emphasis on provenance and evidence retention.
- Correct prioritization of benchmark, Linux support, and firmware support sources such as [PassMark CPU Benchmarks](https://www.cpubenchmark.net), [Phoronix Test Suite](https://github.com/phoronix-test-suite/phoronix-test-suite), [linuxhw/hw-probe](https://github.com/linuxhw/hw-probe), [Linux Hardware Database](https://linux-hardware.org), [coreboot/coreboot](https://github.com/coreboot/coreboot), and [LVFS](https://fwupd.org).
- Good focus on NZ landed-cost modeling and used-market ingestion.

## Gaps to close

### 1. Source contracts need explicit schemas

The plan names adapters but does not yet define a standard adapter output contract. Add a shared schema for:

- source entity key
- canonical entity candidates
- raw capture reference
- normalized facts
- confidence score
- retrieved_at
- source_url

### 2. Build-level recommendation outputs need a formal schema

Define the final recommendation output early. Include:

- build ID
- component list
- compatibility verdict
- workload scores
- total cost
- shipping-adjusted cost
- Linux support notes
- firmware openness notes
- caveats
- evidence links

### 3. Lifecycle and repairability need stronger first-class treatment

The current plan references lifecycle and firmware, but repairability and support-lifecycle data should become explicit tables rather than being buried in general metadata.

### 4. QA loops should be part of each phase

Do not wait until operations to validate data quality. Add validation gates to schema, ingestion, and scoring phases.

## Recommended edits

- Add a `schemas/` directory in the next implementation pass.
- Write JSON schemas for adapters and recommendation outputs before writing ingestion code.
- Add a source freshness policy by source class.
- Add a manual-review queue for entity resolution conflicts and anomalous pricing.
- Create a small gold dataset of 20 to 50 parts for end-to-end testing before scaling ingestion.

## Conclusion

The plan is ready to proceed, but schema contracts and review loops should be added immediately in the next planning pass.
