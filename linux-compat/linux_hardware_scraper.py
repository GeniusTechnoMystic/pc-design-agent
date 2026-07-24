#!/usr/bin/env python3
"""
linux-hardware.org Scraper
==========================
Collect device compatibility data from linux-hardware.org for PC design decisions.

Target categories:
  - GPUs (NVIDIA & AMD): driver, kernel versions, status
  - Wi-Fi chips: driver support
  - Network controllers: driver support
  - Audio codecs: driver support

Output: JSONL format (one JSON object per device).
"""

import argparse
import csv
import io
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

import requests
from bs4 import BeautifulSoup, Tag

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = "https://linux-hardware.org"
DEFAULT_OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DELAY = 1.5  # seconds between requests
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("lhw-scraper")

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class KernelDriver:
    """A single kernel driver entry from the LKDDb table."""
    kernel_range: str = ""
    source: str = ""
    config: str = ""
    by_id: str = ""
    by_class: str = ""


@dataclass
class OtherDriver:
    """Third-party / proprietary driver entry."""
    name: str = ""
    version_range: str = ""


@dataclass
class ProbeStatus:
    """A single probe status row for a computer using this device."""
    hwid: str = ""
    computer_type: str = ""
    vendor: str = ""
    model: str = ""
    probes: int = 0
    system: str = ""
    status: str = ""      # "works", "detected", "failed"
    comment: str = ""


@dataclass
class DeviceInfo:
    """Complete device information from the detail page."""
    device_id: str = ""
    bus: str = ""         # pci, usb, etc.
    vendor_id: str = ""
    device_code: str = ""
    subvendor_id: str = ""
    subdevice_code: str = ""
    class_id: str = ""
    device_type: str = ""
    vendor_name: str = ""
    device_name: str = ""
    subsystem_name: str = ""
    category: str = ""    # gpu-nvidia, gpu-amd, wifi, network, audio
    kernel_drivers: list[KernelDriver] = field(default_factory=list)
    other_drivers: list[OtherDriver] = field(default_factory=list)
    probes_total: int = 0
    status_summary: dict = field(default_factory=dict)  # {"works": N, "detected": N, "failed": N}
    sample_probes: list[ProbeStatus] = field(default_factory=list)
    source_url: str = ""


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT})


def fetch_html(url: str, dry_run: bool = False, delay: float = DEFAULT_DELAY) -> Optional[str]:
    """Fetch HTML from a URL with rate limiting."""
    if dry_run:
        log.info("[DRY-RUN] Would fetch: %s", url)
        return None

    log.debug("Fetching: %s", url)
    try:
        resp = _session.get(url, timeout=30)
        resp.raise_for_status()
        # Respect rate limiting
        time.sleep(delay)
        return resp.text
    except requests.RequestException as e:
        log.warning("Failed to fetch %s: %s", url, e)
        return None


def make_absolute(href: str) -> str:
    """Convert a relative href to absolute URL."""
    return urljoin(BASE_URL, href)


# ---------------------------------------------------------------------------
# Search page parser
# ---------------------------------------------------------------------------

def parse_search_pagination(html: str) -> int:
    """Extract the last page number from a search results page."""
    soup = BeautifulSoup(html, 'html.parser')
    # Find the pagination links
    pagination = soup.find_all('a', href=re.compile(r'page=(\d+)'))
    max_page = 1
    for a in pagination:
        m = re.search(r'page=(\d+)', a.get('href', ''))
        if m:
            p = int(m.group(1))
            if p > max_page:
                max_page = p
    return max_page


def parse_search_results(html: str) -> list[dict]:
    """
    Parse search results table rows into device references.

    Returns list of dicts: {vendor, bus, device_type, device_name, url, device_id}
    """
    soup = BeautifulSoup(html, 'html.parser')
    devices = []

    # The results table alternates: some tables in the page, find the one with rows
    # that have Vendor | Bus | Type | Name columns
    # Look for tables that appear after the search form
    tables = soup.find_all('table')

    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 3:
                continue

            # Check if this looks like a data row (has a link to ?id=)
            link = row.find('a', href=re.compile(r'\?id='))
            if not link:
                continue

            href = link.get('href', '')
            device_id = href.split('?id=')[-1] if '?id=' in href else ''

            # Parse cells
            cells_text = [c.get_text(strip=True) for c in cells]

            vendor = cells_text[0] if len(cells_text) > 0 else ''
            bus = cells_text[1] if len(cells_text) > 1 else ''
            dev_type = cells_text[2] if len(cells_text) > 2 else ''
            name = link.get_text(strip=True)

            devices.append({
                'vendor': vendor,
                'bus': bus,
                'device_type': dev_type,
                'device_name': name,
                'url': make_absolute(href),
                'device_id': device_id,
            })

    return devices


