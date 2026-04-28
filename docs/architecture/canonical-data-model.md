# Canonical Data Model

## Purpose

Define the first formal data contracts for the PC Design Agent canonical store.

## Canonical entity ID format

Use lowercase, stable, namespaced IDs:

- `mfr:<slug>`
- `family:<slug>`
- `sku:<slug>`
- `cpu:<slug>`
- `mb:<slug>`
- `gpu:<slug>`
- `ram:<slug>`
- `ssd:<slug>`
- `hdd:<slug>`
- `psu:<slug>`
- `case:<slug>`
- `cooler:<slug>`
- `nic:<slug>`
- `wifi:<slug>`
- `fw:<slug>`
- `drv:<slug>`
- `suite:<slug>`
- `bench:<slug>`
- `retailer:<slug>`
- `listing:<slug>`

Use a normalized slug that preserves the distinguishing parts of the model name, memory size, and vendor where needed.

## Fact model

Use a typed fact model rather than only wide tables.

Suggested logical fields:

- fact_id
- canonical_entity_id
- attribute_name
- value_type
- value_string
- value_number
- value_integer
- value_boolean
- value_json
- unit
- source_name
- source_url
- source_type
- retrieved_at
- effective_date
- confidence_score
- extraction_method
- raw_capture_ref

## Relationship model

Start with relationship tables in PostgreSQL.

Core edges:

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

## Price and offer model

Store all volatile market data separately from core specs.

### Retail offers

- offer_id
- canonical_entity_id
- retailer_id
- region
- currency
- price_local
- shipping_local
- landed_nzd
- stock_status
- retrieved_at
- source_url

### Used listings

- listing_id
- canonical_entity_id
- marketplace
- title
- condition
- asking_price_local
- shipping_local
- landed_nzd
- seller_rating
- listing_age_days
- sold_flag
- source_url
- retrieved_at

## Recommendation model

Use recommendation payloads that carry:

- workload profile
- compatibility verdict
- component list
- score vector
- cost summary
- Linux notes
- firmware openness notes
- caveats
- evidence links

## Validation philosophy

- Official specs win for hard physical and electrical facts.
- Field evidence wins for Linux operability and firmware update reality.
- Preserve conflicting values if confidence is insufficient to collapse them.
- Emit manual-review flags for ambiguous matches or anomalous prices.
