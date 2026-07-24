#!/usr/bin/env bash
# =============================================================================
# scrape_prices.sh — Cron wrapper for NZ PC Component Price Scraper
# =============================================================================
# Designed to run as a cron job. Sources the project .env file,
# runs the scraper, and handles logging.
#
# Usage:
#   ./scrape_prices.sh                          # normal run
#   ./scrape_prices.sh --dry-run                # preview mode
#   ./scrape_prices.sh --retailer pbtech        # single retailer
#   ./scrape_prices.sh --log-level DEBUG        # verbose logging
#
# Cron example (runs daily at 6 AM NZ time):
#   0 6 * * * /home/hermes/.hermes/data/pc-design-agent/scraper/scrape_prices.sh
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$HOME/.hermes/projects/pc-design-agent"
DATA_DIR="$HOME/.hermes/data/pc-design-agent"
SCRAPER_DIR="$DATA_DIR/scraper"
PRICES_DIR="$DATA_DIR/prices"
LOG_DIR="$HOME/.hermes/logs"
PYTHON="${PYTHON:-python3}"

# ---------------------------------------------------------------------------
# Ensure directories exist
# ---------------------------------------------------------------------------
mkdir -p "$PRICES_DIR" "$LOG_DIR"

# ---------------------------------------------------------------------------
# Source .env if present
# ---------------------------------------------------------------------------
ENV_FILE="$PROJECT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$ENV_FILE"
    set +a
fi

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/scraper_$TIMESTAMP.log"
ERROR_LOG="$LOG_DIR/scraper_$TIMESTAMP.err"

# ---------------------------------------------------------------------------
# Check dependencies
# ---------------------------------------------------------------------------
command -v "$PYTHON" >/dev/null 2>&1 || { echo "ERROR: $PYTHON not found"; exit 1; }

# Check if requirements are installed (fast check)
"$PYTHON" -c "import yaml, bs4, requests" 2>/dev/null || {
    echo "Installing Python dependencies..."
    pip3 install -r "$SCRAPER_DIR/requirements.txt" >> "$LOG_FILE" 2>&1
}

# ---------------------------------------------------------------------------
# Run scraper
# ---------------------------------------------------------------------------
cd "$SCRAPER_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting price scraper..." | tee -a "$LOG_FILE"

# Forward all CLI args to the Python scraper
"$PYTHON" nz_price_scraper.py \
    --config "$SCRAPER_DIR/prices.yaml" \
    "$@" \
    >> "$LOG_FILE" 2>> "$ERROR_LOG"

EXIT_CODE=$?

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Scraper finished with exit code $EXIT_CODE" \
    | tee -a "$LOG_FILE"

# ---------------------------------------------------------------------------
# Report errors
# ---------------------------------------------------------------------------
if [ $EXIT_CODE -ne 0 ]; then
    echo "ERROR: Scraper exited with code $EXIT_CODE" | tee -a "$ERROR_LOG"
fi

# Rotate logs — keep last 30 days
find "$LOG_DIR" -name "scraper_*.log" -type f -mtime +30 -delete 2>/dev/null || true
find "$LOG_DIR" -name "scraper_*.err" -type f -mtime +30 -delete 2>/dev/null || true

exit $EXIT_CODE