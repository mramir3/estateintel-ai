"""Tests for scraping, HTML parsing, safeguards, and schema normalization."""
import pytest
from app.scraping.parser import clean_text, compute_content_hash, normalize_price, normalize_number
from app.scraping.darglobal import DarGlobalScraper
from app.scraping.wasalt import WasaltScraper
from app.utils.validators import is_safe_url

def test_clean_text():
    html_input = "<p>Luxury <b>Villa</b> with &amp; private garden.&nbsp;</p>"
    expected = "Luxury Villa with & private garden."
    assert clean_text(html_input) == expected

def test_compute_content_hash():
    h1 = compute_content_hash("Villa Riyadh 1,000,000 SAR")
    h2 = compute_content_hash("Villa   Riyadh   1,000,000 SAR  ")
    assert h1 == h2
    assert len(h1) == 64

def test_normalize_price():
    val, cur = normalize_price("1,600,000 SAR")
    assert val == 1600000.0
    assert cur == "SAR"

    val_eur, cur_eur = normalize_price(4500000.0, default_currency="EUR")
    assert val_eur == 4500000.0
    assert cur_eur == "EUR"

    val_none, cur_none = normalize_price(None)
    assert val_none is None

def test_normalize_number():
    assert normalize_number(5) == 5
    assert normalize_number("4 Bedrooms") == 4
    assert normalize_number(None) is None

def test_url_allowlisting_and_ssrf():
    assert is_safe_url("https://darglobal.co.uk/projects") is True
    assert is_safe_url("https://wasalt.sa/en/property/sale/123") is True
    assert is_safe_url("https://cdn.wasalt.sa/sitemap/test.xml") is True
    # Dangerous URLs blocked
    assert is_safe_url("http://127.0.0.1:8000/secret") is False
    assert is_safe_url("http://localhost:8080/admin") is False
    assert is_safe_url("http://169.254.169.254/latest/meta-data") is False
    assert is_safe_url("https://malicious-phishing.com/steal") is False

def test_darglobal_waf_detection_and_safeguards():
    scraper = DarGlobalScraper()
    accessible, reason = scraper.check_access_restrictions()
    assert isinstance(accessible, bool)
    assert isinstance(reason, str)
    # The verified public data should always yield valid items
    items = scraper.scrape_all()
    assert len(items) >= 10
    for item in items:
        assert item.source == "DarGlobal"
        assert item.id.startswith("darglobal-")
        assert len(item.title) > 3
        assert item.source_url.startswith("http")

def test_wasalt_scraper_schema():
    scraper = WasaltScraper()
    # Test sample item extraction
    urls = scraper.get_property_urls(limit=3)
    assert len(urls) > 0
    item = scraper.parse_property_page(urls[0])
    if item:
        assert item.source == "Wasalt"
        assert item.id.startswith("wasalt-")
        assert item.country == "Saudi Arabia"
        assert len(item.content_hash) == 64
