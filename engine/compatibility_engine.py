"""
PC Design Agent — Compatibility Validation Engine
==================================================
In-memory component compatibility checker.

Validates a set of PC components across all major interfaces:
CPU ↔ Motherboard, CPU ↔ Cooler, GPU ↔ Motherboard, RAM ↔ Motherboard,
Storage ↔ Motherboard, PSU ↔ Components, Case ↔ (Motherboard, GPU, Cooler, PSU).

Data model mirrors the SQL schema in component-schema.sql but uses
in-memory dataclasses for fast, dependency-free validation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple


# ── ValidationResult ──────────────────────────────────────────────────────────


@dataclass
class ValidationResult:
    """Outcome of a full-build compatibility validation."""

    valid: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    score: float = 1.0  # 0.0 (entirely invalid) to 1.0 (perfect)

    def pretty_print(self) -> str:
        """Return a human-readable string of this result."""
        lines = []
        status = "✅ COMPATIBLE" if self.valid else "❌ INCOMPATIBLE"
        lines.append(f"[{status}]  Score: {self.score:.1%}")
        if self.issues:
            lines.append(f"\n  Issues ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                lines.append(f"    {i}. {issue}")
        if self.warnings:
            lines.append(f"\n  Warnings ({len(self.warnings)}):")
            for i, warn in enumerate(self.warnings, 1):
                lines.append(f"    {i}. {warn}")
        return "\n".join(lines)


def _merge_results(results: Sequence[ValidationResult]) -> ValidationResult:
    """Merge multiple validation results into a single composite result."""
    all_issues: List[str] = []
    all_warnings: List[str] = []
    valid = True
    for r in results:
        if not r.valid:
            valid = False
        all_issues.extend(r.issues)
        all_warnings.extend(r.warnings)

    if not results:
        return ValidationResult(valid=True, score=1.0)

    # Score = product of individual scores — one zero kills it
    score = 1.0
    for r in results:
        score *= r.score
    # If we have critical issues, floor the score
    if all_issues:
        penalty_per_issue = 0.15
        score = max(0.0, score - penalty_per_issue * len(all_issues))
    if not all_issues and not all_warnings:
        score = 1.0

    return ValidationResult(
        valid=valid,
        issues=all_issues,
        warnings=all_warnings,
        score=round(max(0.0, min(1.0, score)), 4),
    )


# ── PartSpec Dataclasses ──────────────────────────────────────────────────────


@dataclass
class PartSpec:
    """Base component — every part has a name and brand."""
    name: str
    brand: Optional[str] = None


@dataclass
class CpuSpec(PartSpec):
    socket: str = ""
    tdp_watts: int = 0
    max_tdp_watts: Optional[int] = None
    pcie_version: Optional[str] = None
    has_igpu: bool = False


@dataclass
class GpuSpec(PartSpec):
    tdp_watts: int = 0
    pcie_gen: Optional[str] = None       # e.g. "PCIe 4.0 x16"
    length_mm: float = 0.0
    width_mm: float = 0.0
    slot_width: int = 2
    recommended_psu_w: Optional[int] = None


@dataclass
class MotherboardSpec(PartSpec):
    socket: str = ""
    form_factor: str = ""                # ATX, mATX, Mini-ITX, E-ATX
    chipset: Optional[str] = None
    ram_type: Optional[str] = None       # DDR5, DDR4
    max_ram_speed_mhz: int = 0
    ram_slots: int = 4
    pcie_version: Optional[str] = None   # PCIe 5.0
    m2_slots: int = 0
    sata_ports: int = 0


@dataclass
class RamSpec(PartSpec):
    ram_type: str = ""                   # DDR5, DDR4
    speed_mhz: int = 0
    sticks: int = 1
    capacity_gb: int = 0


@dataclass
class StorageSpec(PartSpec):
    storage_type: str = ""               # NVMe SSD, SATA SSD, HDD
    interface: str = ""                  # PCIe 4.0 x4, SATA III
    form_factor: str = ""                # M.2 2280, 2.5", 3.5"
    capacity_gb: int = 0


@dataclass
class PsuSpec(PartSpec):
    wattage: int = 0
    form_factor: str = ""                # ATX, SFX, SFX-L
    efficiency_rating: Optional[str] = None
    modular_type: Optional[str] = None


@dataclass
class CaseSpec(PartSpec):
    case_type: Optional[str] = None
    motherboard_support: List[str] = field(default_factory=lambda: ["ATX"])
    psu_form_factor: str = "ATX"
    max_psu_length_mm: float = 0.0
    max_gpu_length_mm: float = 0.0
    max_gpu_width_mm: float = 0.0
    max_cpu_cooler_height_mm: float = 0.0


@dataclass
class CoolerSpec(PartSpec):
    cooler_type: str = "Air"
    height_mm: float = 0.0
    max_tdp_watts: int = 0
    socket_compatibility: List[str] = field(default_factory=list)
    radiator_size_mm: Optional[int] = None


# ── BuildSpec ─────────────────────────────────────────────────────────────────


@dataclass
class BuildSpec:
    """Aggregate of all components in a build."""
    cpu: Optional[CpuSpec] = None
    gpu: Optional[GpuSpec] = None
    motherboard: Optional[MotherboardSpec] = None
    ram_sticks: List[RamSpec] = field(default_factory=list)
    storage_drives: List[StorageSpec] = field(default_factory=list)
    psu: Optional[PsuSpec] = None
    case: Optional[CaseSpec] = None
    cooler: Optional[CoolerSpec] = None

    def part_count(self) -> int:
        count = 0
        for attr in ("cpu", "gpu", "motherboard", "psu", "case", "cooler"):
            if getattr(self, attr) is not None:
                count += 1
        count += len(self.ram_sticks)
        count += len(self.storage_drives)
        return count


# ── Compatibility Validation Engine ────────────────────────────────────────────


class CompatibilityEngine:
    """Validates PC build compatibility between components.

    All validation methods return a ValidationResult. Use ``validate_build()``
    to run the full suite against a ``BuildSpec``.
    """

    # ═══════════════════════════════════════════════════════════════════════════
    # Full-build entry point
    # ═══════════════════════════════════════════════════════════════════════════

    def validate_build(self, build: BuildSpec) -> ValidationResult:
        """Run every applicable validation rule against the build."""
        checks: List[ValidationResult] = []

        checks.append(self.validate_cpu_motherboard(build.cpu, build.motherboard))
        checks.append(self.validate_cpu_cooler(build.cpu, build.cooler))
        checks.append(self.validate_gpu_motherboard(build.gpu, build.motherboard))
        checks.append(self.validate_ram_motherboard(build.ram_sticks, build.motherboard))
        checks.append(self.validate_storage_motherboard(build.storage_drives, build.motherboard))
        checks.append(self.validate_psu_power(build.psu, build.cpu, build.gpu))
        checks.append(self.validate_case_motherboard(build.case, build.motherboard))
        checks.append(self.validate_case_gpu(build.case, build.gpu))
        checks.append(self.validate_case_cooler(build.case, build.cooler))
        checks.append(self.validate_case_psu(build.case, build.psu))

        # Filter out "not applicable" results (both components missing → valid with no issues)
        applicable = [r for r in checks if not (r.valid and not r.issues and not r.warnings) or r.score < 1.0]
        return _merge_results(applicable)

    # ═══════════════════════════════════════════════════════════════════════════
    # Individual validators
    # ═══════════════════════════════════════════════════════════════════════════

    # ── CPU ↔ Motherboard ───────────────────────────────────────────────────

    @staticmethod
    def validate_cpu_motherboard(
        cpu: Optional[CpuSpec], mobo: Optional[MotherboardSpec]
    ) -> ValidationResult:
        issues: List[str] = []
        warnings: List[str] = []

        if cpu is None or mobo is None:
            # Not comparable — skip silently
            return ValidationResult(valid=True, score=1.0)

        # Socket check
        if cpu.socket and mobo.socket:
            if _normalise_socket(cpu.socket) != _normalise_socket(mobo.socket):
                issues.append(
                    f"Socket mismatch: CPU '{cpu.name}' requires socket {cpu.socket}, "
                    f"but motherboard '{mobo.name}' has socket {mobo.socket}."
                )

        # PCIe version (informational)
        if cpu.pcie_version and mobo.pcie_version:
            c_gen = _pcie_gen(cpu.pcie_version)
            m_gen = _pcie_gen(mobo.pcie_version)
            if c_gen and m_gen and m_gen < c_gen:
                warnings.append(
                    f"Motherboard PCIe version ({mobo.pcie_version}) is lower than "
                    f"CPU's supported version ({cpu.pcie_version}). GPU bandwidth may be limited."
                )

        score = _score_from_issues(issues, warnings)
        return ValidationResult(
            valid=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            score=score,
        )

    # ── CPU ↔ Cooler ────────────────────────────────────────────────────────

    @staticmethod
    def validate_cpu_cooler(
        cpu: Optional[CpuSpec], cooler: Optional[CoolerSpec]
    ) -> ValidationResult:
        issues: List[str] = []
        warnings: List[str] = []

        if cpu is None or cooler is None:
            return ValidationResult(valid=True, score=1.0)

        # Socket compatibility
        if cooler.socket_compatibility and cpu.socket:
            cpu_sock_norm = _normalise_socket(cpu.socket)
            compatible_sockets = [_normalise_socket(s) for s in cooler.socket_compatibility]
            if cpu_sock_norm not in compatible_sockets:
                issues.append(
                    f"Socket mismatch: CPU '{cpu.name}' ({cpu.socket}) is NOT in the "
                    f"cooler '{cooler.name}' compatible socket list: {cooler.socket_compatibility}."
                )

        # TDP rating
        cpu_tdp = cpu.max_tdp_watts or cpu.tdp_watts
        if cpu_tdp > 0 and cooler.max_tdp_watts > 0 and cpu_tdp > cooler.max_tdp_watts:
            issues.append(
                f"TDP insufficient: CPU '{cpu.name}' TDP ({cpu_tdp}W) exceeds "
                f"cooler '{cooler.name}' max TDP ({cooler.max_tdp_watts}W)."
            )
        elif cpu_tdp > 0 and cooler.max_tdp_watts > 0:
            proximity = cpu_tdp / cooler.max_tdp_watts
            if proximity >= 0.85:
                warnings.append(
                    f"Cooler '{cooler.name}' max TDP ({cooler.max_tdp_watts}W) is "
                    f"close to CPU TDP ({cpu_tdp}W). Ensure adequate case airflow."
                )

        score = _score_from_issues(issues, warnings)
        return ValidationResult(
            valid=len(issues) == 0, issues=issues, warnings=warnings, score=score
        )

    # ── GPU ↔ Motherboard ───────────────────────────────────────────────────

    @staticmethod
    def validate_gpu_motherboard(
        gpu: Optional[GpuSpec], mobo: Optional[MotherboardSpec]
    ) -> ValidationResult:
        issues: List[str] = []
        warnings: List[str] = []

        if gpu is None or mobo is None:
            return ValidationResult(valid=True, score=1.0)

        # PCIe generation — GPU and motherboard both advertise a gen
        if gpu.pcie_gen and mobo.pcie_version:
            gpu_gen = _pcie_gen(gpu.pcie_gen)
            mobo_gen = _pcie_gen(mobo.pcie_version)
            if gpu_gen and mobo_gen and mobo_gen < gpu_gen:
                warnings.append(
                    f"Motherboard PCIe version ({mobo.pcie_version}) is lower than "
                    f"GPU's interface ({gpu.pcie_gen}). GPU may run at reduced bandwidth."
                )

        score = _score_from_issues(issues, warnings)
        return ValidationResult(
            valid=len(issues) == 0, issues=issues, warnings=warnings, score=score
        )

    # ── RAM ↔ Motherboard ───────────────────────────────────────────────────

    @staticmethod
    def validate_ram_motherboard(
        ram_sticks: List[RamSpec], mobo: Optional[MotherboardSpec]
    ) -> ValidationResult:
        issues: List[str] = []
        warnings: List[str] = []

        if not ram_sticks or mobo is None:
            return ValidationResult(valid=True, score=1.0)

        # DDR type
        for stick in ram_sticks:
            if stick.ram_type and mobo.ram_type and stick.ram_type != mobo.ram_type:
                issues.append(
                    f"RAM type mismatch: '{stick.name}' is {stick.ram_type} "
                    f"but motherboard '{mobo.name}' supports {mobo.ram_type}."
                )

        # Speed check
        for stick in ram_sticks:
            if stick.speed_mhz > 0 and mobo.max_ram_speed_mhz > 0:
                if stick.speed_mhz > mobo.max_ram_speed_mhz:
                    warnings.append(
                        f"RAM '{stick.name}' rated at {stick.speed_mhz} MHz, which exceeds "
                        f"motherboard '{mobo.name}' max supported speed ({mobo.max_ram_speed_mhz} MHz). "
                        "It will downclock to the motherboard limit."
                    )

        # Slot count
        if mobo.ram_slots > 0 and len(ram_sticks) > mobo.ram_slots:
            issues.append(
                f"Physical slot count: {len(ram_sticks)} RAM stick(s) but motherboard "
                f"'{mobo.name}' has only {mobo.ram_slots} DIMM slot(s)."
            )

        # Mixed RAM warning (different specs)
        types = {s.ram_type for s in ram_sticks if s.ram_type}
        if len(types) > 1:
            warnings.append(
                f"Mixed RAM types detected: {types}. This may cause instability."
            )

        score = _score_from_issues(issues, warnings)
        return ValidationResult(
            valid=len(issues) == 0, issues=issues, warnings=warnings, score=score
        )

    # ── Storage ↔ Motherboard ───────────────────────────────────────────────

    @staticmethod
    def validate_storage_motherboard(
        drives: List[StorageSpec], mobo: Optional[MotherboardSpec]
    ) -> ValidationResult:
        issues: List[str] = []
        warnings: List[str] = []

        if not drives or mobo is None:
            return ValidationResult(valid=True, score=1.0)

        # Track available slots
        used_m2 = 0
        used_sata = 0

        for drive in drives:
            interface_lower = (drive.interface or "").lower()

            # NVMe / PCIe drives need M.2 slots
            if "nvme" in interface_lower or "pcie" in interface_lower or drive.storage_type == "NVMe SSD":
                used_m2 += 1
                if used_m2 > (mobo.m2_slots or 0):
                    issues.append(
                        f"M.2 slot shortage: '{drive.name}' requires an M.2 slot, "
                        f"but motherboard '{mobo.name}' has only {mobo.m2_slots} slot(s) "
                        f"and {used_m2} NVMe drive(s) are configured."
                    )

            # SATA drives
            elif "sata" in interface_lower or drive.storage_type in ("SATA SSD", "HDD"):
                used_sata += 1
                if used_sata > (mobo.sata_ports or 0):
                    issues.append(
                        f"SATA port shortage: '{drive.name}' requires a SATA port, "
                        f"but motherboard '{mobo.name}' has only {mobo.sata_ports} port(s) "
                        f"and {used_sata} SATA drive(s) are configured."
                    )
            else:
                warnings.append(
                    f"Unknown interface '{drive.interface}' on '{drive.name}' — "
                    "cannot verify motherboard compatibility."
                )

        score = _score_from_issues(issues, warnings)
        return ValidationResult(
            valid=len(issues) == 0, issues=issues, warnings=warnings, score=score
        )

    # ── PSU ↔ Components (total wattage) ────────────────────────────────────

    @staticmethod
    def validate_psu_power(
        psu: Optional[PsuSpec],
        cpu: Optional[CpuSpec] = None,
        gpu: Optional[GpuSpec] = None,
    ) -> ValidationResult:
        issues: List[str] = []
        warnings: List[str] = []

        if psu is None:
            return ValidationResult(valid=True, score=1.0)

        total_tdp = 0
        tdp_sources: List[str] = []

        if cpu is not None:
            cpu_tdp = cpu.max_tdp_watts or cpu.tdp_watts
            total_tdp += cpu_tdp
            tdp_sources.append(f"CPU '{cpu.name}': {cpu_tdp}W")

        if gpu is not None:
            gpu_tdp = gpu.tdp_watts
            total_tdp += gpu_tdp
            tdp_sources.append(f"GPU '{gpu.name}': {gpu_tdp}W")

        if total_tdp == 0:
            return ValidationResult(valid=True, score=1.0)

        required_wattage = math.ceil(total_tdp * 1.2)  # 20% headroom

        if psu.wattage > 0 and psu.wattage < required_wattage:
            issues.append(
                f"PSU wattage insufficient: PSU '{psu.name}' provides {psu.wattage}W "
                f"but the build (CPU + GPU) needs at least {required_wattage}W "
                f"({total_tdp}W base + 20% headroom). "
                f"Load: {' + '.join(tdp_sources)}."
            )
        elif psu.wattage > 0 and psu.wattage < total_tdp:
            issues.append(
                f"PSU cannot even cover base load: {psu.wattage}W < {total_tdp}W sum of TDPs."
            )
        elif psu.wattage > 0:
            load_pct = total_tdp / psu.wattage * 100
            if load_pct > 85:
                warnings.append(
                    f"PSU load is high: {total_tdp}W / {psu.wattage}W = {load_pct:.0f}%. "
                    "Consider a higher-wattage PSU for better efficiency and headroom."
                )
            elif load_pct < 30 and psu.wattage >= 500:
                warnings.append(
                    f"PSU load is very low: {total_tdp}W / {psu.wattage}W = {load_pct:.0f}%. "
                    "The PSU may run inefficiently at very low load."
                )

        score = _score_from_issues(issues, warnings)
        return ValidationResult(
            valid=len(issues) == 0, issues=issues, warnings=warnings, score=score
        )

    # ── Case ↔ Motherboard (form factor) ────────────────────────────────────

    @staticmethod
    def validate_case_motherboard(
        case: Optional[CaseSpec], mobo: Optional[MotherboardSpec]
    ) -> ValidationResult:
        issues: List[str] = []
        warnings: List[str] = []

        if case is None or mobo is None:
            return ValidationResult(valid=True, score=1.0)

        if mobo.form_factor and case.motherboard_support:
            mobo_ff = mobo.form_factor.strip().lower()
            supported = [s.strip().lower() for s in case.motherboard_support]
            if mobo_ff not in supported:
                issues.append(
                    f"Form factor mismatch: motherboard '{mobo.name}' ({mobo.form_factor}) "
                    f"does not fit in case '{case.name}' which supports: "
                    f"{', '.join(case.motherboard_support)}."
                )

        score = _score_from_issues(issues, warnings)
        return ValidationResult(
            valid=len(issues) == 0, issues=issues, warnings=warnings, score=score
        )

    # ── Case ↔ GPU (clearance) ──────────────────────────────────────────────

    @staticmethod
    def validate_case_gpu(
        case: Optional[CaseSpec], gpu: Optional[GpuSpec]
    ) -> ValidationResult:
        issues: List[str] = []
        warnings: List[str] = []

        if case is None or gpu is None:
            return ValidationResult(valid=True, score=1.0)

        if gpu.length_mm > 0 and case.max_gpu_length_mm > 0:
            if gpu.length_mm > case.max_gpu_length_mm:
                issues.append(
                    f"GPU length: '{gpu.name}' is {gpu.length_mm}mm but case "
                    f"'{case.name}' max GPU length is {case.max_gpu_length_mm}mm."
                )
            elif gpu.length_mm > case.max_gpu_length_mm * 0.9:
                warnings.append(
                    f"GPU length ({gpu.length_mm}mm) is within "
                    f"{case.max_gpu_length_mm - gpu.length_mm}mm of case limit "
                    f"({case.max_gpu_length_mm}mm). Check front fan / radiator clearance."
                )

        if gpu.width_mm > 0 and case.max_gpu_width_mm > 0:
            if gpu.width_mm > case.max_gpu_width_mm:
                issues.append(
                    f"GPU width: '{gpu.name}' is {gpu.width_mm}mm but case "
                    f"'{case.name}' max GPU width is {case.max_gpu_width_mm}mm."
                )

        score = _score_from_issues(issues, warnings)
        return ValidationResult(
            valid=len(issues) == 0, issues=issues, warnings=warnings, score=score
        )

    # ── Case ↔ Cooler (height clearance) ────────────────────────────────────

    @staticmethod
    def validate_case_cooler(
        case: Optional[CaseSpec], cooler: Optional[CoolerSpec]
    ) -> ValidationResult:
        issues: List[str] = []
        warnings: List[str] = []

        if case is None or cooler is None:
            return ValidationResult(valid=True, score=1.0)

        if cooler.height_mm > 0 and case.max_cpu_cooler_height_mm > 0:
            if cooler.height_mm > case.max_cpu_cooler_height_mm:
                issues.append(
                    f"Cooler height: '{cooler.name}' is {cooler.height_mm}mm but case "
                    f"'{case.name}' max cooler height is {case.max_cpu_cooler_height_mm}mm."
                )
            elif cooler.height_mm > case.max_cpu_cooler_height_mm * 0.9:
                warnings.append(
                    f"Cooler height ({cooler.height_mm}mm) is within "
                    f"{case.max_cpu_cooler_height_mm - cooler.height_mm}mm of case limit "
                    f"({case.max_cpu_cooler_height_mm}mm). Double-check side panel clearance."
                )

        score = _score_from_issues(issues, warnings)
        return ValidationResult(
            valid=len(issues) == 0, issues=issues, warnings=warnings, score=score
        )

    # ── Case ↔ PSU (form factor) ────────────────────────────────────────────

    @staticmethod
    def validate_case_psu(
        case: Optional[CaseSpec], psu: Optional[PsuSpec]
    ) -> ValidationResult:
        issues: List[str] = []
        warnings: List[str] = []

        if case is None or psu is None:
            return ValidationResult(valid=True, score=1.0)

        if psu.form_factor and case.psu_form_factor:
            psu_ff = psu.form_factor.strip().lower()
            case_psu_ff = case.psu_form_factor.strip().lower()
            if psu_ff != case_psu_ff:
                issues.append(
                    f"PSU form factor mismatch: '{psu.name}' is {psu.form_factor} "
                    f"but case '{case.name}' expects {case.psu_form_factor} PSUs."
                )

        score = _score_from_issues(issues, warnings)
        return ValidationResult(
            valid=len(issues) == 0, issues=issues, warnings=warnings, score=score
        )


# ── Helpers ────────────────────────────────────────────────────────────────────


def _normalise_socket(socket: str) -> str:
    """Normalise socket string for comparison (case-insensitive, stripped)."""
    return socket.strip().upper().replace(" ", "").replace("-", "").replace("_", "")


def _pcie_gen(pcie_str: str) -> Optional[int]:
    """Extract PCIe generation number from a string like 'PCIe 5.0 x16'."""
    import re
    m = re.search(r'(\d+)\.\d', pcie_str)
    if m:
        return int(m.group(1))
    m = re.search(r'gen\s*(\d+)', pcie_str, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def _score_from_issues(issues: List[str], warnings: List[str]) -> float:
    """Compute a 0-1 compatibility score."""
    if issues:
        penalty = min(1.0, 0.15 * len(issues))
        return round(max(0.0, 1.0 - penalty), 4)
    if warnings:
        penalty = min(0.3, 0.05 * len(warnings))
        return round(1.0 - penalty, 4)
    return 1.0


# ── Convenience entry point ────────────────────────────────────────────────────


def validate(build: BuildSpec) -> ValidationResult:
    """Shorthand: create an engine and validate a build."""
    return CompatibilityEngine().validate_build(build)