# ---------------------------------------------------------------------------
# Device detail page parser
# ---------------------------------------------------------------------------

def _extract_metadata(soup: BeautifulSoup) -> dict:
    """Extract device metadata from the info table rows."""
    meta = {
        'device_id': '',
        'bus': '',
        'vendor_id': '',
        'device_code': '',
        'subvendor_id': '',
        'subdevice_code': '',
        'class_id': '',
        'device_type': '',
        'vendor_name': '',
        'device_name': '',
        'subsystem_name': '',
    }

    # Main info table - first table with class "properties"
    # Structure:
    #   <tr><th>ID</th><td>PCI a727:0013:10b7:1026</td></tr>
    #   <tr><th>Class</th><td>02-80 <a href="...">»</a></td></tr>
    #   ...
    info_table = soup.find('table', class_=re.compile(r'properties|tbl'))
    if not info_table:
        # fallback: just find any table that has <th> elements
        for table in soup.find_all('table'):
            if table.find('th'):
                info_table = table
                break
    if not info_table:
        return meta

    for row in info_table.find_all('tr'):
        th = row.find('th')
        td = row.find('td')
        if not th or not td:
            continue

        label = th.get_text(strip=True)
        value_text = td.get_text(strip=True)

        # Strip trailing » icon from value
        value_text = value_text.rstrip('\u00bb').strip()

        if label == 'ID':
            parts = value_text.split()
            if len(parts) >= 2:
                meta['bus'] = parts[0].lower()
                id_parts = parts[1].split(':')
                if len(id_parts) >= 2:
                    meta['vendor_id'] = id_parts[0]
                    meta['device_code'] = id_parts[1]
                if len(id_parts) >= 4:
                    meta['subvendor_id'] = id_parts[2]
                    meta['subdevice_code'] = id_parts[3]
                meta['device_id'] = parts[1]
        elif label == 'Class':
            meta['class_id'] = value_text.split()[0] if value_text else ''
        elif label == 'Type':
            # value_text is like "net/wireless" after stripping »
            meta['device_type'] = value_text
        elif label == 'Vendor':
            # value_text is like "3Com" after stripping »
            meta['vendor_name'] = value_text
        elif label == 'Name':
            meta['device_name'] = value_text
        elif label == 'Subsystem':
            meta['subsystem_name'] = value_text

    # Also try to get device name from the page title
    title_tag = soup.find('title')
    if title_tag:
        t = title_tag.get_text(strip=True)
        if t and not meta['device_name']:
            meta['device_name'] = t

    return meta


def _extract_kernel_drivers(soup: BeautifulSoup) -> list[KernelDriver]:
    """Extract the kernel drivers (LKDDb) table."""
    drivers = []

    # Find the "Kernel Drivers" section - look for heading
    # The table typically appears after "Kernel Drivers" header
    kernel_header = soup.find(lambda tag: tag.name in ('h2', 'h3', 'strong')
                              and 'Kernel Driver' in tag.get_text())
    if not kernel_header:
        return drivers

    # Find the table that follows
    table = kernel_header.find_next('table')
    if not table:
        return drivers

    rows = table.find_all('tr')
    for row in rows[1:]:  # skip header
        cells = row.find_all('td')
        if len(cells) < 5:
            continue

        drv = KernelDriver(
            kernel_range=cells[0].get_text(strip=True),
            source=cells[1].get_text(strip=True),
            config=cells[2].get_text(strip=True),
            by_id=cells[3].get_text(strip=True),
            by_class=cells[4].get_text(strip=True),
        )
        drivers.append(drv)

    return drivers


