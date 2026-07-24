# Data Layout

## Directories

- `raw/` for immutable source captures, imported files, and snapshots
- `staging/` for normalized intermediate tables and manifests
- `curated/` for validated, reconciled outputs and gold datasets

## Principles

- Keep source files immutable once imported.
- Track the original file name, source URL, and retrieval or import timestamp.
- Do not mix raw source artifacts with reconciled outputs.
- Every staged dataset should point back to the raw import manifest.
