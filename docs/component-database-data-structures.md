# Component Database and Data Structures for Mission Profile Builds

**Author:** Project Steward (2026-07-26)
**Status:** Design Draft
**Milestone:** M3 - Canonical Database Baseline

## 1. Mission Profile Catalogue

| Profile ID | Label | Primary Scoring Axes |
|------------|-------|---------------------|
| desktop-budget | Budget Desktop | value, single_thread, memory |
| desktop-mid | Mid-Range Desktop | multi_thread, single_thread, value |
| desktop-high | High-Perf Desktop | multi_thread, single_thread, io_throughput |
| gaming-budget | Budget Gaming | gpu, single_thread, memory |
| gaming-mid | Mid-Range Gaming | gpu, multi_thread, value |
| gaming-high | High-End Gaming | gpu, multi_thread, single_thread |
| linux-dev | Linux Dev Workstation | linux_support, single_thread, memory |
| linux-gpu | Linux GPU/AI Workstation | linux_support, gpu, multi_thread |
| home-server | Home Server | value, io_throughput, lifecycle |
| media-center | Media Center | linux_support, firmware_openness, value |
| silent-pc | Silent / HTPC | noise_efficiency, linux_support, value |
| ai-inference | Local AI Inference | gpu, memory, linux_support |

## 2. Core Entity Tables (SQL DDL)

### manufacturers
CREATE TABLE manufacturers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT,
    country TEXT,
    founded_year INTEGER,
    url TEXT,
    created_at TEXT DEFAULT (datetime()),
    updated_at TEXT DEFAULT (datetime())
);

### components (polymorphic table)
CREATE TABLE components (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('cpu','gpu','motherboard','memory_module','ssd','hdd','psu','case','cooler','nic','wifi_module')),
    manufacturer_id TEXT REFERENCES manufacturers(id),
    display_name TEXT NOT NULL,
    mpn TEXT,
    upc TEXT,
    ean TEXT,
    launch_date TEXT,
    lifecycle_status TEXT CHECK(lifecycle_status IN ('active','eol','legacy','unknown')),
    form_factor TEXT,
    socket TEXT,
    tdp_watts INTEGER,
    created_at TEXT DEFAULT (datetime()),
    updated_at TEXT DEFAULT (datetime())
);

### component_attributes (EAV pattern)
CREATE TABLE component_attributes (
    id TEXT PRIMARY KEY,
    component_id TEXT NOT NULL REFERENCES components(id) ON DELETE CASCADE,
    attr_key TEXT NOT NULL,
    attr_value TEXT NOT NULL,
    unit TEXT,
    source_fact_id TEXT,
    confidence REAL DEFAULT 1.0,
    created_at TEXT DEFAULT (datetime())
);

### compatibility_edges
CREATE TABLE compatibility_edges (
    id TEXT PRIMARY KEY,
    source_component TEXT NOT NULL REFERENCES components(id),
    target_component TEXT NOT NULL REFERENCES components(id),
    edge_type TEXT NOT NULL CHECK(edge_type IN ('fits_socket','fits_form_factor','pcie_compatible','psu_power_ok','bios_compatible','ram_compatible','cooler_compatible','case_fits','chipset_matches','incompatible')),
    verdict TEXT NOT NULL CHECK(verdict IN ('pass','pass_with_caveat','incompatible')),
    caveat TEXT,
    source_fact_id TEXT,
    created_at TEXT DEFAULT (datetime())
);

### offers (pricing data)
CREATE TABLE offers (
    id TEXT PRIMARY KEY,
    component_id TEXT NOT NULL REFERENCES components(id),
    retailer TEXT NOT NULL,
    listing_url TEXT NOT NULL,
    price_nzd REAL NOT NULL,
    shipping_nzd REAL DEFAULT 0,
    condition TEXT,
    stock_status TEXT,
    effective_date TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    source_fact_id TEXT
);

### source_facts (provenance)
CREATE TABLE source_facts (
    id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT,
    confidence REAL DEFAULT 1.0,
    retrieved_at TEXT NOT NULL,
    notes TEXT
);

## 3. Implementation Sequence

| Phase | Deliverable | Depends On |
|-------|------------|------------|
| 1 | Mission profile catalogue (this doc) | None |
| 2 | SQL DDL migration script | Phase 1 |
| 3 | Compatibility edge JSON schema | Phase 1 |
| 4 | Price offer JSON schema | Phase 1 |
| 5 | Compatibility evaluator stub (Python) | Phase 2, 3 |
| 6 | Parser stubs for CSV/XLSX imports | Phase 2 |
| 7 | Seed data: local datasets into data/raw/ | Phase 2 |
