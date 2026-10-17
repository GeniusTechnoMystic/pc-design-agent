#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SEED_FILE = RAW_DIR / "seed_sample_components.jsonl"

SAMPLE_RECORDS = [
    {
        "source": "seed",
        "category": "cpu",
        "vendor": "AMD",
        "model": "Ryzen 7 7800X3D",
        "socket": "AM5",
        "tdp_watts": 120,
        "core_count": 8,
        "thread_count": 16,
        "market": "global",
        "provenance": {
            "source_name": "seed_sample",
            "source_url": "https://example.invalid/seed/cpu/ryzen-7-7800x3d",
            "confidence_score": 0.9,
        },
    },
    {
        "source": "seed",
        "category": "gpu",
        "vendor": "NVIDIA",
        "model": "GeForce RTX 4070 Super",
        "gpu_arch": "AD104",
        "tdp_watts": 220,
        "vram_gb": 12,
        "market": "global",
        "provenance": {
            "source_name": "seed_sample",
            "source_url": "https://example.invalid/seed/gpu/rtx-4070-super",
            "confidence_score": 0.9,
        },
    },
    {
        "source": "seed",
        "category": "motherboard",
        "vendor": "MSI",
        "model": "B650 Tomahawk WiFi",
        "socket": "AM5",
        "chipset": "B650",
        "form_factor": "ATX",
        "market": "global",
        "provenance": {
            "source_name": "seed_sample",
            "source_url": "https://example.invalid/seed/motherboard/b650-tomahawk-wifi",
            "confidence_score": 0.85,
        },
    },
]

if SEED_FILE.exists():
    existing = SEED_FILE.read_text(encoding="utf-8").strip().splitlines()
    if existing:
        print(f"Seed file already exists at {SEED_FILE}. Skipping regeneration.")
        raise SystemExit(0)

with SEED_FILE.open("w", encoding="utf-8") as fh:
    for record in SAMPLE_RECORDS:
        fh.write(json.dumps(record, separators=(",", ":")) + "\n")

print(f"Created seed data at {SEED_FILE}")
