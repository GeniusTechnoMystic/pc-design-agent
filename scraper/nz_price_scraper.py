#!/usr/bin/env python3
"""
NZ Retailer Price Scraper for PC Design Agent.

Scrapes PC component prices from NZ retailers and outputs as JSONL.
Designed to run as a cron job.

Usage:
    python nz_price_scraper.py --config prices.yaml              # normal run
    python nz_price_scraper.py --config prices.yaml --dry-run    # preview only
    python nz_price_scraper.py --config prices.yaml --retailer pbtech  # single retailer

Output format (JSONL, one JSON object per line):
    {
        "product_name": "AMD Ryzen 7 7800X3D",
        "price": 749.00,
        "currency": "NZD",
        "retailer": "pbtech",
        "source_url": "https://www.pbtech.co.nz/...",
        "in_stock": true,
        "stock_status": "In Stock",
        "category": "cpu",
        "timestamp": "2025-07-21T10:30:00+1200"
    }
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlencode, quote_plus

import requests
from bs4 import BeautifulSoup, Tag

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ScrapedProduct:
    """A single product price observation."""
    product_name: str
    price: float
    currency: str = "NZD"
    retailer: str = ""
    source_url: str = ""
    in_stock: bool = True
    stock_status: str = "In Stock"
    category: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            # NZ is UTC+12 / UTC+13 during daylight saving
            nz_tz = timezone(timedelta(hours=12))
            self.timestamp = datetime.now(nz_tz).strftime("%Y-%m-%dT%H:%M:%S%z")

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class ScraperConfig:
    """Parsed configuration from YAML."""
    retailers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=lambda: {
        "request_timeout": 30,
        "retry_attempts": 2,
        "retry_delay": 5,
        "output_dir": os.path.expanduser("~/.hermes/data/pc-design-agent/prices/"),
        "date_format": "%Y-%m-%dT%H:%M:%S%z",
        "log_level": "INFO",
    })

    @classmethod
    def from_yaml(cls, path: str) -> "ScraperConfig":
        import yaml
        with open(path, "r") as f:
            raw = yaml.safe_load(f)
        config = cls()
        config.retailers = raw.get("retailers", {})
        if "settings" in raw:
            config.settings.update(raw["settings"])
        # Expand ~ in paths
        if "output_dir" in config.settings:
            config.settings["output_dir"] = os.path.expanduser(
                config.settings["output_dir"]
            )
        return config


# ---------------------------------------------------------------------------
# Price parsing helpers
# ---------------------------------------------------------------------------

_PRICE_CLEAN_RE = re.compile(r"[^0-9.]")
_NZD_SYMBOL_RE = re.compile(r"[$＄]")

def parse_price(text: str) -> Optional[float]:
    """
    Extract a NZD price from text like "$749.00", "NZ$ 1,299", "$1,200.50".
    Returns a float or None if no price found.
    """
    if not text:
        return None
    # Remove common prefix symbols
    cleaned = _NZD_SYMBOL_RE.sub("", text).strip()
    # Remove commas
    cleaned = cleaned.replace(",", "")
    # Keep only digits and dots
    cleaned = _PRICE_CLEAN_RE.sub("", cleaned)
    # Remove empty trailing/leading dots
    cleaned = cleaned.strip(".")
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def parse_stock_status(text: str) -> tuple:
    """
    Parse stock status text. Returns (in_stock: bool, status_label: str).
    """
    if not text:
        return True, "In Stock"
    lower = text.strip().lower()
    if any(word in lower for word in ("out of stock", "outofstock", "sold out", "discontinued", "unavailable")):
        return False, "Out of Stock"
    if "pre-order" in lower or "preorder" in lower:
        return False, "Pre-order"
    if "low stock" in lower or "lowstock" in lower or "limited stock" in lower:
        return True, "Low Stock"
    if any(word in lower for word in ("in stock", "instock", "available", "add to cart", "buy now")):
        return True, "In Stock"
    # Default: assume in stock
    return True, "In Stock"


# ---------------------------------------------------------------------------
# Retailer-specific parsers
# ---------------------------------------------------------------------------

class BaseRetailerParser:
    """Base class for retailer-specific HTML parsing."""

    retailer_name = ""

    def parse_listing(self, html: str, url: str, category: str,
                      logger: logging.Logger) -> List[ScrapedProduct]:
        """
        Parse a listing/category page and extract product data.
        Override in subclasses for retailer-specific markup.
        Returns a list of ScrapedProduct.
        """
        raise NotImplementedError

    def parse_product_page(self, html: str, url: str, category: str,
                           logger: logging.Logger) -> Optional[ScrapedProduct]:
        """
        Parse a single product detail page. Falls back to generic parser
        if not overridden.
        """
        return self._generic_parse_detail(html, url, category, logger)

    # ------------------------------------------------------------------
    # Generic fallback parsers — try common HTML patterns
    # ------------------------------------------------------------------

    def _generic_parse_listing(self, html: str, url: str, category: str,
                                logger: logging.Logger) -> List[ScrapedProduct]:
        """Fallback: try common listing page structures."""
        soup = BeautifulSoup(html, "html.parser")
        products: List[ScrapedProduct] = []
        candidates = []

        # Try by common container selectors
        for selector in (
            ".product-item", ".product-card", ".product", ".item",
            "[class*=product]", "[class*=item]", "article",
            ".listing-product", ".category-product", ".grid > div",
            "li.product", "li.item", "tr.product-row",
        ):
            candidates.extend(soup.select(selector))

        # Deduplicate (a node might match multiple selectors)
        seen_ids = set()
        for el in candidates:
            el_id = id(el)
            if el_id in seen_ids:
                continue
            seen_ids.add(el_id)
            product = self._extract_product_from_card(el, url, category, logger)
            if product:
                products.append(product)

        # If no structured containers found, try table rows
        if not products:
            rows = soup.select("table tr")
            for row in rows:
                product = self._extract_product_from_table_row(row, url, category, logger)
                if product:
                    products.append(product)

        # If still nothing, try a loose text-based extraction
        if not products:
            # Look for price-like patterns in text nodes
            price_pattern = re.compile(r"\$\s*[\d,]+\.?\d{0,2}")
            for el in soup.find_all(["div", "span", "li"]):
                text = el.get_text(strip=True)
                if price_pattern.search(text) and el.find("a"):
                    product = self._extract_product_from_card(el, url, category, logger)
                    if product:
                        products.append(product)

        return products

    def _extract_product_from_card(self, el: Tag, base_url: str,
                                    category: str,
                                    logger: logging.Logger) -> Optional[ScrapedProduct]:
        """Extract product data from a product card/list element."""
        try:
            # Name — find anchor or heading
            name_el = el.find(["a", "h2", "h3", "h4", "span", "div"],
                              class_=re.compile(r"(name|title|product-name|heading)", re.I))
            if not name_el:
                name_el = el.find("a")
            if not name_el:
                name_el = el.find(["h2", "h3", "h4"])
            if not name_el:
                return None

            product_name = name_el.get_text(strip=True)
            if not product_name or len(product_name) < 3:
                return None

            # URL
            href = name_el.get("href", "")
            if href and not href.startswith(("http://", "https://")):
                source_url = urljoin(base_url, href)
            elif href:
                source_url = href
            else:
                source_url = base_url

            # Price
            price_el = el.find(class_=re.compile(r"(price|cost|amount|sale-price)", re.I))
            if not price_el:
                price_el = el.find(["span", "div", "strong", "b"],
                                    string=re.compile(r"[\$＄]"))
            if not price_el:
                # Fallback: scan text for price pattern
                full_text = el.get_text()
                price_match = re.search(r"[\$＄]\s*(\d[\d,]*\.?\d*)", full_text)
                if price_match:
                    price = parse_price(price_match.group(0))
                else:
                    return None
            else:
                price = parse_price(price_el.get_text(strip=True))

            if price is None or price <= 0:
                return None

            # Stock status
            stock_el = el.find(class_=re.compile(r"(stock|availability|status)", re.I))
            in_stock = True
            stock_status = "In Stock"
            if stock_el:
                in_stock, stock_status = parse_stock_status(stock_el.get_text(strip=True))

            return ScrapedProduct(
                product_name=product_name,
                price=price,
                retailer=self.retailer_name,
                source_url=source_url,
                in_stock=in_stock,
                stock_status=stock_status,
                category=category,
            )
        except Exception as exc:
            logger.debug("Failed to extract from card element: %s", exc)
            return None

    def _extract_product_from_table_row(self, row: Tag, base_url: str,
                                         category: str,
                                         logger: logging.Logger) -> Optional[ScrapedProduct]:
        """Extract product data from a table row."""
        try:
            cells = row.find_all("td")
            if len(cells) < 2:
                return None
            link = row.find("a")
            if not link:
                return None

            product_name = link.get_text(strip=True)
            if not product_name or len(product_name) < 3:
                return None

            href = link.get("href", "")
            if href and not href.startswith(("http://", "https://")):
                source_url = urljoin(base_url, href)
            elif href:
                source_url = href
            else:
                source_url = base_url

            # Price is likely in one of the later cells
            price = None
            for cell in cells[1:]:
                price = parse_price(cell.get_text(strip=True))
                if price and price > 0:
                    break

            if not price or price <= 0:
                return None

            return ScrapedProduct(
                product_name=product_name,
                price=price,
                retailer=self.retailer_name,
                source_url=source_url,
                category=category,
            )
        except Exception as exc:
            logger.debug("Failed to extract from table row: %s", exc)
            return None

    def _generic_parse_detail(self, html: str, url: str, category: str,
                               logger: logging.Logger) -> Optional[ScrapedProduct]:
        """Parse a single product detail page."""
        soup = BeautifulSoup(html, "html.parser")

        # Product name
        name_el = (soup.find("h1")
                   or soup.find(class_=re.compile(r"(product-name|product-title|name)", re.I))
                   or soup.find("title"))
        if not name_el:
            return None
        product_name = name_el.get_text(strip=True)
        if not product_name or len(product_name) < 3:
            return None
        # Remove " - RetailerName" suffixes from <title>
        product_name = re.sub(r"\s*[—\-|]\s*[^—\-|]+$", "", product_name).strip()

        # Price
        price_el = (soup.find(class_=re.compile(r"(price|our-price|sale-price)", re.I))
                    or soup.find(["span", "div", "meta"], itemprop="price")
                    or soup.find(["span", "div", "strong"],
                                 string=re.compile(r"[\$＄]")))
        price = None
        if price_el:
            if price_el.name == "meta":
                price = parse_price(price_el.get("content", ""))
            else:
                price = parse_price(price_el.get_text(strip=True))

        if not price or price <= 0:
            return None

        # Stock status
        stock_el = (soup.find(class_=re.compile(r"(stock|availability|status)", re.I))
                    or soup.find(string=re.compile(r"(in stock|out of stock)", re.I)))
        in_stock = True
        stock_status = "In Stock"
        if stock_el:
            txt = stock_el if isinstance(stock_el, str) else stock_el.get_text(strip=True)
            in_stock, stock_status = parse_stock_status(txt)

        return ScrapedProduct(
            product_name=product_name,
            price=price,
            retailer=self.retailer_name,
            source_url=url,
            in_stock=in_stock,
            stock_status=stock_status,
            category=category,
        )


# ---------------------------------------------------------------------------
# Concrete retailer parsers
# ---------------------------------------------------------------------------

class PBtechParser(BaseRetailerParser):
    """PB Tech (pbtech.co.nz) — search-based scraper."""
    retailer_name = "pbtech"

    def parse_listing(self, html: str, url: str, category: str,
                      logger: logging.Logger) -> List[ScrapedProduct]:
        soup = BeautifulSoup(html, "html.parser")
        products = []

        # PB Tech typically uses .product-listing-item or .product-item
        for card in soup.select(".product-item, .product-listing-item, [class*=product]"):
            product = self._extract_product_from_card(card, url, category, logger)
            if product:
                products.append(product)

        # Fallback to generic parser
        if not products:
            products = self._generic_parse_listing(html, url, category, logger)

        return products


class ComputerLoungeParser(BaseRetailerParser):
    """Computer Lounge (computerlounge.co.nz)."""
    retailer_name = "computerlounge"

    def parse_listing(self, html: str, url: str, category: str,
                      logger: logging.Logger) -> List[ScrapedProduct]:
        soup = BeautifulSoup(html, "html.parser")
        products = []

        # Look for product cards, grid items
        for card in soup.select(
            ".product-grid-item, .product-card, .item, [class*=product]"
        ):
            product = self._extract_product_from_card(card, url, category, logger)
            if product:
                products.append(product)

        # Fallback
        if not products:
            products = self._generic_parse_listing(html, url, category, logger)

        return products


class MightyApeParser(BaseRetailerParser):
    """Mighty Ape (mightyape.co.nz)."""
    retailer_name = "mightyape"

    def parse_listing(self, html: str, url: str, category: str,
                      logger: logging.Logger) -> List[ScrapedProduct]:
        soup = BeautifulSoup(html, "html.parser")
        products = []

        # Mighty Ape uses .ProductListItem, .product-item, etc.
        for card in soup.select(
            ".ProductListItem, .product-item, [data-product], .listing-item"
        ):
            product = self._extract_product_from_card(card, url, category, logger)
            if product:
                products.append(product)

        # Fallback
        if not products:
            products = self._generic_parse_listing(html, url, category, logger)

        return products


class FirstWaveParser(BaseRetailerParser):
    """1st Wave (1stwave.co.nz)."""
    retailer_name = "1stwave"

    def parse_listing(self, html: str, url: str, category: str,
                      logger: logging.Logger) -> List[ScrapedProduct]:
        soup = BeautifulSoup(html, "html.parser")
        products = []

        for card in soup.select(
            ".product-item, .product-card, .product, [class*=product]"
        ):
            product = self._extract_product_from_card(card, url, category, logger)
            if product:
                products.append(product)

        if not products:
            products = self._generic_parse_listing(html, url, category, logger)

        return products


class ParadigmPcsParser(BaseRetailerParser):
    """Paradigm PCs (paradigmpcs.co.nz)."""
    retailer_name = "paradigmpcs"

    def parse_listing(self, html: str, url: str, category: str,
                      logger: logging.Logger) -> List[ScrapedProduct]:
        soup = BeautifulSoup(html, "html.parser")
        products = []

        for card in soup.select(
            ".product-item, .product-card, .product, [class*=product], .grid__item"
        ):
            product = self._extract_product_from_card(card, url, category, logger)
            if product:
                products.append(product)

        if not products:
            products = self._generic_parse_listing(html, url, category, logger)

        return products


# ---------------------------------------------------------------------------
# Registry of parsers
# ---------------------------------------------------------------------------

PARSERS: Dict[str, BaseRetailerParser] = {
    "pbtech": PBtechParser(),
    "computerlounge": ComputerLoungeParser(),
    "mightyape": MightyApeParser(),
    "1stwave": FirstWaveParser(),
    "paradigmpcs": ParadigmPcsParser(),
}


# ---------------------------------------------------------------------------
# HTTP session
# ---------------------------------------------------------------------------

def build_session(user_agent: Optional[str] = None) -> requests.Session:
    """Create a requests session with sensible defaults."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-NZ,en;q=0.9",
    })
    # Rotate Accept-Encoding to avoid compression issues
    session.headers["Accept-Encoding"] = "gzip, deflate"
    return session


