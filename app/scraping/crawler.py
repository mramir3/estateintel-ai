"""Unified data crawler and ingestion coordinator for DarGlobal and Wasalt."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple
from app.api.schemas import PropertyItem, IngestionStats
from app.scraping.darglobal import DarGlobalScraper
from app.scraping.wasalt import WasaltScraper
from app.config import settings
from app.utils.logging import logger

class UnifiedCrawler:
    """Manages the full data collection, deduplication, and normalization pipeline."""

    def __init__(self):
        self.darglobal_scraper = DarGlobalScraper()
        self.wasalt_scraper = WasaltScraper()
        
        # Ensure directories exist
        settings.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        settings.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def run_crawl(self, wasalt_limit: int = 35) -> Tuple[List[PropertyItem], IngestionStats]:
        """Executes full crawl across both platforms and saves normalized outputs."""
        logger.info("Starting unified property ingestion pipeline...")
        
        # Track statistics
        pages_attempted = 0
        pages_succeeded = 0
        pages_blocked = 0
        duplicates_detected = 0

        # 1. DarGlobal Ingestion
        pages_attempted += 1  # Probe primary site
        accessible, reason = self.darglobal_scraper.check_access_restrictions()
        if not accessible:
            pages_blocked += 1
            logger.info(f"DarGlobal primary site blocked by WAF ({reason}). Ingesting official public filings.")
        else:
            pages_succeeded += 1

        darglobal_items = self.darglobal_scraper.scrape_all()
        pages_succeeded += len(darglobal_items)

        # 2. Wasalt Ingestion
        wasalt_urls = self.wasalt_scraper.get_property_urls(limit=wasalt_limit)
        pages_attempted += len(wasalt_urls) + 1  # +1 for sitemap

        wasalt_items = []
        for url in wasalt_urls:
            item = self.wasalt_scraper.parse_property_page(url)
            if item:
                wasalt_items.append(item)
                pages_succeeded += 1
            else:
                pages_blocked += 1

        # Save raw JSON files
        raw_dg_path = settings.RAW_DATA_DIR / "darglobal_raw.json"
        raw_wasalt_path = settings.RAW_DATA_DIR / "wasalt_raw.json"
        
        with open(raw_dg_path, "w", encoding="utf-8") as f:
            json.dump([item.model_dump() for item in darglobal_items], f, indent=2, ensure_ascii=False)
            
        with open(raw_wasalt_path, "w", encoding="utf-8") as f:
            json.dump([item.model_dump() for item in wasalt_items], f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved raw data to {raw_dg_path} and {raw_wasalt_path}")

        # 3. Deduplication & Consolidation
        all_items: List[PropertyItem] = []
        seen_hashes = set()
        seen_ids = set()

        for item in (darglobal_items + wasalt_items):
            if item.id in seen_ids or item.content_hash in seen_hashes:
                duplicates_detected += 1
                logger.info(f"Duplicate detected and filtered: {item.id} - {item.title}")
                continue
            seen_ids.add(item.id)
            seen_hashes.add(item.content_hash)
            all_items.append(item)

        # 4. Save normalized dataset
        processed_path = settings.PROCESSED_DATA_DIR / "properties.json"
        with open(processed_path, "w", encoding="utf-8") as f:
            json.dump([item.model_dump() for item in all_items], f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(all_items)} normalized properties to {processed_path}")

        # 5. Ingestion Stats
        now_str = datetime.now(timezone.utc).isoformat()
        stats = IngestionStats(
            pages_attempted=pages_attempted,
            pages_succeeded=pages_succeeded,
            pages_blocked=pages_blocked,
            records_darglobal=len(darglobal_items),
            records_wasalt=len(wasalt_items),
            total_documents_indexed=len(all_items),
            duplicates_detected=duplicates_detected,
            last_ingestion_time=now_str,
            vector_store_status="Ready"
        )

        stats_path = settings.PROCESSED_DATA_DIR / "ingestion_stats.json"
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats.model_dump(), f, indent=2)

        return all_items, stats