def _extract_other_drivers(soup: BeautifulSoup) -> list[OtherDriver]:
    """Extract non-kernel (third-party) drivers."""
    drivers = []

    # Find "Other Drivers" section
    other_header = soup.find(lambda tag: tag.name in ('h2', 'h3', 'strong')
                             and 'Other Driver' in tag.get_text())
    if not other_header:
        return drivers

    # Parse the list following the header
    ul = other_header.find_next('ul')
    if ul:
        for li in ul.find_all('li'):
            text = li.get_text(strip=True)
            # Format: "nvidia (530.41.03 and newer)" or just "nvidia"
            m = re.match(r'^(\S+)\s*\((.+)\)\s*$', text)
            if m:
                drivers.append(OtherDriver(name=m.group(1), version_range=m.group(2)))
            else:
                drivers.append(OtherDriver(name=text))

    return drivers


def _extract_status_summary(soup: BeautifulSoup) -> dict:
    """Extract the device status summary.

    Returns dict with probe count and status breakdown.
    """
    summary = {'total_probes': 0, 'works': 0, 'detected': 0, 'failed': 0}

    # Look for "Status (N)" text
    status_header = soup.find(lambda tag: tag.name in ('h2', 'h3', 'strong')
                              and re.match(r'Status\s*\((\d+)\)', tag.get_text()))
    if status_header:
        m = re.search(r'\((\d+)\)', status_header.get_text())
        if m:
            summary['total_probes'] = int(m.group(1))

    # Parse the status table for sample probes
    probes = []
    status_table = None

    # Find the status table - it follows the "Status" header
    candidate = status_header
    if candidate:
        table = candidate.find_next('table')
        if table:
            status_table = table

    if not status_table:
        return summary, probes

    rows = status_table.find_all('tr')
    for row in rows[1:]:  # skip header
        cells = row.find_all('td')
        if len(cells) < 6:
            continue

        hwid_link = cells[0].find('a')
        hwid_text = cells[0].get_text(strip=True)
        # HWID text looks like "7A15F»" — remove the » arrow
        hwid = hwid_text.rstrip('»').strip() if hwid_text else ''

        # Computer type (e.g., desktop, notebook)
        comp_type = cells[1].get_text(strip=True)

        # Vendor / Model
        vendor_model = cells[2].get_text(strip=True).replace('\n', ' / ').strip()

        # Probes count
        probes_link = cells[3].find('a')
        probes_count = 0
        if probes_link:
            try:
                probes_count = int(probes_link.get_text(strip=True))
            except ValueError:
                pass

        # System (distro + version)
        system = cells[4].get_text(strip=True)

        # Status
        status = cells[5].get_text(strip=True).lower()

        # Comment (in a separate row or as an additional cell sometimes)
        comment = ''
        # Check if there's a quote/comment nearby
        quote_img = cells[5].find('img', alt=re.compile(r'Quote', re.I))
        if quote_img:
            # The comment might be in a sibling div or the next row
            parent = quote_img.find_parent()
            if parent:
                comment_text = parent.get_text(strip=True)
                # Remove the status text from the comment
                comment = re.sub(r'^' + re.escape(status), '', comment_text).strip()

        probes.append(ProbeStatus(
            hwid=hwid,
            computer_type=comp_type,
            vendor='',
            model=vendor_model,
            probes=probes_count,
            system=system,
            status=status,
            comment=comment,
        ))

    # Count statuses
    for p in probes:
        if p.status == 'works':
            summary['works'] += 1
        elif p.status == 'detected':
            summary['detected'] += 1
        elif p.status == 'failed':
            summary['failed'] += 1

    return summary, probes


def parse_device_detail(html: str, url: str, category: str = '') -> DeviceInfo:
    """Parse a device detail page into a DeviceInfo dataclass."""
    soup = BeautifulSoup(html, 'html.parser')

    meta = _extract_metadata(soup)
    kernel_drivers = _extract_kernel_drivers(soup)
    other_drivers = _extract_other_drivers(soup)
    status_summary, sample_probes = _extract_status_summary(soup)

    device = DeviceInfo(
        device_id=meta['device_id'],
        bus=meta['bus'],
        vendor_id=meta['vendor_id'],
        device_code=meta['device_code'],
        subvendor_id=meta['subvendor_id'],
        subdevice_code=meta['subdevice_code'],
        class_id=meta['class_id'],
        device_type=meta['device_type'],
        vendor_name=meta['vendor_name'],
        device_name=meta['device_name'],
        subsystem_name=meta['subsystem_name'],
        category=category,
        kernel_drivers=kernel_drivers,
        other_drivers=other_drivers,
        probes_total=status_summary['total_probes'],
        status_summary={
            'works': status_summary['works'],
            'detected': status_summary['detected'],
            'failed': status_summary['failed'],
        },
        sample_probes=sample_probes[:20],  # Keep first 20 as sample
        source_url=url,
    )

    return device


