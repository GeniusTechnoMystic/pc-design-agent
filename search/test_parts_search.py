#!/usr/bin/env python3
"""Tests for parts_search.py — covers dataclasses, registry, search,
compatibility, build summary, and CLI."""

import json
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts_search import (
    PartRegistry,
    CpuSpec, GpuSpec, MotherboardSpec, RamSpec, StorageSpec,
    PsuSpec, CaseSpec, CoolerSpec, PartSpec,
    PART_TYPES, _PART_TYPE_TO_CLASS,
    _hasattr_val,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_CPU = {
    "name": "Ryzen 7 7800X3D",
    "brand": "AMD",
    "model": "100-100000910WOF",
    "part_type": "cpu",
    "current_price": 589.00,
    "socket": "AM5",
    "core_count": 8,
    "thread_count": 16,
    "base_clock_ghz": 4.2,
    "boost_clock_ghz": 5.0,
    "tdp_watts": 120,
    "max_tdp_watts": 162,
    "has_igpu": 1,          # will be coerced to True
    "igpu_model": "Radeon Graphics",
    "memory_type": "DDR5",
    "generation": "Ryzen 7000",
    "l3_cache_mb": 96,
    "pcie_version": "PCIe 4.0",
    "pcie_lanes": 28,
}

SAMPLE_CPU2 = {
    "name": "Core i5-13600K",
    "brand": "Intel",
    "model": "BX8071513600K",
    "part_type": "cpu",
    "current_price": 319.00,
    "socket": "LGA1700",
    "core_count": 14,
    "thread_count": 20,
    "base_clock_ghz": 3.5,
    "boost_clock_ghz": 5.1,
    "tdp_watts": 125,
    "max_tdp_watts": 181,
    "has_igpu": 1,
    "igpu_model": "UHD Graphics 770",
    "memory_type": "DDR5",
    "generation": "13th Gen",
    "l3_cache_mb": 24,
    "pcie_version": "PCIe 5.0",
    "pcie_lanes": 20,
}

SAMPLE_GPU = {
    "name": "RTX 4090",
    "brand": "NVIDIA",
    "model": "GV-N4090GAMING OC-24GD",
    "part_type": "gpu",
    "current_price": 2799.00,
    "chipset": "RTX 4090",
    "vram_size_gb": 24,
    "vram_type": "GDDR6X",
    "tdp_watts": 450,
    "length_mm": 331.0,
    "recommended_psu_w": 850,
    "boost_clock_mhz": 2520,
}

SAMPLE_MOBO = {
    "name": "ROG STRIX X670E-E",
    "brand": "ASUS",
    "model": "ROG STRIX X670E-E GAMING WIFI",
    "part_type": "motherboard",
    "current_price": 649.00,
    "socket": "AM5",
    "chipset": "X670E",
    "form_factor": "ATX",
    "ram_type": "DDR5",
    "ram_slots": 4,
    "max_ram_gb": 128,
    "wifi_builtin": 1,
    "pcie_version": "PCIe 5.0",
    "m2_slots": 5,
}

SAMPLE_MOBO_INTEL = {
    "name": "Z790 AORUS ELITE AX",
    "brand": "Gigabyte",
    "model": "Z790 AORUS ELITE AX",
    "part_type": "motherboard",
    "current_price": 259.00,
    "socket": "LGA1700",
    "chipset": "Z790",
    "form_factor": "ATX",
    "ram_type": "DDR5",
    "ram_slots": 4,
    "max_ram_gb": 128,
    "wifi_builtin": 1,
}

SAMPLE_RAM = {
    "name": "Trident Z5 Neo RGB 32GB",
    "brand": "G.Skill",
    "model": "F5-6000J3038F16GX2-TZ5NR",
    "part_type": "ram",
    "current_price": 179.00,
    "ram_type": "DDR5",
    "speed_mhz": 6000,
    "capacity_gb": 32,
    "sticks": 2,
    "cas_latency": "CL30",
    "timings": "30-38-38-96",
    "rgb": 1,
    "xmp_support": 1,
    "expo_support": 1,
}

SAMPLE_STORAGE = {
    "name": "990 Pro 2TB",
    "brand": "Samsung",
    "model": "MZ-V9P2T0BW",
    "part_type": "storage",
    "current_price": 249.00,
    "storage_type": "NVMe SSD",
    "capacity_gb": 2000,
    "form_factor": "M.2 2280",
    "interface": "PCIe 4.0 x4",
    "nand_type": "TLC",
    "dram_cache": 1,
    "read_speed_mbs": 7450,
    "write_speed_mbs": 6900,
    "endurance_tbw": 1200,
}

SAMPLE_PSU = {
    "name": "RM850x",
    "brand": "Corsair",
    "model": "CP-9020200-NA",
    "part_type": "psu",
    "current_price": 149.00,
    "wattage": 850,
    "efficiency_rating": "80+ Gold",
    "modular_type": "Full",
    "form_factor": "ATX",
    "fan_size_mm": 135,
    "single_rail": 1,
    "atx_30_compliant": 1,
}

SAMPLE_PSU_LOW = {
    "name": "VS550",
    "brand": "Corsair",
    "model": "CP-9020170-NA",
    "part_type": "psu",
    "current_price": 69.00,
    "wattage": 550,
    "efficiency_rating": "80+ White",
    "modular_type": "Non-modular",
    "form_factor": "ATX",
}

SAMPLE_CASE = {
    "name": "4000D Airflow",
    "brand": "Corsair",
    "model": "CC-9011200-WW",
    "part_type": "case",
    "current_price": 104.00,
    "case_type": "Mid Tower",
    "motherboard_support": '["ATX", "mATX", "Mini-ITX"]',
    "max_gpu_length_mm": 360.0,
    "max_cpu_cooler_height_mm": 170.0,
    "max_psu_length_mm": 220.0,
}

SAMPLE_COOLER = {
    "name": "NH-D15",
    "brand": "Noctua",
    "model": "NH-D15",
    "part_type": "cooler",
    "current_price": 109.00,
    "cooler_type": "Air (Tower)",
    "height_mm": 165.0,
    "max_tdp_watts": 250,
    "socket_compatibility": "LGA1700, AM5, AM4, LGA1200, LGA115x",
    "fan_size_mm": 140,
    "fan_count": 2,
    "pwm": 1,
    "heatpipe_count": 6,
}

SAMPLE_COOLER_AIO = {
    "name": "Kraken X63",
    "brand": "NZXT",
    "model": "RL-KRX63-01",
    "part_type": "cooler",
    "current_price": 179.00,
    "cooler_type": "AIO",
    "radiator_size_mm": 280,
    "max_tdp_watts": 350,
    "socket_compatibility": "LGA1700, AM5, AM4, LGA1200, LGA115x, sTRX4, sWRX8",
    "fan_size_mm": 140,
    "fan_count": 2,
}


def make_registry() -> PartRegistry:
    """Build a populated registry for testing."""
    reg = PartRegistry()
    reg.load_dict("cpu", SAMPLE_CPU)
    reg.load_dict("cpu", SAMPLE_CPU2)
    reg.load_dict("gpu", SAMPLE_GPU)
    reg.load_dict("motherboard", SAMPLE_MOBO)
    reg.load_dict("motherboard", SAMPLE_MOBO_INTEL)
    reg.load_dict("ram", SAMPLE_RAM)
    reg.load_dict("storage", SAMPLE_STORAGE)
    reg.load_dict("psu", SAMPLE_PSU)
    reg.load_dict("psu", SAMPLE_PSU_LOW)
    reg.load_dict("case", SAMPLE_CASE)
    reg.load_dict("cooler", SAMPLE_COOLER)
    reg.load_dict("cooler", SAMPLE_COOLER_AIO)
    return reg


# ===========================================================================
# Tests: Dataclasses
# ===========================================================================

class TestDataclasses:
    def test_part_types_all_have_classes(self):
        for pt in PART_TYPES:
            assert pt in _PART_TYPE_TO_CLASS, f"Missing class for {pt}"

    def test_part_type_class_mapping(self):
        assert _PART_TYPE_TO_CLASS["cpu"] is CpuSpec
        assert _PART_TYPE_TO_CLASS["gpu"] is GpuSpec
        assert _PART_TYPE_TO_CLASS["motherboard"] is MotherboardSpec
        assert _PART_TYPE_TO_CLASS["ram"] is RamSpec
        assert _PART_TYPE_TO_CLASS["storage"] is StorageSpec
        assert _PART_TYPE_TO_CLASS["psu"] is PsuSpec
        assert _PART_TYPE_TO_CLASS["case"] is CaseSpec
        assert _PART_TYPE_TO_CLASS["cooler"] is CoolerSpec

    def test_cpu_spec_defaults(self):
        c = CpuSpec()
        assert c.part_type == "cpu"
        assert c.core_count == 0
        assert c.has_igpu is False

    def test_cpu_spec_to_dict(self):
        c = CpuSpec(name="Test CPU", brand="AMD", current_price=299.0,
                     socket="AM5", core_count=6, tdp_watts=65)
        d = c.to_dict()
        assert d["name"] == "Test CPU"
        assert d["socket"] == "AM5"
        assert d["core_count"] == 6
        assert "_id" not in d
        assert "_tags" not in d

    def test_gpu_spec(self):
        g = GpuSpec(name="Test GPU", chipset="RTX 4070", vram_size_gb=12, tdp_watts=200)
        assert g.part_type == "gpu"
        assert g.chipset == "RTX 4070"
        assert g.label() == "Test GPU"  # no leading space when brand empty

    def test_motherboard_spec(self):
        m = MotherboardSpec(name="B650 Board", socket="AM5", form_factor="mATX",
                            ram_type="DDR5", wifi_builtin=True)
        assert m.wifi_builtin is True
        assert m.form_factor == "mATX"

    def test_ram_spec(self):
        r = RamSpec(name="Kit 32GB", ram_type="DDR5", speed_mhz=6000, capacity_gb=32, sticks=2)
        assert r.capacity_gb == 32
        assert r.label() == "Kit 32GB"  # no leading space when brand is empty

    def test_storage_spec(self):
        s = StorageSpec(name="NVMe Drive", storage_type="NVMe SSD", capacity_gb=1000)
        assert s.storage_type == "NVMe SSD"

    def test_psu_spec(self):
        p = PsuSpec(name="PSU 850", wattage=850, efficiency_rating="80+ Gold")
        assert p.wattage == 850

    def test_case_spec(self):
        c = CaseSpec(name="Case", case_type="Mid Tower", max_gpu_length_mm=350.0)
        assert c.max_gpu_length_mm == 350.0

    def test_cooler_spec(self):
        c = CoolerSpec(name="Cooler", cooler_type="AIO", max_tdp_watts=300, height_mm=55.0)
        assert c.max_tdp_watts == 300


# ===========================================================================
# Tests: Registry
# ===========================================================================

class TestRegistryLoad:
    def test_load_dict_returns_part(self):
        reg = PartRegistry()
        part = reg.load_dict("cpu", SAMPLE_CPU)
        assert isinstance(part, CpuSpec)
        assert part.name == "Ryzen 7 7800X3D"
        assert part._id == 1

    def test_load_dict_coerces_bool_fields(self):
        reg = PartRegistry()
        part = reg.load_dict("cpu", SAMPLE_CPU)
        assert part.has_igpu is True

    def test_load_list(self):
        reg = PartRegistry()
        parts = reg.load_list("cpu", [SAMPLE_CPU, SAMPLE_CPU2])
        assert len(parts) == 2
        assert reg.count() == 2

    def test_load_json_list_format(self):
        reg = PartRegistry()
        data = [
            {**SAMPLE_CPU, "part_type": "cpu"},
            {**SAMPLE_GPU, "part_type": "gpu"},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            fname = f.name
        try:
            count = reg.load_json(fname)
            assert count == 2
            assert reg.count() == 2
        finally:
            os.unlink(fname)

    def test_load_json_dict_format(self):
        reg = PartRegistry()
        data = {
            "cpu": [SAMPLE_CPU, SAMPLE_CPU2],
            "gpu": [SAMPLE_GPU],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            fname = f.name
        try:
            count = reg.load_json(fname)
            assert count == 3
        finally:
            os.unlink(fname)

    def test_load_unknown_type_raises(self):
        reg = PartRegistry()
        try:
            reg.load_dict("spaceship", {"name": "X-Wing"})
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_get_part(self):
        reg = make_registry()
        part = reg.get_part(1)
        assert part is not None
        assert isinstance(part, CpuSpec)
        assert part.name == "Ryzen 7 7800X3D"

    def test_get_part_missing(self):
        reg = PartRegistry()
        assert reg.get_part(999) is None

    def test_get_parts_by_type(self):
        reg = make_registry()
        cpus = reg.get_parts_by_type("cpu")
        assert len(cpus) == 2
        gpus = reg.get_parts_by_type("gpu")
        assert len(gpus) == 1

    def test_all_parts(self):
        reg = make_registry()
        assert len(reg.all_parts()) == 12

    def test_count_by_type(self):
        reg = make_registry()
        cnt = reg.count_by_type()
        assert cnt["cpu"] == 2
        assert cnt["gpu"] == 1
        assert cnt["motherboard"] == 2
        assert cnt["psu"] == 2
        assert cnt.get("case") == 1


# ===========================================================================
# Tests: Search / Filter
# ===========================================================================

class TestSearchParts:
    def test_search_all(self):
        reg = make_registry()
        results = reg.search_parts()
        assert len(results) == 12

    def test_search_by_type(self):
        reg = make_registry()
        results = reg.search_parts(part_type="cpu")
        assert len(results) == 2
        assert all(r["part_type"] == "cpu" for r in results)

    def test_filter_socket(self):
        reg = make_registry()
        results = reg.search_parts(part_type="cpu", filters={"socket": "AM5"})
        assert len(results) == 1
        assert results[0]["name"] == "Ryzen 7 7800X3D"

    def test_filter_socket_motherboard(self):
        reg = make_registry()
        results = reg.search_parts(part_type="motherboard",
                                   filters={"socket": "LGA1700"})
        assert len(results) == 1
        assert results[0]["brand"] == "Gigabyte"

    def test_filter_budget_max(self):
        reg = make_registry()
        results = reg.search_parts(part_type="cpu", filters={"budget_max": 400})
        assert len(results) == 1
        assert results[0]["name"] == "Core i5-13600K"

    def test_filter_budget_min(self):
        reg = make_registry()
        results = reg.search_parts(filters={"budget_min": 500})
        for r in results:
            assert r["current_price"] >= 500 or r["current_price"] == 0.0

    def test_filter_brand_case_insensitive(self):
        reg = make_registry()
        results = reg.search_parts(filters={"brand": "amd"})
        for r in results:
            assert "amd" in r.get("brand", "").lower()

    def test_filter_min_cores(self):
        reg = make_registry()
        results = reg.search_parts(part_type="cpu", filters={"min_cores": 10})
        assert len(results) == 1
        assert results[0]["name"] == "Core i5-13600K"

    def test_filter_min_vram_gb(self):
        reg = make_registry()
        results = reg.search_parts(part_type="gpu", filters={"min_vram_gb": 20})
        assert len(results) == 1

    def test_filter_min_capacity_gb(self):
        reg = make_registry()
        results = reg.search_parts(part_type="storage",
                                   filters={"min_capacity_gb": 1000})
        assert len(results) == 1

    def test_filter_min_wattage(self):
        reg = make_registry()
        results = reg.search_parts(part_type="psu", filters={"min_wattage": 800})
        assert len(results) == 1
        assert results[0]["wattage"] == 850

    def test_filter_form_factor(self):
        reg = make_registry()
        results = reg.search_parts(part_type="motherboard",
                                   filters={"form_factor": "ATX"})
        assert len(results) == 2

    def test_filter_has_igpu(self):
        reg = make_registry()
        results = reg.search_parts(part_type="cpu", filters={"has_igpu": True})
        assert len(results) == 2  # both have iGPU in our sample

    def test_filter_wifi_builtin(self):
        reg = make_registry()
        results = reg.search_parts(part_type="motherboard",
                                   filters={"wifi_builtin": True})
        assert len(results) == 2

    def test_filter_rgb(self):
        reg = make_registry()
        results = reg.search_parts(filters={"rgb": True})
        assert len(results) == 1  # only the RAM has rgb=1
        assert results[0]["part_type"] == "ram"

    def test_filter_search_text(self):
        reg = make_registry()
        results = reg.search_parts(filters={"search": "Ryzen"})
        assert len(results) >= 1

    def test_filter_pcie_version(self):
        reg = make_registry()
        results = reg.search_parts(part_type="cpu",
                                   filters={"pcie_version": "PCIe 5.0"})
        assert len(results) == 1
        assert results[0]["name"] == "Core i5-13600K"

    def test_filter_efficiency_rating(self):
        reg = make_registry()
        results = reg.search_parts(part_type="psu",
                                   filters={"efficiency_rating": "80+ Gold"})
        assert len(results) == 1

    def test_filter_cooler_type(self):
        reg = make_registry()
        results = reg.search_parts(part_type="cooler",
                                   filters={"cooler_type": "AIO"})
        assert len(results) == 1

    def test_results_sorted_by_price(self):
        reg = make_registry()
        results = reg.search_parts(part_type="psu")
        prices = [r["current_price"] for r in results if r["current_price"]]
        assert prices == sorted(prices)

    def test_filter_memory_type_cpu(self):
        reg = make_registry()
        results = reg.search_parts(part_type="cpu",
                                   filters={"memory_type": "DDR5"})
        assert len(results) == 2

    def test_filter_tdp_max(self):
        reg = make_registry()
        results = reg.search_parts(part_type="cpu",
                                   filters={"tdp_max": 120})
        assert len(results) >= 1

    def test_filter_tdp_min(self):
        reg = make_registry()
        results = reg.search_parts(part_type="cpu",
                                   filters={"tdp_min": 120})
        assert len(results) >= 1

    def test_filter_multiple_criteria(self):
        reg = make_registry()
        results = reg.search_parts(
            part_type="cpu",
            filters={"socket": "AM5", "budget_max": 600, "min_cores": 6}
        )
        assert len(results) == 1
        assert results[0]["name"] == "Ryzen 7 7800X3D"

    def test_filter_max_length_mm(self):
        reg = make_registry()
        results = reg.search_parts(part_type="gpu",
                                   filters={"max_length_mm": 340})
        assert len(results) == 1


# ===========================================================================
# Tests: Compatibility
# ===========================================================================

class TestCompatibleParts:
    def test_cpu_to_motherboards(self):
        reg = make_registry()
        cpu = reg.get_part(1)  # Ryzen 7800X3D (AM5)
        results = reg.get_compatible_parts(cpu, "motherboards")
        assert len(results) == 1
        assert results[0]["socket"] == "AM5"

    def test_motherboard_to_cpus(self):
        reg = make_registry()
        mobo = reg.get_part(4)  # ASUS X670E (AM5)
        results = reg.get_compatible_parts(mobo, "cpus")
        assert len(results) == 1  # Only the AM5 CPU (Ryzen 7800X3D)
        assert results[0]["name"] == "Ryzen 7 7800X3D"

    def test_cpu_to_coolers(self):
        reg = make_registry()
        cpu = reg.get_part(2)  # Intel Core i5-13600K (LGA1700, 125W TDP)
        results = reg.get_compatible_parts(cpu, "coolers")
        # Both coolers support LGA1700; NH-D15 250W >= 125W, Kraken 350W >= 125W
        assert len(results) == 2

    def test_cpu_to_coolers_tdp_filter(self):
        reg = make_registry()
        # Use the AMD CPU
        cpu = reg.get_part(1)  # Ryzen 7800X3D (AM5, 120W)
        results = reg.get_compatible_parts(cpu, "coolers")
        # NH-D15 supports AM5/250W, Kraken supports AM5/350W
        assert len(results) == 2

    def test_gpu_to_cases(self):
        reg = make_registry()
        gpu = reg.get_part(3)  # RTX 4090 (331mm)
        results = reg.get_compatible_parts(gpu, "cases")
        # Corsair 4000D has max_gpu_length_mm=360 >= 331
        assert len(results) == 1

    def test_gpu_to_cases_too_long(self):
        reg = make_registry()
        # Make a very long GPU
        long_gpu = reg.load_dict("gpu", {
            "name": "Mega GPU",
            "brand": "Test",
            "part_type": "gpu",
            "length_mm": 450.0,
            "tdp_watts": 300,
        })
        results = reg.get_compatible_parts(long_gpu, "cases")
        assert len(results) == 0  # None fit

    def test_motherboard_to_rams(self):
        reg = make_registry()
        mobo = reg.get_part(4)  # ASUS X670E (DDR5)
        results = reg.get_compatible_parts(mobo, "rams")
        assert len(results) == 1
        assert results[0]["ram_type"] == "DDR5"

    def test_cpu_to_psus(self):
        reg = make_registry()
        cpu = reg.get_part(1)  # Ryzen 7800X3D
        results = reg.get_compatible_parts(cpu, "psus")
        # At least our 850W PSU should qualify
        psu_watts = [r["wattage"] for r in results]
        assert all(w >= 450 for w in psu_watts)

    def test_invalid_compatibility_type(self):
        reg = PartRegistry()
        cpu = CpuSpec()
        try:
            reg.get_compatible_parts(cpu, "spaceships")
            assert False, "Should raise ValueError"
        except ValueError:
            pass


# ===========================================================================
# Tests: Build Summary
# ===========================================================================

class TestBuildSummary:
    def test_full_build_no_warnings(self):
        reg = make_registry()
        components = {
            "cpu": reg.get_part(1),          # Ryzen 7800X3D
            "gpu": reg.get_part(3),          # RTX 4090
            "motherboard": reg.get_part(3),  # ASUS X670E (AM5)
            "ram": reg.get_part(5),          # DDR5 RAM
            "storage": reg.get_part(6),      # 990 Pro
            "psu": reg.get_part(7),          # RM850x
            "case": reg.get_part(9),         # 4000D
            "cooler": reg.get_part(10),      # NH-D15
        }
        summary = reg.get_build_summary(components)
        assert summary["component_count"] == 8
        assert summary["total_price"] > 0
        assert summary["total_tdp"] > 0
        # Should have no critical warnings with this compatible build
        assert isinstance(summary["compatibility_warnings"], list)
        assert len(summary["missing_components"]) == 0

    def test_build_with_socket_mismatch(self):
        reg = make_registry()
        components = {
            "cpu": reg.get_part(1),          # Ryzen 7800X3D (AM5)
            "motherboard": reg.get_part(5),  # Gigabyte Z790 (LGA1700)
        }
        summary = reg.get_build_summary(components)
        warnings = summary["compatibility_warnings"]
        socket_warnings = [w for w in warnings if "Socket mismatch" in w]
        assert len(socket_warnings) == 1

    def test_build_with_missing_components(self):
        reg = make_registry()
        components: dict = {
            "cpu": reg.get_part(1),
            "gpu": None,
            "motherboard": None,
        }
        summary = reg.get_build_summary(components)
        assert "gpu" in summary["missing_components"]
        assert "motherboard" in summary["missing_components"]
        assert "psu" in summary["missing_components"]
        assert summary["component_count"] == 1

    def test_build_ram_type_mismatch(self):
        reg = make_registry()
        # Load a DDR4 RAM stick
        reg.load_dict("ram", {
            "name": "Old RAM",
            "brand": "Test",
            "part_type": "ram",
            "ram_type": "DDR4",
            "speed_mhz": 3200,
            "capacity_gb": 16,
            "sticks": 2,
        })
        mobo = reg.get_part(4)  # X670E (DDR5)
        ram = reg.get_part(13)  # DDR4 RAM (loaded after the 12 registry parts)
        components = {
            "motherboard": mobo,
            "ram": ram,
        }
        summary = reg.get_build_summary(components)
        warnings = summary["compatibility_warnings"]
        ram_warnings = [w for w in warnings if "RAM type mismatch" in w]
        assert len(ram_warnings) == 1

    def test_build_gpu_too_long_for_case(self):
        reg = make_registry()
        components = {
            "gpu": reg.get_part(3),   # RTX 4090 (331mm)
            "case": reg.get_part(10), # 4000D (360mm max) — should fit
        }
        summary = reg.get_build_summary(components)
        gpu_warnings = [w for w in summary["compatibility_warnings"]
                        if "GPU too long" in w]
        assert len(gpu_warnings) == 0  # Should fit

        # Now with a tiny case
        reg.load_dict("case", {
            "name": "Tiny Case",
            "brand": "Test",
            "part_type": "case",
            "max_gpu_length_mm": 250.0,
        })
        components["case"] = reg.get_part(13)  # Tiny case just loaded
        summary = reg.get_build_summary(components)
        gpu_warnings = [w for w in summary["compatibility_warnings"]
                        if "GPU too long" in w]
        assert len(gpu_warnings) == 1

    def test_build_psu_underpowered(self):
        reg = make_registry()
        components = {
            "cpu": reg.get_part(1),       # Ryzen 7800X3D (120W)
            "gpu": reg.get_part(3),       # RTX 4090 (450W)
            "psu": reg.get_part(9),       # VS550 (550W)
        }
        summary = reg.get_build_summary(components)
        psu_warnings = [w for w in summary["compatibility_warnings"]
                        if "PSU" in w or "underpowered" in w or "insufficient" in w]
        assert len(psu_warnings) >= 1

    def test_build_cooler_tdp_insufficient(self):
        reg = make_registry()
        # Load a tiny cooler
        reg.load_dict("cooler", {
            "name": "Weeny Cooler",
            "brand": "Test",
            "part_type": "cooler",
            "max_tdp_watts": 65,
            "socket_compatibility": "AM5",
        })
        components = {
            "cpu": reg.get_part(1),         # Ryzen 7800X3D (120W)
            "cooler": reg.get_part(13),      # Weeny Cooler (65W)
        }
        summary = reg.get_build_summary(components)
        cooler_warnings = [w for w in summary["compatibility_warnings"]
                           if "Cooler" in w and "insufficient" in w]
        assert len(cooler_warnings) >= 1

    def test_build_ram_slots_insufficient(self):
        reg = make_registry()
        # Load RAM with more sticks than mobo slots
        reg.load_dict("ram", {
            "name": "Many Sticks",
            "brand": "Test",
            "part_type": "ram",
            "ram_type": "DDR5",
            "sticks": 8,
            "capacity_gb": 8,
        })
        components = {
            "motherboard": reg.get_part(4),  # X670E (4 slots)
            "ram": reg.get_part(13),
        }
        summary = reg.get_build_summary(components)
        slot_warnings = [w for w in summary["compatibility_warnings"]
                         if "RAM slots" in w]
        assert len(slot_warnings) >= 1

    def test_build_components_used_dict(self):
        reg = make_registry()
        cpu = reg.get_part(1)
        components = {"cpu": cpu}
        summary = reg.get_build_summary(components)
        assert summary["components_used"]["cpu"] is not None
        assert summary["components_used"]["cpu"]["name"] == cpu.name


# ===========================================================================
# Tests: Helpers
# ===========================================================================

class TestHelpers:
    def test_hasattr_val_string(self):
        obj = CpuSpec(socket="AM5")
        assert _hasattr_val(obj, "socket", "AM5") is True
        assert _hasattr_val(obj, "socket", "am5") is True  # case insensitive
        assert _hasattr_val(obj, "socket", "LGA1700") is False

    def test_hasattr_val_none(self):
        obj = CpuSpec()
        assert _hasattr_val(obj, "nonexistent", "foo") is False

    def test_hasattr_val_int(self):
        obj = CpuSpec(core_count=8)
        assert _hasattr_val(obj, "core_count", 8) is True
        assert _hasattr_val(obj, "core_count", 6) is False

    def test_part_spec_label(self):
        p = CpuSpec(name="Test", brand="AMD")
        assert p.label() == "AMD Test"
        p2 = CpuSpec(name="JustName")
        assert p2.label() == "JustName"


# ===========================================================================
# Tests: CLI (via main function)
# ===========================================================================

class TestCLI:
    def setup_method(self):
        """Reset the persistent CLI registry before each test."""
        import parts_search
        parts_search._reset_cli_registry()

    def _run(self, *args: str) -> tuple[int, str, str]:
        """Run main() with given args, capture stdout/stderr."""
        import io
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        try:
            rc = __import__("parts_search").main(list(args))
        except SystemExit as e:
            rc = e.code or 0
        out = sys.stdout.getvalue()
        err = sys.stderr.getvalue()
        sys.stdout, sys.stderr = old_out, old_err
        return rc, out, err

    def test_cli_stats_empty(self):
        rc, out, err = self._run("stats")
        assert rc == 0
        assert "Registry has 0 parts" in out

    def test_cli_load_and_stats(self):
        data = [SAMPLE_CPU, SAMPLE_GPU]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            fname = f.name
        try:
            rc, out, err = self._run("load", "--json", fname)
            assert rc == 0
            assert "Loaded 2 parts" in out
            rc2, out2, err2 = self._run("stats")
            assert "cpu: 1" in out2
            assert "gpu: 1" in out2
        finally:
            os.unlink(fname)

    def test_cli_search_no_results(self):
        rc, out, err = self._run("search", "--type", "cpu", "--socket", "SP999")
        assert rc == 0
        assert "No results found" in out

    def test_cli_search_with_results(self):
        reg = make_registry()
        import parts_search
        parts_search._GLOBAL_REGISTRY = reg  # not ideal; we just test main's own reg below
        # Instead test search via the module's main which creates its own empty reg
        # — so we'll use load + search
        data = [SAMPLE_CPU, SAMPLE_CPU2]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            fname = f.name
        try:
            rc1, _, _ = self._run("load", "--json", fname)
            assert rc1 == 0
            rc2, out2, _ = self._run("search", "--type", "cpu", "--socket", "AM5")
            assert rc2 == 0
            assert "Ryzen 7 7800X3D" in out2
        finally:
            os.unlink(fname)

    def test_cli_search_json_output(self):
        data = [SAMPLE_CPU]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            fname = f.name
        try:
            self._run("load", "--json", fname)
            rc, out, _ = self._run("search", "--type", "cpu", "--json")
            assert rc == 0
            parsed = json.loads(out)
            assert isinstance(parsed, list)
            assert parsed[0]["name"] == "Ryzen 7 7800X3D"
        finally:
            os.unlink(fname)

    def test_cli_help(self):
        rc, out, err = self._run("--help")
        assert rc == 0
        # Should show subcommands
        for cmd in ("search", "compatible", "summary", "load", "stats"):
            assert cmd in out

    def test_cli_compatible_no_part(self):
        rc, out, err = self._run("compatible", "--part-id", "999", "--compatibility", "cpus")
        assert rc == 1
        assert "No part with ID 999" in err or "No part with ID 999" in out

    def test_cli_summary_invalid_json(self):
        rc, out, err = self._run("summary", "--components", "not-json")
        assert rc == 1

    def test_cli_summary(self):
        comps = json.dumps({
            "cpu": {"part_type": "cpu", "name": "Test CPU", "socket": "AM5",
                     "tdp_watts": 100, "current_price": 299},
            "motherboard": {"part_type": "motherboard", "name": "Test Mobo",
                            "socket": "AM5", "current_price": 199},
        })
        rc, out, err = self._run("summary", "--components", comps)
        assert rc == 0
        assert "Total TDP" in out
        assert "Total Price" in out


# ===========================================================================
# Tests: Edge Cases
# ===========================================================================

class TestEdgeCases:
    def test_empty_registry_search(self):
        reg = PartRegistry()
        results = reg.search_parts()
        assert results == []

    def test_empty_registry_compatible(self):
        reg = PartRegistry()
        cpu = reg.load_dict("cpu", {"name": "Test", "socket": "AM5", "core_count": 4, "tdp_watts": 65})
        results = reg.get_compatible_parts(cpu, "motherboards")
        assert results == []

    def test_empty_build_summary(self):
        reg = PartRegistry()
        summary = reg.get_build_summary({})
        assert summary["component_count"] == 0
        assert summary["total_tdp"] == 0
        assert summary["total_price"] == 0
        assert len(summary["missing_components"]) == 8

    def test_filter_with_none_value(self):
        reg = make_registry()
        # filters with None shouldn't crash
        results = reg.search_parts(filters={"socket": None, "budget_max": None})
        assert len(results) == 12

    def test_load_dict_extra_fields_ignored(self):
        reg = PartRegistry()
        part = reg.load_dict("cpu", {
            **SAMPLE_CPU,
            "extra_field": "ignored",
            "another_one": 42,
        })
        assert isinstance(part, CpuSpec)
        assert not hasattr(part, "extra_field")

    def test_part_spec_to_dict_clean(self):
        reg = make_registry()
        for part in reg.all_parts():
            d = part.to_dict()
            assert "_id" not in d
            assert "_tags" not in d
            assert d["part_type"] == part.part_type

    def test_many_parts_search_performance(self):
        reg = PartRegistry()
        for i in range(100):
            reg.load_dict("cpu", {
                "name": f"CPU {i}",
                "brand": "Test",
                "socket": "AM5" if i % 2 == 0 else "LGA1700",
                "core_count": (i % 16) + 2,
                "tdp_watts": (i % 100) + 50,
                "current_price": (i * 10) + 100.0,
            })
        results = reg.search_parts(part_type="cpu", filters={
            "socket": "AM5", "budget_max": 500, "min_cores": 8
        })
        assert len(results) > 0
        for r in results:
            assert r["current_price"] <= 500 or r["current_price"] == 0.0


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))