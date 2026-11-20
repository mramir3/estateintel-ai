"""Command-line ingestion script for scraping and indexing DarGlobal & Wasalt properties."""
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.scraping.crawler import UnifiedCrawler
from app.rag.vector_store import vector_store
from app.utils.logging import logger

def run_ingestion(wasalt_limit: int = 35):
    """Executes crawl, normalizes data, and indexes into vector store."""
    logger.info("==================================================")
    logger.info("   EstateIntel AI - Real Estate Ingestion Pipeline")
    logger.info("==================================================")
    
    crawler = UnifiedCrawler()
    properties, stats = crawler.run_crawl(wasalt_limit=wasalt_limit)
    
    logger.info("\n--- Ingestion Summary ---")
    logger.info(f"Pages attempted:            {stats.pages_attempted}")
    logger.info(f"Pages successfully fetched: {stats.pages_succeeded}")
    logger.info(f"Pages blocked / restricted: {stats.pages_blocked}")
    logger.info(f"DarGlobal developments:     {stats.records_darglobal}")
    logger.info(f"Wasalt listings:            {stats.records_wasalt}")
    logger.info(f"Duplicates filtered:        {stats.duplicates_detected}")
    logger.info(f"Total unified properties:   {len(properties)}")
    logger.info(f"Last ingestion timestamp:   {stats.last_ingestion_time}")

    logger.info("\nIndexing properties into vector store...")
    indexed_count = vector_store.index_properties(properties)
    logger.info(f"Successfully indexed {indexed_count} documents into vector store!")
    logger.info("==================================================")

if __name__ == "__main__":
    limit = 35
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass
    run_ingestion(wasalt_limit=limit)
