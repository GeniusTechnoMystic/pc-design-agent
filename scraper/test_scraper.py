#!/usr/bin/env python3
"""
Tests for NZ Retailer Price Scraper.

Tests the config parser, data model, price parsing, stock status parsing,
and HTTP mocking of the scraper pipeline — without hitting real endpoints.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import yaml

# Ensure the scraper directory is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# ---------------------------------------------------------------------------
# Import the scraper module
# ---------------------------------------------------------------------------

from nz_price_scraper import (
    NZPriceScraper,
    PARSERS,
    ScraperConfig,
    ScrapedProduct,
    BaseRetailerParser,
    ComputerLoungeParser,
    FirstWaveParser,
    MightyApeParser,
    PBtechParser,
    ParadigmPcsParser,
    build_session,
    parse_price,
    parse_stock_status,
    main,
)


# ===========================================================================
# Unit tests
# ===========================================================================

class TestParsePrice(unittest.TestCase):
    """Test the parse_price helper function."""

    def test_simple_price(self):
        self.assertEqual(parse_price("$749.00"), 749.00)

    def test_price_with_commas(self):
        self.assertEqual(parse_price("$1,299.00"), 1299.00)

    def test_price_no_cents(self):
        self.assertEqual(parse_price("$749"), 749.00)

    def test_nz_symbol(self):
        self.assertEqual(parse_price("NZ$ 1,299"), 1299.00)

    def test_price_with_text(self):
        self.assertEqual(parse_price("Price: $899.50"), 899.50)

    def test_negative_price(self):
        self.assertEqual(parse_price("$0.00"), 0.00)

    def test_non_matching_text(self):
        self.assertIsNone(parse_price("Out of stock"))
        self.assertIsNone(parse_price(""))
        self.assertIsNone(parse_price("Free"))

    def test_no_dollar_sign(self):
        # Bare number without $ is parsed as price (some retailers format this way)
        self.assertEqual(parse_price("749"), 749.0)


class TestParseStockStatus(unittest.TestCase):
    """Test the parse_stock_status helper function."""

    def test_in_stock(self):
        self.assertEqual(parse_stock_status("In Stock"), (True, "In Stock"))

    def test_out_of_stock(self):
        self.assertEqual(parse_stock_status("Out of Stock"), (False, "Out of Stock"))
        self.assertEqual(parse_stock_status("Out Of Stock"), (False, "Out of Stock"))
        self.assertEqual(parse_stock_status("Sold Out"), (False, "Out of Stock"))
        self.assertEqual(parse_stock_status("Discontinued"), (False, "Out of Stock"))
        self.assertEqual(parse_stock_status("Currently Unavailable"), (False, "Out of Stock"))

    def test_preorder(self):
        self.assertEqual(parse_stock_status("Pre-order Now"), (False, "Pre-order"))
        self.assertEqual(parse_stock_status("Preorder"), (False, "Pre-order"))

    def test_low_stock(self):
        in_stock, status = parse_stock_status("Low Stock")
        self.assertTrue(in_stock)
        self.assertEqual(status, "Low Stock")

    def test_available(self):
        self.assertEqual(parse_stock_status("Available"), (True, "In Stock"))
        self.assertEqual(parse_stock_status("Add to Cart"), (True, "In Stock"))
        self.assertEqual(parse_stock_status("Buy Now"), (True, "In Stock"))

    def test_empty(self):
        self.assertEqual(parse_stock_status(""), (True, "In Stock"))
        self.assertEqual(parse_stock_status(None), (True, "In Stock"))

    def test_case_sensitivity(self):
        self.assertEqual(parse_stock_status("IN STOCK"), (True, "In Stock"))
        self.assertEqual(parse_stock_status("OUT OF STOCK"), (False, "Out of Stock"))


class TestScrapedProduct(unittest.TestCase):
    """Test the ScrapedProduct dataclass."""

    def test_default_timestamp(self):
        """Product without explicit timestamp gets one auto-generated."""
        product = ScrapedProduct(
            product_name="Test CPU",
            price=499.00,
            retailer="pbtech",
        )
        self.assertEqual(product.product_name, "Test CPU")
        self.assertEqual(product.price, 499.00)
        self.assertEqual(product.currency, "NZD")
        self.assertEqual(product.retailer, "pbtech")
        self.assertTrue(product.in_stock)
        self.assertEqual(product.stock_status, "In Stock")
        self.assertIsNotNone(product.timestamp)

    def test_jsonl_output(self):
        product = ScrapedProduct(
            product_name="AMD Ryzen 7 7800X3D",
            price=749.00,
            retailer="pbtech",
            source_url="https://www.pbtech.co.nz/product/CPUAMR7800X3D",
            in_stock=True,
            stock_status="In Stock",
            category="cpu",
        )
        line = product.to_jsonl()
        data = json.loads(line)
        self.assertEqual(data["product_name"], "AMD Ryzen 7 7800X3D")
        self.assertEqual(data["price"], 749.00)
        self.assertEqual(data["currency"], "NZD")
        self.assertEqual(data["retailer"], "pbtech")
        self.assertTrue(data["in_stock"])
        self.assertEqual(data["category"], "cpu")
        self.assertIn("timestamp", data)

    def test_explicit_timestamp(self):
        ts = "2025-07-21T10:30:00+1200"
        product = ScrapedProduct(
            product_name="Test",
            price=100.00,
            timestamp=ts,
        )
        self.assertEqual(product.timestamp, ts)


class TestScraperConfig(unittest.TestCase):
    """Test config parsing from YAML."""

    def setUp(self):
        self.config_yaml = {
            "retailers": {
                "pbtech": {
                    "base_url": "https://www.pbtech.co.nz",
                    "search_path": "/search?q={query}",
                    "components": [
                        {"query": "CPU", "category": "cpu"},
                    ],
                },
                "computerlounge": {
                    "base_url": "https://www.computerlounge.co.nz",
                    "components": [
                        {"url": "/components/cpus", "category": "cpu"},
                    ],
                },
            },
            "settings": {
                "request_timeout": 15,
                "output_dir": "/tmp/test_prices",
            },
        }

    def test_from_yaml(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(self.config_yaml, f)
            config_path = f.name

        try:
            config = ScraperConfig.from_yaml(config_path)
            self.assertIn("pbtech", config.retailers)
            self.assertIn("computerlounge", config.retailers)
            self.assertEqual(
                config.retailers["pbtech"]["base_url"],
                "https://www.pbtech.co.nz",
            )
            self.assertEqual(config.settings["request_timeout"], 15)
            self.assertEqual(config.settings["output_dir"], "/tmp/test_prices")
        finally:
            os.unlink(config_path)

    def test_default_settings(self):
        """Missing settings should use defaults."""
        minimal = {"retailers": {}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(minimal, f)
            config_path = f.name

        try:
            config = ScraperConfig.from_yaml(config_path)
            self.assertEqual(config.settings["request_timeout"], 30)
            self.assertEqual(config.settings["retry_attempts"], 2)
        finally:
            os.unlink(config_path)

    def test_tilde_expansion(self):
        """Output directory with ~ should be expanded."""
        config = self.config_yaml.copy()
        config["settings"] = {"output_dir": "~/test_expand"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            parsed = ScraperConfig.from_yaml(config_path)
            self.assertTrue(parsed.settings["output_dir"].startswith("/home/"))
            self.assertIn("test_expand", parsed.settings["output_dir"])
        finally:
            os.unlink(config_path)


class TestParserRegistry(unittest.TestCase):
    """Test that all retailer parsers are registered."""

    def test_all_parsers_present(self):
        expected = {"pbtech", "computerlounge", "mightyape", "1stwave", "paradigmpcs"}
        self.assertEqual(set(PARSERS.keys()), expected)

    def test_parser_types(self):
        self.assertIsInstance(PARSERS["pbtech"], PBtechParser)
        self.assertIsInstance(PARSERS["computerlounge"], ComputerLoungeParser)
        self.assertIsInstance(PARSERS["mightyape"], MightyApeParser)
        self.assertIsInstance(PARSERS["1stwave"], FirstWaveParser)
        self.assertIsInstance(PARSERS["paradigmpcs"], ParadigmPcsParser)

    def test_retailer_names(self):
        self.assertEqual(PARSERS["pbtech"].retailer_name, "pbtech")
        self.assertEqual(PARSERS["computerlounge"].retailer_name, "computerlounge")
        self.assertEqual(PARSERS["mightyape"].retailer_name, "mightyape")
        self.assertEqual(PARSERS["1stwave"].retailer_name, "1stwave")
        self.assertEqual(PARSERS["paradigmpcs"].retailer_name, "paradigmpcs")


# ===========================================================================
# HTML fixture helpers
# ===========================================================================

_SAMPLE_LISTING_HTML = """\
<!DOCTYPE html>
<html>
<head><title>PC Components</title></head>
<body>
<div class="product-item">
    <a href="/product/cpu123">AMD Ryzen 7 7800X3D</a>
    <span class="price">$749.00</span>
    <span class="stock">In Stock</span>
