# Staging Plan

## Initial staged datasets

### 1. GPU benchmark staging

Input:
- `data/raw/gpu-userbenchmarks/GPU_UserBenchmarks.csv`

Outputs:
- normalized GPU benchmark rows
- extracted vendor and model aliases
- benchmark source links
- sample-count quality indicators

### 2. CPU and mixed benchmark staging

Input:
- `data/raw/pcbuild/PCBuild.xlsx`

Outputs:
- normalized CPU benchmark rows
- normalized value-score rows
- memory and price feature extracts where available

### 3. GPU price and benchmark cross-reference staging

Input:
- `data/raw/amd-radeon-xfx-analysis/AMD-Radeon-XFX-Graphics-Cards-Analysis-04-11-2025.xlsx`

Outputs:
- normalized GPU model rows
- benchmark-source URL references
- NZ pricing-source references
- cross-source alias map for XFX products

## Validation checks

- detect duplicate column names
- detect missing source URLs in imported metadata
- detect malformed price fields
- detect missing benchmark sample counts where expected
- flag aliases that cannot map cleanly to a vendor and model family
