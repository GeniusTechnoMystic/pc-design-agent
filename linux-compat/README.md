# Linux Hardware Scraper

Scrape device compatibility data from [linux-hardware.org](https://linux-hardware.org/) for PC design decisions.

## Purpose

Collects real-world Linux compatibility data for:

| Category | Description | Devices |
|----------|-------------|--------|
| **GPU (NVIDIA)** | NVIDIA graphics cards | ~12,500+ |
| **GPU (AMD)** | AMD/ATI graphics cards | ~9,900+ |
| **Wi-Fi** | Wireless network chips | ~2,500+ |
| **Network** | Ethernet controllers | ~3,600+ |
| **Audio** | Sound cards / audio codecs | ~35,000+ |

Per device, the scraper collects:

- **Kernel drivers** — LKDDb entries showing which kernel versions support the device, with source file and config option
- **Other drivers** — Proprietary/third-party drivers (e.g., `nvidia`), with minimum version
- **Status data** — Probe results from real computers: how many report "works", "detected", or "failed"
- **Sample probes** — Up to 20 representative probe rows with distro, kernel, system type, and any user comments

## Requirements

- Python 3.10+
- `pip install -r requirements.txt`

## Usage

```bash
# Dry run (show what would be done without fetching)
python linux_hardware_scraper.py --category gpu-nvidia --dry-run

# Scrape a single category (10 devices)
python linux_hardware_scraper.py --category gpu-nvidia --max-devices 10

# Scrape all categories
python linux_hardware_scraper.py --all --max-pages 2

# Scrape with custom delay and output directory
python linux_hardware_scraper.py --category wifi --delay 2.0 --output-dir ./data
```

### Options

| Flag | Description |
|------|-------------|
| `--category, -c` | Category to scrape: `gpu-nvidia`, `gpu-amd`, `wifi`, `network`, `audio` |
| `--all, -a` | Scrape all categories |
| `--dry-run, -n` | Show planned operations without making HTTP requests |
| `--delay` | Seconds between requests (default: 1.5) |
| `--max-pages` | Max search result pages per category (default: all) |
| `--max-devices` | Max device detail pages per category (default: all) |
| `--output-dir, -o` | Output directory (default: current dir) |
| `--verbose, -v` | Verbose/debug logging |

## Output Format

[JSONL](https://jsonlines.org/) — one JSON object per line, each representing one device:

```json
{
  "device_id": "pci:10de-2684-1462-5103",
  "bus": "pci",
  "vendor_id": "10de",
  "device_code": "2684",
  "subvendor_id": "1462",
  "subdevice_code": "5103",
  "class_id": "03-00-00",
  "device_type": "graphics card",
  "vendor_name": "Nvidia",
  "device_name": "AD102 [GeForce RTX 4090]",
  "subsystem_name": "Micro-Star International [MSI]",
  "category": "gpu-nvidia",
  "kernel_drivers": [
    {
      "kernel_range": "3.7 - 7.0",
      "source": "drivers/gpu/drm/nouveau/nouveau_drm.c",
      "config": "CONFIG_DRM_NOUVEAU",
      "by_id": "10de:*",
      "by_class": "03"
    }
  ],
  "other_drivers": [
    {
      "name": "nvidia",
      "version_range": "530.41.03 and newer"
    }
  ],
  "probes_total": 48,
  "status_summary": {"works": 7, "detected": 0, "failed": 41},
  "sample_probes": [...],
  "source_url": "https://linux-hardware.org/?id=pci:10de-2684-1462-5103"
}
```

### Output Files

| File | Category |
|------|----------|
| `gpu_nvidia.jsonl` | NVIDIA GPUs |
| `gpu_amd.jsonl` | AMD GPUs |
| `wifi.jsonl` | Wi-Fi chips |
| `network.jsonl` | Network controllers |
| `audio.jsonl` | Audio codecs |

## Data Source

[linux-hardware.org](https://linux-hardware.org/) collects anonymous hardware probes from Linux users worldwide
via the [hw-probe](https://github.com/linuxhw/hw-probe) tool. The database contains probes from **355,000+ computers**
and **599,000+ tested parts** (as of mid-2026).

This scraper reads:

1. **Search pages** — `/?view=search&vendor=NVIDIA&typeid=graphics+card&page=1`
2. **Device detail pages** — `/?id=pci:10de-2684`

There is no official JSON API, so the scraper parses HTML pages with BeautifulSoup.
A 1.5-second delay between requests is applied to avoid overloading the server.

## Ethics

- Respects robots.txt conventions
- Configurable delay between requests (default 1.5s)
- Dry-run mode available for planning
- Data is already public — we're just collecting it systematically
- Consider running during off-peak hours for large scrapes