</div>
<div class="product-item">
    <a href="/product/gpu456">NVIDIA RTX 4070 Ti</a>
    <span class="price">$1,499.00</span>
    <span class="stock">In Stock</span>
</div>
<div class="product-item">
    <a href="/product/psu789">Corsair RM850x</a>
    <span class="price">$199.00</span>
    <span class="stock">Out of Stock</span>
</div>
</body>
</html>
"""

_SAMPLE_EMPTY_LISTING = """\
<!DOCTYPE html>
<html>
<head><title>No Results</title></head>
<body>
<p>No products found.</p>
</body>
</html>
"""

_SAMPLE_PRODUCT_PAGE = """\
<!DOCTYPE html>
<html>
<head><title>AMD Ryzen 7 7800X3D - PB Tech</title></head>
<body>
<div class="product-name">AMD Ryzen 7 7800X3D</div>
<span class="our-price">$749.00</span>
<span class="availability">In Stock</span>
</body>
</html>
"""

_SAMPLE_CAPTCHA_PAGE = """\
<!DOCTYPE html>
<html>
<head><title>Just a moment...</title></head>
<body>
<script>document.getElementById('captcha');</script>
<p>Please enable JavaScript to access this site.</p>
</body>
</html>
"""


class TestBaseRetailerParser(unittest.TestCase):
    """Test the generic parser on sample HTML."""

    def setUp(self):
        self.parser = BaseRetailerParser()
        self.parser.retailer_name = "test_retailer"
        self.logger = NZPriceScraper(
            ScraperConfig(), dry_run=True, log_level="ERROR"
        ).logger

    def test_generic_parse_listing_yields_products(self):
        products = self.parser._generic_parse_listing(
            _SAMPLE_LISTING_HTML, "https://example.com", "cpu", self.logger
        )
        self.assertEqual(len(products), 3)

        # Check product names
        names = [p.product_name for p in products]
        self.assertIn("AMD Ryzen 7 7800X3D", names)
        self.assertIn("NVIDIA RTX 4070 Ti", names)
        self.assertIn("Corsair RM850x", names)

        # Check prices
        for p in products:
            self.assertGreater(p.price, 0)
            self.assertEqual(p.currency, "NZD")

    def test_generic_parse_listing_out_of_stock(self):
        products = self.parser._generic_parse_listing(
            _SAMPLE_LISTING_HTML, "https://example.com", "cpu", self.logger
        )
        corsair = [p for p in products if "Corsair" in p.product_name][0]
        self.assertFalse(corsair.in_stock)
        self.assertEqual(corsair.stock_status, "Out of Stock")

    def test_generic_parse_empty_listing(self):
        products = self.parser._generic_parse_listing(
            _SAMPLE_EMPTY_LISTING, "https://example.com", "cpu", self.logger
        )
        self.assertEqual(len(products), 0)

    def test_generic_parse_detail(self):
        product = self.parser._generic_parse_detail(
            _SAMPLE_PRODUCT_PAGE,
            "https://example.com/product/cpu123",
            "cpu",
            self.logger,
        )
        self.assertIsNotNone(product)
        self.assertEqual(product.product_name, "AMD Ryzen 7 7800X3D")
        self.assertEqual(product.price, 749.00)
        self.assertTrue(product.in_stock)


# ===========================================================================
# Integration tests (mocked HTTP)
# ===========================================================================

class TestNZPriceScraperMocked(unittest.TestCase):
    """Test the full scraper pipeline with mocked HTTP requests."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_data = {
            "retailers": {
                "pbtech": {
                    "base_url": "https://www.pbtech.co.nz",
                    "search_path": "/search?q={query}",
                    "components": [
                        {"query": "CPU", "category": "cpu"},
                        {"query": "GPU", "category": "gpu"},
                    ],
                },
                "computerlounge": {
                    "base_url": "https://www.computerlounge.co.nz",
                    "components": [
                        {"url": "/components/cpus", "category": "cpu"},
                    ],
                },
            },
            "settings": {
                "output_dir": self.tmpdir,
                "request_timeout": 5,
                "retry_attempts": 0,
            },
        }
        self.config_path = os.path.join(self.tmpdir, "test_config.yaml")
        with open(self.config_path, "w") as f:
            yaml.dump(self.config_data, f)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("nz_price_scraper.requests.Session.get")
    def test_mocked_scrape(self, mock_get):
        """Test scraper with mock HTTP responses."""
        # Mock HTTP responses for all 3 URLs
        def mock_response(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = _SAMPLE_LISTING_HTML
            mock_resp.raise_for_status.return_value = None
            return mock_resp

        mock_get.side_effect = mock_response

        config = ScraperConfig.from_yaml(self.config_path)
        scraper = NZPriceScraper(config, log_level="ERROR")
        results = scraper.run()

        # Should have 3 products × 3 URLs = 9 products
        # But wait — pbtech has 2 components (CPU, GPU) and computerlounge has 1
        # That's 3 pages × 3 products each = 9
        self.assertEqual(len(results), 9)

        # Verify all retailers present
        retailers = set(p.retailer for p in results)
        self.assertEqual(retailers, {"pbtech", "computerlounge"})

        # Verify all products have valid data
        for p in results:
            self.assertGreater(p.price, 0)
            self.assertTrue(len(p.product_name) > 3)
            self.assertIn(p.category, ("cpu", "gpu"))

        # Verify output file was written
        output_files = list(Path(self.tmpdir).glob("prices_*.jsonl"))
        self.assertEqual(len(output_files), 1)

        # Verify JSONL content
        with open(output_files[0]) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 9)
        for line in lines:
            data = json.loads(line)
            self.assertIn("product_name", data)
            self.assertIn("price", data)
            self.assertIn("retailer", data)
            self.assertIn("timestamp", data)

    @patch("nz_price_scraper.requests.Session.get")
    def test_dry_run_no_http(self, mock_get):
        """Test that --dry-run does not make HTTP requests."""
        config = ScraperConfig.from_yaml(self.config_path)
        scraper = NZPriceScraper(config, dry_run=True, log_level="ERROR")
        results = scraper.run()

        self.assertEqual(len(results), 0)
        mock_get.assert_not_called()

        # No output file in dry run
        output_files = list(Path(self.tmpdir).glob("prices_*.jsonl"))
        self.assertEqual(len(output_files), 0)

    @patch("nz_price_scraper.requests.Session.get")
    def test_404_handling(self, mock_get):
        """Test that 404 responses are handled gracefully."""
        def mock_response(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_resp.raise_for_status.side_effect = (
                __import__("requests").HTTPError("404 Client Error")
            )
            return mock_resp

        mock_get.side_effect = mock_response

        config = ScraperConfig.from_yaml(self.config_path)
        scraper = NZPriceScraper(config, log_level="ERROR")
        results = scraper.run()

        # No products from 404 pages
        self.assertEqual(len(results), 0)

    @patch("nz_price_scraper.requests.Session.get")
    def test_captcha_detection(self, mock_get):
        """Test that CAPTCHA pages are detected and skipped."""
        def mock_response(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = _SAMPLE_CAPTCHA_PAGE
            mock_resp.raise_for_status.return_value = None
            return mock_resp

        mock_get.side_effect = mock_response

        config = ScraperConfig.from_yaml(self.config_path)
        scraper = NZPriceScraper(config, log_level="ERROR")
        results = scraper.run()

        # No products from CAPTCHA-blocked pages
        self.assertEqual(len(results), 0)

    @patch("nz_price_scraper.requests.Session.get")
    def test_retailer_filter(self, mock_get):
        """Test that --retailer flag filters correctly."""
        def mock_response(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = _SAMPLE_LISTING_HTML
            mock_resp.raise_for_status.return_value = None
            return mock_resp

        mock_get.side_effect = mock_response

        config = ScraperConfig.from_yaml(self.config_path)
        scraper = NZPriceScraper(config, log_level="ERROR")
        results = scraper.run(retailer_filter="pbtech")

        # Only pbtech products (2 components × 3 products = 6)
        self.assertEqual(len(results), 6)
        for p in results:
            self.assertEqual(p.retailer, "pbtech")


# ===========================================================================
# CLI argument parsing tests
# ===========================================================================

class TestCLI(unittest.TestCase):
    """Test command-line argument parsing."""

    def test_dry_run_flag(self):
        args = ["--dry-run"]
        parsed = main(args)
        # Should exit 0 (dry run doesn't error)
        self.assertEqual(parsed, 0)

    def test_missing_config(self):
        args = ["--config", "/nonexistent/config.yaml"]
        parsed = main(args)
        self.assertEqual(parsed, 1)

    def test_help(self):
        with self.assertRaises(SystemExit):
            main(["--help"])


# ===========================================================================
# Build session test
# ===========================================================================

class TestBuildSession(unittest.TestCase):
    """Test the HTTP session builder."""

    def test_session_defaults(self):
        session = build_session()
        self.assertIn("User-Agent", session.headers)
        self.assertIn("Accept", session.headers)
        self.assertIn("Accept-Language", session.headers)

    def test_session_custom_ua(self):
        ua = "CustomBot/1.0"
        session = build_session(user_agent=ua)
        self.assertEqual(session.headers["User-Agent"], ua)


# ===========================================================================
# Error handling tests
# ===========================================================================

class TestErrorHandling(unittest.TestCase):
    """Test error reporting in the scraper."""

    @patch("nz_price_scraper.requests.Session.get")
    def test_errors_collected(self, mock_get):
        """Test that errors are collected but execution continues."""
        def mock_response(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = _SAMPLE_LISTING_HTML
            mock_resp.raise_for_status.return_value = None
            return mock_resp

        mock_get.side_effect = mock_response

        config_data = {
            "retailers": {
                "pbtech": {
                    "base_url": "https://www.pbtech.co.nz",
                    "search_path": "/search?q={query}",
                    "components": [
                        {"query": "CPU", "category": "cpu"},
                    ],
                },
            },
            "settings": {
                "output_dir": tempfile.mkdtemp(),
                "request_timeout": 5,
                "retry_attempts": 0,
            },
        }
        config = ScraperConfig()
        config.retailers = config_data["retailers"]
        config.settings.update(config_data["settings"])

        scraper = NZPriceScraper(config, log_level="ERROR")
        results = scraper.run()
        self.assertGreater(len(results), 0)

    def test_invalid_config_yields_error(self):
        """Missing config file returns exit code 1."""
        exit_code = main(["--config", "/tmp/nonexistent_scraper_test_config.yaml"])
        self.assertEqual(exit_code, 1)


# ===========================================================================
# Main
# ===========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)