# ---------------------------------------------------------------------------
# Pipeline: Category-specific search and scrape
# ---------------------------------------------------------------------------

CATEGORY_CONFIG = {
    'gpu-nvidia': {
        'search_url': '/?view=search&vendor=NVIDIA&typeid=graphics+card&page={page}',
        'vendor_filters': ['Nvidia', 'NVIDIA'],
        'output_file': 'gpu_nvidia.jsonl',
    },
    'gpu-amd': {
        'search_url': '/?view=search&vendor=AMD&typeid=graphics+card&page={page}',
        'vendor_filters': ['AMD', 'Advanced Micro Devices'],
        'output_file': 'gpu_amd.jsonl',
    },
    'wifi': {
        'search_url': '/?view=search&typeid=net%2Fwireless&page={page}',
        'vendor_filters': None,  # Include all vendors
        'output_file': 'wifi.jsonl',
    },
    'network': {
        'search_url': '/?view=search&typeid=net%2Fethernet&page={page}',
        'vendor_filters': None,
        'output_file': 'network.jsonl',
    },
    'audio': {
        'search_url': '/?view=search&typeid=sound&page={page}',
        'vendor_filters': None,
        'output_file': 'audio.jsonl',
    },
}


def scrape_category(
    category: str,
    dry_run: bool = False,
    delay: float = DEFAULT_DELAY,
    max_pages: int = 0,
    max_devices: int = 0,
) -> list[DeviceInfo]:
    """Scrape all devices in a given category.

    Returns list of DeviceInfo objects.
    """
    config = CATEGORY_CONFIG.get(category)
    if not config:
        log.error("Unknown category: %s. Options: %s", category, list(CATEGORY_CONFIG.keys()))
        return []

    devices_info = []
    page = 1
    total_pages = None

    while True:
        if max_pages > 0 and page > max_pages:
            log.info("Reached max_pages=%d limit for category '%s'", max_pages, category)
            break

        search_url = make_absolute(config['search_url'].format(page=page))
        log.info("Category '%s': fetching search page %d...", category, page)
        html = fetch_html(search_url, dry_run=dry_run, delay=delay)
        if not html:
            if dry_run:
                # In dry run, simulate some data
                log.info("[DRY-RUN] Would parse search page %d", page)
                if page >= 3:  # Simulate just 3 pages in dry run
                    break
                page += 1
                continue
            break

        # Determine total pages on first fetch
        if total_pages is None:
            total_pages = parse_search_pagination(html)
            log.info("Category '%s' has ~%d pages", category, total_pages)

        # Parse device list
        device_refs = parse_search_results(html)
        if not device_refs:
            log.info("No more devices found on page %d", page)
            break

        log.info("Found %d devices on page %d", len(device_refs), page)

        for ref in device_refs:
            # Apply vendor filter if configured
            if config['vendor_filters']:
                # Always include for GPU categories — the search is already filtered
                pass

            if max_devices > 0 and len(devices_info) >= max_devices:
                log.info("Reached max_devices=%d limit", max_devices)
                return devices_info

            device_id = ref['device_id']
            if not device_id:
                continue

            # Fetch detail page
            detail_url = make_absolute(f'/?id={device_id}')
            log.debug("Fetching device detail: %s", device_id)
            detail_html = fetch_html(detail_url, dry_run=dry_run, delay=delay)

            if detail_html:
                device = parse_device_detail(detail_html, detail_url, category=category)
                devices_info.append(device)
                log.info(
                    "Scraped: %s | %s | kernel_drivers=%d | other_drivers=%d | probes=%d",
                    device.vendor_name,
                    device.device_name[:60] if device.device_name else '(no name)',
                    len(device.kernel_drivers),
                    len(device.other_drivers),
                    device.probes_total,
                )
            elif dry_run:
                # Simulate a device entry in dry-run mode
                devices_info.append(DeviceInfo(
                    device_id=device_id,
                    vendor_name=ref['vendor'],
                    device_name=ref['device_name'],
                    device_type=ref['device_type'],
                    category=category,
                    source_url=detail_url,
                ))
                log.info("[DRY-RUN] Would scrape: %s - %s", ref['vendor'], ref['device_name'][:60])

        # Check if there are more pages
        if total_pages and page >= total_pages:
            break
        page += 1

    return devices_info


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def device_to_jsonl(device: DeviceInfo) -> str:
    """Serialize a DeviceInfo to a JSON line."""
    d = asdict(device)

    # Convert dataclass fields for JSON serialization
    d['kernel_drivers'] = [asdict(kd) for kd in device.kernel_drivers]
    d['other_drivers'] = [asdict(od) for od in device.other_drivers]
    d['sample_probes'] = [asdict(ps) for ps in device.sample_probes]

    return json.dumps(d, ensure_ascii=False, default=str)


