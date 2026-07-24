#!/usr/bin/env python3
"""
PC Design Agent — Parts Search Tool

A Python module that searches PC components by type, socket, budget, or other criteria.
Supports 13 tables from the component knowledge graph schema: parts (unified registry)
plus 8 detail tables (cpu, gpu, motherboard, ram, storage, psu, case, cooler).

Provides:
  - Dataclass hierarchy mirroring the SQL schema
  - In-memory PartRegistry that can be populated from dicts/JSON
  - search_parts()  — search/filter parts by criteria
  - get_compatible_parts() — find compatible parts for a given part
  - get_build_summary() — analyze a full set of build components
  - CLI entry point
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, ClassVar, Optional

# ---------------------------------------------------------------------------
# PartSpec base + 8 component dataclasses (mirrors the SQL schema)
# ---------------------------------------------------------------------------

PART_TYPES = (
    "cpu", "gpu", "motherboard", "ram", "storage", "psu", "case", "cooler"
)

# Map from part_type string to the Spec class
_PART_TYPE_TO_CLASS: dict[str, type] = {}


@dataclass
class PartSpec:
    """Base dataclass — fields common to all parts (mirrors `parts` table)."""
    part_type: str = ""
    name: str = ""
    brand: str = ""
    model: str = ""
    release_date: str = ""
    current_price: float = 0.0
    currency: str = "NZD"
    msrp: float = 0.0
    created_at: str = ""
    updated_at: str = ""
    # Internal tracking
    _id: int = 0
    _tags: set[str] = field(default_factory=set)

    PART_TYPE: ClassVar[str] = ""

    def __post_init__(self) -> None:
        """Auto-set part_type from the PART_TYPE class variable."""
        if not self.part_type and self.PART_TYPE:
            object.__setattr__(self, "part_type", self.PART_TYPE)

    def to_dict(self) -> dict[str, Any]:
        """Convert to flat dict, dropping internal fields."""
        d = dataclasses.asdict(self)
        d.pop("_id", None)
        d.pop("_tags", None)
        return d

    def label(self) -> str:
        return f"{self.brand} {self.name}".strip() or self.name


@dataclass
class CpuSpec(PartSpec):
    PART_TYPE: ClassVar[str] = "cpu"
    socket: str = ""
    architecture: str = ""
    microarchitecture: str = ""
    core_count: int = 0
    thread_count: int = 0
    base_clock_ghz: float = 0.0
    boost_clock_ghz: float = 0.0
    l3_cache_mb: int = 0
    l2_cache_mb: float = 0.0
    tdp_watts: int = 0
    max_tdp_watts: int = 0
    generation: str = ""
    has_igpu: bool = False
    igpu_model: str = ""
    igpu_cores: int = 0
    memory_type: str = ""
    max_memory_gb: int = 0
    max_memory_speed: int = 0
    pcie_version: str = ""
    pcie_lanes: int = 0
    socket_compatible: str = ""
    lithography_nm: int = 0
    smt: bool = True


@dataclass
class GpuSpec(PartSpec):
    PART_TYPE: ClassVar[str] = "gpu"
    chipset: str = ""
    architecture: str = ""
    vram_size_gb: int = 0
    vram_type: str = ""
    vram_bus_width_bits: int = 0
    vram_bandwidth_gbps: float = 0.0
    core_clock_mhz: int = 0
    boost_clock_mhz: int = 0
    tdp_watts: int = 0
    pcie_gen: str = ""
    outputs: str = ""
    max_resolution: str = ""
    length_mm: float = 0.0
    width_mm: float = 0.0
    slot_width: int = 0
    power_connectors: str = ""
    recommended_psu_w: int = 0
    cuda_cores: int = 0
    tensor_cores: int = 0
    rt_cores: int = 0
    stream_processors: int = 0
    compute_units: int = 0
    dlss_version: str = ""
    directx_support: str = ""
    vulkan_support: str = ""


@dataclass
class MotherboardSpec(PartSpec):
    PART_TYPE: ClassVar[str] = "motherboard"
    socket: str = ""
    chipset: str = ""
    form_factor: str = ""
    ram_slots: int = 0
    max_ram_gb: int = 0
    ram_type: str = ""
    max_ram_speed_mhz: int = 0
    pcie_x16_slots: int = 0
    pcie_x8_slots: int = 0
    pcie_x4_slots: int = 0
    pcie_x1_slots: int = 0
    pcie_version: str = ""
    m2_slots: int = 0
    m2_specs: str = ""
    sata_ports: int = 0
    sata_raid_support: bool = False
    wifi_builtin: bool = False
    wifi_spec: str = ""
    bluetooth_spec: str = ""
    audio_chipset: str = ""
    audio_channels: int = 0
    vrm_phase_count: int = 0
    vrm_rating: str = ""
    ethernet_speed: str = ""
    usb_c_rear: int = 0
    usb_a_rear: int = 0
    usb_c_front: int = 0
    usb_a_front: int = 0
    io_ports: str = ""
    bios_flashback: bool = False
    rgb_headers: int = 0
    argb_headers: int = 0


@dataclass
class RamSpec(PartSpec):
    PART_TYPE: ClassVar[str] = "ram"
    ram_type: str = ""
    speed_mhz: int = 0
    capacity_gb: int = 0
    sticks: int = 0
    voltage_v: float = 0.0
    cas_latency: str = ""
    first_word_latency_ns: float = 0.0
    timings: str = ""
    heat_spreader: bool = False
    height_mm: float = 0.0
    rgb: bool = False
    ecc: bool = False
    registered: bool = False
    dual_rank: bool = False
    xmp_support: bool = False
    expo_support: bool = False
    die_type: str = ""


@dataclass
class StorageSpec(PartSpec):
    PART_TYPE: ClassVar[str] = "storage"
    storage_type: str = ""
    capacity_gb: int = 0
    form_factor: str = ""
    interface: str = ""
    nand_type: str = ""
    nand_layers: int = 0
    dram_cache: bool = False
    dram_cache_size_mb: int = 0
    hmb_support: bool = False
    read_speed_mbs: int = 0
    write_speed_mbs: int = 0
    random_read_iops: int = 0
    random_write_iops: int = 0
    endurance_tbw: int = 0
    endurance_dwpd: float = 0.0
    warranty_years: int = 0
    height_mm: float = 0.0
    controller: str = ""
    nvme_version: str = ""
    encryption: bool = False
    rpm: int = 0


@dataclass
class PsuSpec(PartSpec):
    PART_TYPE: ClassVar[str] = "psu"
    wattage: int = 0
    efficiency_rating: str = ""
    modular_type: str = ""
    form_factor: str = ""
    length_mm: float = 0.0
    width_mm: float = 0.0
    height_mm: float = 0.0
    fan_size_mm: int = 0
    fanless_mode: bool = False
    fan_bearing: str = ""
    atx_24pin: int = 1
    cpu_4plus4pin: int = 1
    cpu_8pin: int = 0
    pcie_6plus2pin: int = 0
    pcie_12vhpwr: int = 0
    sata_connectors: int = 0
    molex_connectors: int = 0
    single_rail: bool = True
    rail_amps: int = 0
    active_pfc: bool = True
    rated_voltage_ac: str = ""
    standby_efficiency: str = ""
    protection_features: str = ""
    atx_30_compliant: bool = False
    zero_rpm_mode: bool = False


@dataclass
class CaseSpec(PartSpec):
    PART_TYPE: ClassVar[str] = "case"
    case_type: str = ""
    motherboard_support: str = ""
    psu_form_factor: str = ""
    max_psu_length_mm: float = 0.0
    max_gpu_length_mm: float = 0.0
    max_gpu_width_mm: float = 0.0
    max_cpu_cooler_height_mm: float = 0.0
    material: str = ""
    side_panel: str = ""
    weight_kg: float = 0.0
    dimensions_wxhxd_mm: str = ""
    volume_litres: float = 0.0
    fan_slots: str = ""
    included_fans: str = ""
    max_fan_count: int = 0
    radiator_support: str = ""
    drive_bays_35: int = 0
    drive_bays_25: int = 0
    drive_bays_35_ext: int = 0
    usb_c_front: int = 0
    usb_a_front: int = 0
    usb_type: str = ""
    audio_jack: bool = True
    dust_filters: int = 0
    cable_routing: int = 0
    gpu_vertical_mount: bool = False
    gpu_anti_sag: bool = False


@dataclass
class CoolerSpec(PartSpec):
    PART_TYPE: ClassVar[str] = "cooler"
    cooler_type: str = ""
    height_mm: float = 0.0
    width_mm: float = 0.0
    depth_mm: float = 0.0
    radiator_size_mm: int = 0
    radiator_thickness_mm: float = 0.0
    fan_count: int = 0
    fan_size_mm: int = 0
    fan_speed_rpm: str = ""
    fan_noise_dba: float = 0.0
    airflow_cfm: float = 0.0
    static_pressure_mmh2o: float = 0.0
    fan_bearing: str = ""
    max_tdp_watts: int = 0
    socket_compatibility: str = ""
    rgb: bool = False
    pwm: bool = True
    material: str = ""
    heatpipe_count: int = 0
    heatpipe_diameter_mm: float = 0.0
    base_plate: str = ""
    pump_speed_rpm: str = ""
    pump_noise_dba: float = 0.0
    lcd_display: bool = False
    warranty_years: int = 0
    pre_applied_paste: bool = True
    offset_mount: bool = False


# Build the part-type → class registry automatically
for _cls in PartSpec.__subclasses__():
    if hasattr(_cls, "PART_TYPE") and _cls.PART_TYPE:
        _PART_TYPE_TO_CLASS[_cls.PART_TYPE] = _cls


# ---------------------------------------------------------------------------
# Part Registry — in-memory store that can be populated from dicts / JSON
# ---------------------------------------------------------------------------


class PartRegistry:
    """An in-memory registry of PC components.

    Supports loading from dicts (e.g. from YAML/JSON) and provides all
    search/filter/compatibility operations.  Does NOT require a real database.
    """

    def __init__(self) -> None:
        self._parts: dict[int, PartSpec] = {}        # id → part
        self._by_type: dict[str, list[PartSpec]] = defaultdict(list)
        self._next_id: int = 1
        # Compatibility edges stored similarly to compatibility_rules table
        self._compat_rules: list[dict] = []  # {part_id, compatible_part_id, compat_type, direction}

    # -- Loading ------------------------------------------------------------

    def load_dict(self, part_type: str, data: dict[str, Any]) -> PartSpec:
        """Load a single part from a dict, auto-detecting the correct dataclass."""
        cls = _PART_TYPE_TO_CLASS.get(part_type)
        if cls is None:
            raise ValueError(f"Unknown part_type '{part_type}'. Valid: {', '.join(PART_TYPES)}")

        # Filter to only fields the dataclass knows about
        valid_fields = {f.name for f in dataclasses.fields(cls)}
        kwargs = {k: v for k, v in data.items() if k in valid_fields}
        kwargs.setdefault("part_type", part_type)

        # Coerce has_igpu, smt, etc. from int → bool
        for field_name in list(kwargs):
            if field_name in ("has_igpu", "smt", "wifi_builtin", "sata_raid_support",
                              "bios_flashback", "heat_spreader", "rgb", "ecc",
                              "registered", "dual_rank", "xmp_support", "expo_support",
                              "dram_cache", "hmb_support", "encryption", "fanless_mode",
                              "single_rail", "active_pfc", "atx_30_compliant",
                              "zero_rpm_mode", "audio_jack", "gpu_vertical_mount",
                              "gpu_anti_sag", "pwm", "lcd_display", "pre_applied_paste",
                              "offset_mount"):
                if isinstance(kwargs[field_name], int):
                    kwargs[field_name] = bool(kwargs[field_name])

        part = cls(**kwargs)
        part._id = self._next_id
        self._next_id += 1
        self._parts[part._id] = part
        self._by_type[part_type].append(part)
        return part

    def load_list(self, part_type: str, items: list[dict[str, Any]]) -> list[PartSpec]:
        """Load multiple parts of the same type from a list of dicts."""
        return [self.load_dict(part_type, item) for item in items]

    def load_json(self, json_path: str) -> int:
        """Load parts from a JSON file.  Expects either a list or a dict keyed by part_type.

        Two formats accepted:
          1. [{"part_type": "cpu", ...}, {"part_type": "gpu", ...}, ...]
          2. {"cpu": [{...}, ...], "gpu": [{...}, ...], ...}
        Returns the number of parts loaded.
        """
        with open(json_path) as f:
            raw = json.load(f)

        count = 0
        if isinstance(raw, list):
            # Format 1 — each item has a part_type key
            for item in raw:
                pt = item.get("part_type", "")
                self.load_dict(pt, item)
                count += 1
        elif isinstance(raw, dict):
            # Format 2 — keyed by part_type
            for pt, items in raw.items():
                for item in items:
                    item.setdefault("part_type", pt)
                    self.load_dict(pt, item)
                    count += 1
        return count

    def load_compat_rules(self, rules: list[dict[str, Any]]) -> None:
        """Load compatibility rules: [{part_id, compatible_part_id, compatibility_type, direction?}]"""
        self._compat_rules.extend(rules)

    # -- Querying -----------------------------------------------------------

    def get_part(self, part_id: int) -> Optional[PartSpec]:
        """Retrieve a single part by its internal registry ID."""
        return self._parts.get(part_id)

    def get_parts_by_type(self, part_type: str) -> list[PartSpec]:
        """Get all parts of a given type."""
        return list(self._by_type.get(part_type, []))

    def all_parts(self) -> list[PartSpec]:
        """Return every part in the registry."""
        return list(self._parts.values())

    def count(self) -> int:
        return len(self._parts)

    def count_by_type(self) -> dict[str, int]:
        return {t: len(v) for t, v in self._by_type.items()}

    # -- Search / Filter ----------------------------------------------------

    def search_parts(self, part_type: Optional[str] = None,
                     filters: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        """Search and filter parts by type and criteria.

        Args:
            part_type: One of cpu|gpu|motherboard|ram|storage|psu|case|cooler,
                       or None to search all types.
            filters: Dict of filter criteria.  Supported keys include:
                       socket, budget_max, budget_min, form_factor, tdp_max,
                       tdp_min, memory_type, brand, chipset, min_cores,
                       min_vram_gb, min_speed_mhz, min_capacity_gb,
                       min_wattage, efficiency_rating, modular_type,
                       cooler_type, storage_type, case_type,
                       has_igpu, wifi_builtin, rgb, pcie_version,
                       max_length_mm, min_read_speed_mbs, search (text search)

        Returns:
            Sorted list of matching parts (sorted by current_price ascending)
            as flat dicts with all relevant specs.
        """
        filters = filters or {}

        # 1. Filter by type
        candidates: list[PartSpec]
        if part_type:
            candidates = list(self._by_type.get(part_type, []))
        else:
            candidates = list(self._parts.values())

        # 2. Apply filters
        for key, value in filters.items():
            if value is None:
                continue

            if key == "socket":
                # Match by socket field (on cpu, motherboard, cooler)
                candidates = [
                    p for p in candidates
                    if _hasattr_val(p, "socket", value)
                ]
            elif key == "budget_max":
                candidates = [
                    p for p in candidates
                    if p.current_price <= value or p.current_price == 0.0
                ]
            elif key == "budget_min":
                candidates = [
                    p for p in candidates
                    if p.current_price >= value or p.current_price == 0.0
                ]
            elif key == "form_factor":
                candidates = [
                    p for p in candidates
                    if _hasattr_val(p, "form_factor", value)
                ]
            elif key == "tdp_max":
                # Check both tdp_watts and max_tdp_watts
                candidates = [
                    p for p in candidates
                    if (getattr(p, "tdp_watts", 99999) <= value
                        or getattr(p, "max_tdp_watts", 0) <= value
                        or getattr(p, "max_tdp_watts", 0) == 0)
                ]
            elif key == "tdp_min":
                candidates = [
                    p for p in candidates
                    if getattr(p, "tdp_watts", 0) >= value
                ]
            elif key == "memory_type":
                candidates = [
                    p for p in candidates
                    if _hasattr_val(p, "memory_type", value)
                    or _hasattr_val(p, "ram_type", value)
                ]
            elif key == "brand":
                candidates = [
                    p for p in candidates
                    if p.brand and value.lower() in p.brand.lower()
                ]
            elif key == "chipset":
                candidates = [
                    p for p in candidates
                    if _hasattr_val(p, "chipset", value)
                ]
            elif key == "min_cores":
                candidates = [
                    p for p in candidates
                    if getattr(p, "core_count", 0) >= value
                ]
            elif key == "min_vram_gb":
                candidates = [
                    p for p in candidates
                    if getattr(p, "vram_size_gb", 0) >= value
                ]
            elif key == "min_speed_mhz":
                candidates = [
                    p for p in candidates
                    if getattr(p, "speed_mhz", 0) >= value
                    or getattr(p, "max_ram_speed_mhz", 0) >= value
                ]
            elif key == "min_capacity_gb":
                # For RAM (capacity_gb) and Storage (capacity_gb)
                candidates = [
                    p for p in candidates
                    if getattr(p, "capacity_gb", 0) >= value
                ]
            elif key == "min_wattage":
                candidates = [
                    p for p in candidates
                    if getattr(p, "wattage", 0) >= value
                ]
            elif key == "efficiency_rating":
                candidates = [
                    p for p in candidates
                    if _hasattr_val(p, "efficiency_rating", value)
                ]
            elif key == "modular_type":
                candidates = [
                    p for p in candidates
                    if _hasattr_val(p, "modular_type", value)
                ]
            elif key == "cooler_type":
                candidates = [
                    p for p in candidates
                    if _hasattr_val(p, "cooler_type", value)
                ]
            elif key == "storage_type":
                candidates = [
                    p for p in candidates
                    if _hasattr_val(p, "storage_type", value)
                ]
            elif key == "case_type":
                candidates = [
                    p for p in candidates
                    if _hasattr_val(p, "case_type", value)
                ]
            elif key == "has_igpu":
                want = bool(value)
                candidates = [
                    p for p in candidates
                    if p.part_type == "cpu" and getattr(p, "has_igpu", False) == want
                ]
            elif key == "wifi_builtin":
                want = bool(value)
                candidates = [
                    p for p in candidates
                    if p.part_type == "motherboard" and getattr(p, "wifi_builtin", False) == want
                ]
            elif key == "rgb":
                want = bool(value)
                candidates = [
                    p for p in candidates
                    if getattr(p, "rgb", False) == want
                ]
            elif key == "pcie_version":
                candidates = [
                    p for p in candidates
                    if _hasattr_val(p, "pcie_version", value)
                ]
            elif key == "max_length_mm":
                candidates = [
                    p for p in candidates
                    if getattr(p, "length_mm", 99999) <= value or getattr(p, "length_mm", 0) == 0.0
                ]
            elif key == "min_read_speed_mbs":
                candidates = [
                    p for p in candidates
                    if getattr(p, "read_speed_mbs", 0) >= value
                ]
            elif key == "search":
                # Full-text-ish search across name, brand, model
                q = value.lower()
                candidates = [
                    p for p in candidates
                    if q in p.name.lower()
                    or q in (p.brand or "").lower()
                    or q in (p.model or "").lower()
                ]

        # 3. Sort by price ascending
        candidates.sort(key=lambda p: (p.current_price or 0.0, p.name))

        # 4. Convert to dicts with all relevant fields
        return [p.to_dict() for p in candidates]

    # -- Compatibility ------------------------------------------------------

    def get_compatible_parts(self, part: PartSpec,
                             compatibility_type: str) -> list[dict[str, Any]]:
        """Given a part, return compatible parts for the given compatibility_type.

        Args:
            part: The source part (a PartSpec instance from this registry).
            compatibility_type: One of:
                'motherboards' — for a CPU, find mobos with same socket
                'cpus' — for a mobo, find CPUs with same socket
                'coolers' — for a CPU, find coolers that fit socket + TDP
                'cases' — for a GPU, find cases with sufficient clearance
                'rams' — for a motherboard, find RAM with matching DDR type
                'psus' — for any build part, find PSUs with sufficient wattage

        Returns:
            Sorted list of matching parts (by current_price) as flat dicts.
        """
        compat_type_map = {
            "motherboards": "motherboard",
            "cpus": "cpu",
            "coolers": "cooler",
            "cases": "case",
            "rams": "ram",
            "psus": "psu",
        }

        target_type = compat_type_map.get(compatibility_type)
        if target_type is None:
            raise ValueError(
                f"Unknown compatibility_type '{compatibility_type}'. "
                f"Valid: {', '.join(compat_type_map)}"
            )

        candidates = self._by_type.get(target_type, [])
        results: list[PartSpec] = []

        if compatibility_type == "motherboards":
            # CPU → Motherboard: same socket
            socket = getattr(part, "socket", None)
            if socket:
                results = [m for m in candidates if getattr(m, "socket", "") == socket]

        elif compatibility_type == "cpus":
            # Motherboard → CPU: same socket
            socket = getattr(part, "socket", None)
            if socket:
                results = [c for c in candidates if getattr(c, "socket", "") == socket]

        elif compatibility_type == "coolers":
            # CPU → Cooler: same socket (via cooler's socket_compatibility JSON or list-like string)
            socket = getattr(part, "socket", None)
            cpu_tdp = getattr(part, "tdp_watts", 0) or getattr(part, "max_tdp_watts", 0) or 99999
            if socket:
                for cooler in candidates:
                    compat_sockets_str = getattr(cooler, "socket_compatibility", "") or ""
                    if socket in compat_sockets_str:
                        cooler_tdp = getattr(cooler, "max_tdp_watts", 0) or 99999
                        if cooler_tdp >= cpu_tdp:
                            results.append(cooler)

        elif compatibility_type == "cases":
            # GPU → Case: check clearance
            gpu_length = getattr(part, "length_mm", 0) or 99999
            for case in candidates:
                max_gpu_len = getattr(case, "max_gpu_length_mm", 0) or 99999
                if max_gpu_len >= gpu_length:
                    results.append(case)

        elif compatibility_type == "rams":
            # Motherboard → RAM: same ram_type
            ram_type = getattr(part, "ram_type", None)
            if ram_type:
                results = [r for r in candidates if getattr(r, "ram_type", "") == ram_type]

        elif compatibility_type == "psus":
            # Any → PSU: wattage >= required
            required_wattage = _estimate_wattage(part, self)
            for psu in candidates:
                psu_w = getattr(psu, "wattage", 0) or 0
                if psu_w >= required_wattage:
                    results.append(psu)

        results.sort(key=lambda p: (p.current_price or 0.0, p.name))
        return [p.to_dict() for p in results]

    # -- Build Summary ------------------------------------------------------

    def get_build_summary(self, components: dict[str, Optional[PartSpec]]) -> dict[str, Any]:
        """Given a dict of {cpu, gpu, motherboard, ram, storage, psu, case, cooler},
        return analysis including total TDP, total price, compatibility warnings,
        and missing components.

        Args:
            components: Dict keyed by component role. Values can be PartSpec or None.

        Returns:
            Dict with keys: total_tdp, total_price, compatibility_warnings (list),
                            missing_components (list), component_count, components_used (dict).
        """
        warnings: list[str] = []
        missing: list[str] = []
        total_tdp = 0
        total_price = 0.0
        used: dict[str, dict] = {}

        ROLE_TYPES = ["cpu", "gpu", "motherboard", "ram", "storage", "psu", "case", "cooler"]

        for role in ROLE_TYPES:
            comp = components.get(role)
            if comp is None:
                missing.append(role)
                used[role] = None
                continue
            used[role] = comp.to_dict()
            total_price += comp.current_price or 0.0

            # Sum TDP (cpu, gpu, maybe others)
            tdp = getattr(comp, "tdp_watts", 0) or 0
            total_tdp += tdp

        # Compatibility checks
        cpu = components.get("cpu")
        mobo = components.get("motherboard")
        gpu = components.get("gpu")
        ram = components.get("ram")
        psu = components.get("psu")
        case = components.get("case")
        cooler = components.get("cooler")

        # CPU ↔ Motherboard socket
        if cpu and mobo:
            cpu_sock = getattr(cpu, "socket", "")
            mobo_sock = getattr(mobo, "socket", "")
            if cpu_sock and mobo_sock and cpu_sock != mobo_sock:
                warnings.append(
                    f"Socket mismatch: CPU ({cpu_sock}) ≠ Motherboard ({mobo_sock})"
                )

        # CPU → Cooler TDP
        if cpu and cooler:
            cpu_tdp = getattr(cpu, "tdp_watts", 0) or getattr(cpu, "max_tdp_watts", 0) or 0
            cooler_tdp = getattr(cooler, "max_tdp_watts", 0) or 0
            if cpu_tdp > cooler_tdp:
                warnings.append(
                    f"Cooler may be insufficient: CPU TDP ({cpu_tdp}W) > Cooler max ({cooler_tdp}W)"
                )

        # CPU → Cooler socket
        if cpu and cooler:
            cpu_sock = getattr(cpu, "socket", "")
            cooler_socks = getattr(cooler, "socket_compatibility", "") or ""
            if cpu_sock and cooler_socks and cpu_sock not in cooler_socks:
                warnings.append(
                    f"Socket mismatch: CPU ({cpu_sock}) not in cooler support list"
                )

        # Motherboard ↔ RAM type
        if mobo and ram:
            mobo_ram = getattr(mobo, "ram_type", "")
            ram_type = getattr(ram, "ram_type", "")
            if mobo_ram and ram_type and mobo_ram != ram_type:
                warnings.append(
                    f"RAM type mismatch: Motherboard ({mobo_ram}) ≠ RAM ({ram_type})"
                )

        # Motherboard → RAM slots + capacity
        if mobo and ram:
            ram_slots = getattr(mobo, "ram_slots", 0) or 0
            if ram_slots > 0 and getattr(ram, "sticks", 0) > ram_slots:
                warnings.append(
                    f"Not enough RAM slots: {getattr(ram, 'sticks', 0)} sticks "
                    f"but motherboard has {ram_slots} slots"
                )

        # Motherboard → CPU generation / chipset hints
        if mobo and cpu:
            mobo_chipset = getattr(mobo, "chipset", "")
            cpu_gen = getattr(cpu, "generation", "")
            # Basic heuristic: AM5 mobos for Ryzen 7000+, LGA1700 for 12th-14th gen Intel
            if mobo_chipset and cpu_gen:
                if "AM5" in mobo_chipset.upper() and "Ryzen" in cpu_gen and "7000" not in cpu_gen and "9000" not in cpu_gen:
                    warnings.append(
                        f"Motherboard chipset ({mobo_chipset}) may not support CPU generation ({cpu_gen})"
                    )

        # GPU → Case clearance
        if gpu and case:
            gpu_len = getattr(gpu, "length_mm", 0) or 0
            max_gpu_len = getattr(case, "max_gpu_length_mm", 0) or 0
            if gpu_len > 0 and max_gpu_len > 0 and gpu_len > max_gpu_len:
                warnings.append(
                    f"GPU too long for case: GPU ({gpu_len}mm) > Case max ({max_gpu_len}mm)"
                )

        # GPU → PSU recommended
        if gpu and psu:
            rec_psu = getattr(gpu, "recommended_psu_w", 0) or 0
            psu_wattage = getattr(psu, "wattage", 0) or 0
            if rec_psu > 0 and psu_wattage > 0 and psu_wattage < rec_psu:
                warnings.append(
                    f"PSU may be insufficient: GPU recommends {rec_psu}W minimum, "
                    f"PSU is {psu_wattage}W"
                )

        # PSU total power check
        if psu and total_tdp > 0:
            psu_wattage = getattr(psu, "wattage", 0) or 0
            if psu_wattage < total_tdp:
                warnings.append(
                    f"PSU underpowered: total TDP ({total_tdp}W) > PSU ({psu_wattage}W) — "
                    f"recommend at least {int(total_tdp * 1.2)}W"
                )

        return {
            "total_tdp": total_tdp,
            "total_price": round(total_price, 2),
            "compatibility_warnings": warnings,
            "missing_components": missing,
            "component_count": len([c for c in components.values() if c is not None]),
            "components_used": used,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hasattr_val(obj: Any, attr: str, value: Any) -> bool:
    """Check if obj.attr is set and equals value (case-insensitive string match)."""
    v = getattr(obj, attr, None)
    if v is None:
        return False
    if isinstance(v, str) and isinstance(value, str):
        return value.lower() in v.lower()
    return v == value


def _estimate_wattage(part: PartSpec, registry: PartRegistry) -> int:
    """Estimate the required PSU wattage for a part or build."""
    # Simple heuristic: if the part has a recommended_psu_w field, use it
    rec = getattr(part, "recommended_psu_w", 0)
    if rec:
        return rec
    # Otherwise use TDP * 1.5 as a rough guideline
    tdp = getattr(part, "tdp_watts", 0) or 0
    return max(int(tdp * 1.5), 450)  # minimum 450W


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

_CLI_REGISTRY: PartRegistry | None = None


def _get_cli_registry() -> PartRegistry:
    """Return the single persistent registry for CLI use."""
    global _CLI_REGISTRY
    if _CLI_REGISTRY is None:
        _CLI_REGISTRY = PartRegistry()
    return _CLI_REGISTRY


def _reset_cli_registry() -> None:
    """Reset the CLI registry (used by tests)."""
    global _CLI_REGISTRY
    _CLI_REGISTRY = None


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PC Design Agent — Parts Search Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python parts_search.py search --type cpu --socket AM5 --budget-max 800\n"
            "  python parts_search.py search --type gpu --budget-min 500 --min-vram-gb 12\n"
            "  python parts_search.py search --type motherboard --form-factor mATX --socket AM5\n"
            "  python parts_search.py search --search 'Ryzen' --budget-max 1000\n"
            "  python parts_search.py compatible --part-id 1 --compatibility motherboards\n"
            "  python parts_search.py summary --components '{...}'\n"
            "  python parts_search.py load --json parts.json\n"
            "  python parts_search.py stats\n"
        ),
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --- search ---
    sp_search = sub.add_parser("search", help="Search/filter parts")
    sp_search.add_argument("--type", choices=PART_TYPES, default=None,
                           help="Part type to search (omit for all)")
    sp_search.add_argument("--socket", help="Filter by socket (e.g. AM5, LGA1700)")
    sp_search.add_argument("--budget-max", type=float, help="Maximum price")
    sp_search.add_argument("--budget-min", type=float, help="Minimum price")
    sp_search.add_argument("--form-factor", help="Form factor (ATX, mATX, SFX, M.2 2280)")
    sp_search.add_argument("--tdp-max", type=int, help="Maximum TDP (watts)")
    sp_search.add_argument("--tdp-min", type=int, help="Minimum TDP (watts)")
    sp_search.add_argument("--memory-type", help="Memory type (DDR5, DDR4)")
    sp_search.add_argument("--brand", help="Brand filter")
    sp_search.add_argument("--chipset", help="Chipset filter (Z790, B650, RTX 4090)")
    sp_search.add_argument("--min-cores", type=int, help="Minimum CPU core count")
    sp_search.add_argument("--min-vram-gb", type=int, help="Minimum GPU VRAM (GB)")
    sp_search.add_argument("--min-speed-mhz", type=int, help="Minimum RAM speed (MHz)")
    sp_search.add_argument("--min-capacity-gb", type=int, help="Minimum capacity (GB)")
    sp_search.add_argument("--min-wattage", type=int, help="Minimum PSU wattage")
    sp_search.add_argument("--efficiency-rating", help="PSU efficiency (80+ Gold, etc.)")
    sp_search.add_argument("--modular-type", help="PSU modular type (Full, Semi)")
    sp_search.add_argument("--cooler-type", help="Cooler type (Air, AIO)")
    sp_search.add_argument("--storage-type", help="Storage type (NVMe SSD, SATA SSD)")
    sp_search.add_argument("--case-type", help="Case type (Mid Tower, SFF)")
    sp_search.add_argument("--has-igpu", action="store_true", help="CPU must have iGPU")
    sp_search.add_argument("--wifi-builtin", action="store_true",
                           help="Motherboard must have built-in WiFi")
    sp_search.add_argument("--rgb", action="store_true", help="RGB support")
    sp_search.add_argument("--pcie-version", help="PCIe version (PCIe 5.0)")
    sp_search.add_argument("--max-length-mm", type=float, help="Maximum component length (mm)")
    sp_search.add_argument("--min-read-speed-mbs", type=int, help="Min storage read speed (MB/s)")
    sp_search.add_argument("--search", help="Full-text search across name/brand/model")
    sp_search.add_argument("--json", action="store_true",
                           help="Output as JSON (default: table)")

    # --- compatible ---
    sp_comp = sub.add_parser("compatible", help="Find compatible parts")
    sp_comp.add_argument("--part-id", type=int, required=True,
                         help="Part ID in the registry")
    sp_comp.add_argument("--compatibility", required=True,
                         choices=["motherboards", "cpus", "coolers", "cases", "rams", "psus"],
                         help="Type of compatibility to check")
    sp_comp.add_argument("--json", action="store_true", help="Output as JSON")

    # --- summary ---
    sp_sum = sub.add_parser("summary", help="Analyze a build's compatibility")
    sp_sum.add_argument("--components", required=True,
                        help="JSON dict of {cpu: {name:..., socket:...}, ...}")
    sp_sum.add_argument("--json", action="store_true", help="Output as JSON")

    # --- load ---
    sp_load = sub.add_parser("load", help="Load parts from a JSON file")
    sp_load.add_argument("--json", type=str, required=True, help="Path to JSON file")

    # --- stats ---
    sp_stats = sub.add_parser("stats", help="Show registry statistics")

    return parser.parse_args(argv)


def _print_table(results: list[dict[str, Any]]) -> None:
    """Pretty-print a list of part dicts as a table."""
    if not results:
        print("No results found.")
        return

    # Determine columns: common keys first, then type-specific
    base_keys = ["name", "brand", "current_price"]
    type_specific = {}
    for r in results:
        pt = r.get("part_type", "")
        if pt not in type_specific:
            type_specific[pt] = []
        for k in r:
            if k not in base_keys and k not in ("part_type", "_id", "_tags",
                                                "created_at", "updated_at"):
                if k not in type_specific[pt]:
                    type_specific[pt].append(k)

    # Show a unified table with a part_type column
    headers = ["#", "type"] + base_keys + ["key_spec"]
    rows = []
    for i, r in enumerate(results, 1):
        pt = r.get("part_type", "")
        specifics = []
        for key in type_specific.get(pt, [])[:3]:  # Show top 3 type-specific fields
            val = r.get(key, "")
            if val not in (None, "", 0, 0.0, False):
                specifics.append(f"{key}={val}")
        rows.append((
            str(i),
            pt,
            r.get("name", ""),
            r.get("brand", "") or "",
            f"${r.get('current_price', 0):.2f}" if r.get("current_price") else "-",
            ", ".join(specifics),
        ))

    # Compute column widths
    widths = [max(len(str(row[j])) for row in rows + [headers]) for j in range(6)]

    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    header_line = "| " + " | ".join(
        h.ljust(w) for h, w in zip(headers, widths)
    ) + " |"

    print(sep)
    print(header_line)
    print(sep)
    for row in rows:
        print("| " + " | ".join(
            str(row[j]).ljust(widths[j]) for j in range(6)
        ) + " |")
    print(sep)
    print(f"\nTotal: {len(results)} part(s)")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])

    registry = _get_cli_registry()

    if args.command == "load":
        count = registry.load_json(args.json)
        print(f"Loaded {count} parts from {args.json}")
        return 0

    elif args.command == "stats":
        print(f"Registry has {registry.count()} parts total.")
        for pt, cnt in registry.count_by_type().items():
            print(f"  {pt}: {cnt}")
        return 0

    elif args.command == "search":
        filters: dict[str, Any] = {}
        for attr in ("socket", "form_factor", "memory_type", "brand", "chipset",
                     "efficiency_rating", "modular_type", "cooler_type",
                     "storage_type", "case_type", "pcie_version", "search"):
            val = getattr(args, attr, None)
            if val is not None:
                filters[attr] = val
        for attr_num in ("budget_max", "budget_min", "tdp_max", "tdp_min",
                         "min_cores", "min_vram_gb", "min_speed_mhz",
                         "min_capacity_gb", "min_wattage", "max_length_mm",
                         "min_read_speed_mbs"):
            val = getattr(args, attr_num, None)
            if val is not None:
                filters[attr_num] = val
        for flag in ("has_igpu", "wifi_builtin", "rgb"):
            if getattr(args, flag, False):
                filters[flag] = True

        results = registry.search_parts(part_type=args.type, filters=filters)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            _print_table(results)
        return 0

    elif args.command == "compatible":
        part = registry.get_part(args.part_id)
        if part is None:
            print(f"Error: No part with ID {args.part_id} in registry. "
                  f"Load data first with 'load'.", file=sys.stderr)
            return 1
        results = registry.get_compatible_parts(part, args.compatibility)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            _print_table(results)
        return 0

    elif args.command == "summary":
        try:
            comps_raw = json.loads(args.components)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --components: {e}", file=sys.stderr)
            return 1

        components: dict[str, Optional[PartSpec]] = {}
        for role, data in comps_raw.items():
            if data is None:
                components[role] = None
            elif isinstance(data, dict):
                pt = role if role in PART_TYPES else "cpu"  # guess
                if "part_type" in data:
                    pt = data["part_type"]
                components[role] = registry.load_dict(pt, data)
            else:
                components[role] = None

        summary = registry.get_build_summary(components)
        if args.json:
            print(json.dumps(summary, indent=2, default=str))
        else:
            print("=== Build Summary ===")
            print(f"  Total TDP:       {summary['total_tdp']}W")
            print(f"  Total Price:     ${summary['total_price']:.2f}")
            print(f"  Components:      {summary['component_count']}/8")

            if summary["missing_components"]:
                print(f"\n  Missing components: {', '.join(summary['missing_components'])}")

            if summary["compatibility_warnings"]:
                print(f"\n  Compatibility warnings ({len(summary['compatibility_warnings'])}):")
                for w in summary["compatibility_warnings"]:
                    print(f"    ⚠  {w}")
            else:
                print("\n  No compatibility warnings detected.")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())