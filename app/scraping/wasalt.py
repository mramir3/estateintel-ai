"""Wasalt Real Estate public data scraper and parser."""
import re
import json
import time
import urllib.request
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.api.schemas import PropertyItem
from app.scraping.parser import clean_text, compute_content_hash, normalize_price, normalize_number
from app.utils.logging import logger
from app.utils.validators import is_safe_url

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 EstateIntel/1.0"

class WasaltScraper:
    """Scrapes verified public property listings from Wasalt."""
    
    BASE_URL = "https://wasalt.sa"
    SITEMAP_URL = "https://cdn.wasalt.sa/sitemap/product_sitemap_en_sa.xml.gz"

    def __init__(self, request_delay: float = 0.5):
        self.request_delay = request_delay

    def get_property_urls(self, limit: int = 40) -> List[str]:
        """Discovers real property URLs from Wasalt sitemap."""
        urls = []
        try:
            req = urllib.request.Request(self.SITEMAP_URL, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read()
                # Check if gzipped or plain XML
                try:
                    import gzip
                    text = gzip.decompress(content).decode("utf-8", errors="ignore")
                except Exception:
                    text = content.decode("utf-8", errors="ignore")
                
                matches = re.findall(r"<loc>(https://wasalt\.sa/en/property/sale/[^<]+)</loc>", text)
                urls = matches[:limit]
                logger.info(f"Discovered {len(urls)} Wasalt listing URLs from sitemap")
        except Exception as e:
            logger.error(f"Failed to fetch Wasalt sitemap: {e}")
            # Fallback to direct representative sample URLs
            urls = [
                "https://wasalt.sa/en/property/sale/villa-333-sqm-facing-east-on-20m-width-street-5841671",
                "https://wasalt.sa/en/property/sale/villa-333-sqm-facing-east-on-20m-width-street-5841670",
                "https://wasalt.sa/en/property/sale/villa-333-sqm-facing-east-on-20m-width-street-5841669",
                "https://wasalt.sa/en/property/sale/villa-333-sqm-facing-east-on-20m-width-street-5841668",
                "https://wasalt.sa/en/property/sale/villa-333-sqm-facing-east-on-20m-width-street-5841667",
            ]
        return urls

    def parse_property_page(self, url: str) -> Optional[PropertyItem]:
        """Fetches and parses a single Wasalt listing page into a PropertyItem."""
        if not is_safe_url(url):
            logger.warning(f"Skipping unsafe URL: {url}")
            return None

        req = urllib.request.Request(
            url, 
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml",
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                html_content = resp.read().decode("utf-8", errors="ignore")
                
            # Extract Next.js data script
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_content)
            if not match:
                logger.warning(f"No __NEXT_DATA__ found for Wasalt property: {url}")
                return None
                
            data = json.loads(match.group(1))
            page_props = data.get("props", {}).get("pageProps", {})
            v3 = page_props.get("propertyDetailsV3", {})
            if not v3:
                return None

            pinfo = v3.get("propertyInfo", {})
            raw_id = str(v3.get("id") or pinfo.get("id") or url.split("-")[-1])
            prop_id = f"wasalt-{raw_id}"

            title = clean_text(pinfo.get("title") or pinfo.get("propertyName") or "Wasalt Property")
            description = clean_text(pinfo.get("description") or "")
            
            city = pinfo.get("city") or "Saudi Arabia"
            district = pinfo.get("district") or ""
            territory = pinfo.get("territory") or ""
            location_parts = [p for p in [district, territory, city, "Saudi Arabia"] if p]
            location = ", ".join(location_parts)

            property_type = pinfo.get("propertySubType") or pinfo.get("propertyMainType") or "Residential"
            
            raw_price = pinfo.get("salePrice") or pinfo.get("conversionPrice")
            price, currency = normalize_price(raw_price, default_currency=pinfo.get("currencyType") or "SAR")
            
            # Extract attributes (bedrooms, bathrooms, area)
            bedrooms = None
            bathrooms = None
            area_str = None
            amenities = []

            for attr in v3.get("attributes", []):
                key = (attr.get("key") or "").lower()
                name = attr.get("name") or ""
                val = attr.get("value")
                if "bedroom" in key or "bedroom" in name.lower():
                    bedrooms = normalize_number(val)
                elif "bathroom" in key or "bathroom" in name.lower():
                    bathrooms = normalize_number(val)
                elif "area" in key or "carpet" in key:
                    unit = attr.get("unit", "SQM")
                    area_str = f"{val} {unit}"
                else:
                    amenities.append(f"{name}: {val}" if val else name)

            # Check additional amenities from infoDetails
            info_details = page_props.get("infoDetails", {})
            for am in info_details.get("amenities", []):
                if isinstance(am, str):
                    amenities.append(am)
                elif isinstance(am, dict) and am.get("name"):
                    amenities.append(am["name"])

            hash_content = f"{title} {location} {price} {bedrooms} {area_str}"
            content_hash = compute_content_hash(hash_content)

            item = PropertyItem(
                id=prop_id,
                source="Wasalt",
                title=title,
                description=description,
                location=location,
                city=city,
                country="Saudi Arabia",
                property_type=property_type,
                price=price,
                currency=currency,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                area=area_str,
                amenities=amenities,
                source_url=url,
                scraped_at=datetime.now(timezone.utc).isoformat(),
                content_hash=content_hash,
                metadata={
                    "dar_reference": v3.get("darReference"),
                    "rega_license": v3.get("propertyOwner", {}).get("regaAdvLicNo"),
                    "is_verified": v3.get("isVerified", True),
                    "coordinates": v3.get("location"),
                    "status": pinfo.get("statusTypeSlug", "active"),
                }
            )
            return item
        except Exception as e:
            logger.error(f"Error parsing Wasalt listing {url}: {e}")
            return None

    def scrape_all(self, limit: int = 30) -> List[PropertyItem]:
        """Scrapes multiple listings up to limit with rate limiting."""
        urls = self.get_property_urls(limit=limit)
        items = []
        for i, url in enumerate(urls):
            logger.info(f"Scraping Wasalt [{i+1}/{len(urls)}]: {url}")
            item = self.parse_property_page(url)
            if item:
                items.append(item)
            time.sleep(self.request_delay)
        logger.info(f"Successfully scraped {len(items)} Wasalt properties")
        return items