# ---------------------------------------------------------------------------
# Scraper engine
# ---------------------------------------------------------------------------

class NZPriceScraper:
    """Main scraper engine."""

    def __init__(self, config: ScraperConfig, dry_run: bool = False,
                 log_level: str = "INFO"):
        self.config = config
        self.dry_run = dry_run
        self.session = build_session()
        self.results: List[ScrapedProduct] = []
        self.errors: List[Dict[str, Any]] = []
        self._setup_logging(log_level)

    def _setup_logging(self, level: str):
        self.logger = logging.getLogger("nz_price_scraper")
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def run(self, retailer_filter: Optional[str] = None) -> List[ScrapedProduct]:
        """
        Run the scraper for all configured retailers, or a single retailer
        if retailer_filter is provided.
        """
        for retailer_name, retailer_cfg in self.config.retailers.items():
            if retailer_filter and retailer_name != retailer_filter:
                continue
            self._scrape_retailer(retailer_name, retailer_cfg)

        self._write_output()
        return self.results

    def _scrape_retailer(self, name: str, cfg: Dict[str, Any]):
        """Scrape all component listings from one retailer."""
        base_url = cfg["base_url"].rstrip("/")
        components = cfg.get("components", [])
        user_agent = cfg.get("user_agent")
        parser = PARSERS.get(name)

        if not parser:
            self.logger.warning("No parser available for retailer: %s", name)
            return

        if not components:
            self.logger.warning("No components configured for retailer: %s", name)
            return

        for comp in components:
            if "query" in comp:
                # Search-based (PB Tech)
                query = comp["query"]
                search_path = cfg.get("search_path", "/search?q={query}")
                search_url = base_url + search_path.replace("{query}", quote_plus(query))
                self.logger.info(
                    "[%s] Searching: %s (query=%s)", name, search_url, query
                )
            elif "url" in comp:
                # URL-based
                path = comp["url"].lstrip("/")
                search_url = f"{base_url}/{path}"
                self.logger.info(
                    "[%s] Fetching: %s", name, search_url
                )
            else:
                self.logger.warning(
                    "[%s] Component entry has no query or url: %s", name, comp
                )
                continue

            category = comp.get("category", "unknown")

            if self.dry_run:
                self.logger.info("[DRY RUN] Would scrape: %s", search_url)
                continue

            try:
                html = self._fetch_with_retry(search_url)
                if html is None:
                    continue

                products = parser.parse_listing(html, search_url, category, self.logger)
                self.logger.info(
                    "[%s] Found %d product(s) for category '%s'",
                    name, len(products), category
                )
                self.results.extend(products)

                # Be polite: small delay between pages
                time.sleep(1.5)

            except requests.RequestException as exc:
                msg = f"HTTP error scraping {search_url}: {exc}"
                self.logger.error(msg)
                self.errors.append({"url": search_url, "error": str(exc), "retailer": name})
            except Exception as exc:
                msg = f"Unexpected error scraping {search_url}: {exc}"
                self.logger.error(msg)
                self.errors.append({"url": search_url, "error": str(exc), "retailer": name})

    def _fetch_with_retry(self, url: str) -> Optional[str]:
        """Fetch a URL with retry logic. Returns HTML text or None."""
        settings = self.config.settings
        max_attempts = settings.get("retry_attempts", 2) + 1
        timeout = settings.get("request_timeout", 30)

        for attempt in range(1, max_attempts + 1):
            try:
                resp = self.session.get(url, timeout=timeout)
                # Check for CAPTCHA or bot detection
                resp.raise_for_status()
                # Detect CAPTCHA/block pages by looking for common keywords
                text_lower = resp.text.lower()
                if any(word in text_lower for word in
                       ("captcha", "cf-browser-verify", "just a moment",
                        "please enable javascript", "blocked", "access denied")):
                    self.logger.warning(
                        "Possible CAPTCHA/block on %s (attempt %d/%d)",
                        url, attempt, max_attempts
                    )
                    if attempt < max_attempts:
                        delay = settings.get("retry_delay", 5)
                        time.sleep(delay)
                        continue
                    return None
                return resp.text
            except requests.Timeout:
                self.logger.warning(
                    "Timeout fetching %s (attempt %d/%d)",
                    url, attempt, max_attempts
                )
                if attempt < max_attempts:
                    time.sleep(settings.get("retry_delay", 5))
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response else 0
                if status == 404:
                    self.logger.warning("404 on %s — skipping", url)
                    return None
                if status in (429, 503) and attempt < max_attempts:
                    self.logger.warning(
                        "Rate-limited/server-busy on %s (attempt %d/%d)",
                        url, attempt, max_attempts
                    )
                    time.sleep(settings.get("retry_delay", 5) * attempt)
                    continue
                self.logger.error("HTTP %d on %s: %s", status, url, exc)
                return None
            except requests.RequestException as exc:
                self.logger.error("Request error on %s: %s", url, exc)
                return None
        return None

    def _write_output(self):
        """Write results as JSONL to the output directory."""
        if self.dry_run:
            self.logger.info("Dry run — no output written.")
            return

        output_dir = self.config.settings.get("output_dir", ".")
        os.makedirs(output_dir, exist_ok=True)

        nz_tz = timezone(timedelta(hours=12))
        timestamp = datetime.now(nz_tz).strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"prices_{timestamp}.jsonl")

        with open(output_file, "w", encoding="utf-8") as f:
            for product in self.results:
                f.write(product.to_jsonl() + "\n")

        self.logger.info(
            "Wrote %d product(s) to %s", len(self.results), output_file
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NZ PC Component Price Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--config", "-c",
        default=os.path.expanduser(
            "~/.hermes/data/pc-design-agent/scraper/prices.yaml"
        ),
        help="Path to YAML config file",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be scraped without making HTTP requests",
    )
    parser.add_argument(
        "--retailer", "-r",
        help="Scrape only a specific retailer (by config key)",
    )
    parser.add_argument(
        "--log-level", "-l",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if not os.path.exists(args.config):
        print(f"Error: config file not found: {args.config}", file=sys.stderr)
        return 1

    config = ScraperConfig.from_yaml(args.config)
    config.settings["log_level"] = args.log_level

    scraper = NZPriceScraper(config, dry_run=args.dry_run,
                              log_level=args.log_level)

    try:
        results = scraper.run(retailer_filter=args.retailer)
    except KeyboardInterrupt:
        scraper.logger.warning("Interrupted by user")
        return 130

    # Report summary
    if args.dry_run:
        total = sum(len(r.get("components", []))
                    for r in config.retailers.values())
        print(f"Dry run: would scrape {total} component listing(s) across "
              f"{len(config.retailers)} retailer(s)")
        return 0

    if scraper.errors:
        print(f"\nErrors ({len(scraper.errors)}):", file=sys.stderr)
        for err in scraper.errors[:5]:
            print(f"  [{err['retailer']}] {err['error']}", file=sys.stderr)
        if len(scraper.errors) > 5:
            print(f"  ... and {len(scraper.errors) - 5} more", file=sys.stderr)

    print(f"\nScraped {len(results)} product(s) from "
          f"{len(set(p.retailer for p in results))} retailer(s)")
    return 0 if not scraper.errors else 1


if __name__ == "__main__":
    sys.exit(main())