def write_output(devices: list[DeviceInfo], output_dir: str, category: str):
    """Write scraped devices to a JSONL file."""
    config = CATEGORY_CONFIG.get(category)
    filename = config['output_file'] if config else f'{category}.jsonl'
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        for device in devices:
            line = device_to_jsonl(device)
            f.write(line + '\n')

    log.info("Wrote %d devices to %s", len(devices), filepath)
    return filepath


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Scrape Linux device compatibility data from linux-hardware.org",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --category gpu-nvidia --max-devices 10\n"
            "  %(prog)s --category wifi --max-pages 5\n"
            "  %(prog)s --all --dry-run\n"
            "  %(prog)s --all --max-devices 50\n"
        ),
    )

    parser.add_argument(
        '--category', '-c',
        choices=list(CATEGORY_CONFIG.keys()),
        help='Device category to scrape',
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Scrape all categories',
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help="Don't fetch pages, just show what would be done",
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=DEFAULT_DELAY,
        help=f"Delay between requests in seconds (default: {DEFAULT_DELAY})",
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=0,
        help='Maximum search result pages to scrape per category (0 = all)',
    )
    parser.add_argument(
        '--max-devices',
        type=int,
        default=0,
        help='Maximum devices to scrape per category (0 = all)',
    )
    parser.add_argument(
        '--output-dir', '-o',
        default=DEFAULT_OUTPUT_DIR,
        help=f'Output directory (default: {DEFAULT_OUTPUT_DIR})',
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose logging',
    )

    args = parser.parse_args(argv)

    if not args.category and not args.all:
        parser.error("Specify --category or --all")

    if args.verbose:
        log.setLevel(logging.DEBUG)

    return args


def main(argv=None):
    args = parse_args(argv)

    categories = list(CATEGORY_CONFIG.keys()) if args.all else [args.category]

    log.info(
        "Starting linux-hardware.org scraper (dry_run=%s, delay=%.1fs)",
        args.dry_run,
        args.delay,
    )
    log.info("Categories: %s", ', '.join(categories))
    log.info("Output dir: %s", args.output_dir)

    os.makedirs(args.output_dir, exist_ok=True)

    all_devices = {}

    for cat in categories:
        log.info("=" * 60)
        log.info("Scraping category: %s", cat)
        log.info("=" * 60)

        devices = scrape_category(
            category=cat,
            dry_run=args.dry_run,
            delay=args.delay,
            max_pages=args.max_pages,
            max_devices=args.max_devices,
        )

        all_devices[cat] = devices

        if not args.dry_run:
            filepath = write_output(devices, args.output_dir, cat)
        else:
            log.info("[DRY-RUN] Would write %d devices to %s/%s",
                     len(devices), args.output_dir, CATEGORY_CONFIG[cat]['output_file'])

    # Print summary
    log.info("=" * 60)
    log.info("SUMMARY")
    log.info("=" * 60)
    for cat, devices in all_devices.items():
        log.info("  %-15s : %d devices", cat, len(devices))
        if not args.dry_run and devices:
            # Quick stats
            with_kernel = sum(1 for d in devices if d.kernel_drivers)
            with_other = sum(1 for d in devices if d.other_drivers)
            total_probes = sum(d.probes_total for d in devices)
            log.info("    with kernel drivers : %d", with_kernel)
            log.info("    with other drivers  : %d", with_other)
            log.info("    total probes        : %d", total_probes)
    log.info("=" * 60)


if __name__ == '__main__':
    main()