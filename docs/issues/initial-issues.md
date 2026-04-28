# Initial GitHub Issues

## 1. Canonical schema and provenance model

### Summary
Define the first canonical schema for entities, facts, provenance, relationships, and market data.

### Scope
- canonical entity ID format
- fact model
- relationship model
- provenance fields
- retail offer and used listing structures

### Deliverables
- schema design doc
- SQL draft or migration plan
- review notes

## 2. Adapter contracts and JSON schemas

### Summary
Formalize adapter outputs and recommendation payload schemas.

### Scope
- source-fact schema
- entity-candidate schema
- recommendation-output schema
- future compatibility-edge and offer schemas

### Deliverables
- JSON schema files in `schemas/`
- schema README
- example payloads

## 3. Import local benchmark files from Space

### Summary
Create the raw and staging import workflow for existing local benchmark and pricing files.

### Scope
- import manifest
- raw file copy plan
- staging normalization plan
- validation checks

### Deliverables
- `data/raw/import-manifest.yaml`
- staging docs
- import script stub

## 4. CPU and GPU benchmark proof of concept

### Summary
Normalize a first set of CPU and GPU benchmark records with provenance.

### Scope
- ingest local benchmark files
- define normalization outputs
- rank by baseline value metrics
- preserve sample counts and source links

### Deliverables
- proof-of-concept data outputs
- normalization notebook or script
- ranking summary

## 5. Linux support evidence ingestion

### Summary
Define how Linux Hardware Database and hw-probe evidence enters the canonical store.

### Scope
- compatibility evidence schema
- source freshness expectations
- confidence scoring rules
- manual-review triggers

### Deliverables
- source notes
- draft schema additions
- ingestion plan

## 6. Firmware openness and lifecycle ingestion

### Summary
Define how coreboot, fwupd, LVFS, and lifecycle evidence are modeled.

### Scope
- firmware evidence schema
- lifecycle and repairability structures
- source priority rules
- caveat taxonomy

### Deliverables
- schema additions
- source map updates
- ingestion plan

## 7. NZ retail and Trade Me price ingestion proof of concept

### Summary
Design the first NZ-focused retail and marketplace price workflow.

### Scope
- retailer and marketplace offer schema
- shipping and landed-cost normalization
- condition grading for used listings
- anomaly detection for outlier listings

### Deliverables
- price schema additions
- normalization rules
- proof-of-concept query plan
