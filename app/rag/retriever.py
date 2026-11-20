"""Hybrid retrieval combining semantic vector search and deterministic metadata filtering."""
import re
from typing import List, Tuple, Optional, Dict, Any
from app.api.schemas import PropertyItem, SourceCitation, PropertyFilter
from app.rag.vector_store import vector_store
from app.services.property_service import property_service
from app.config import settings
from app.utils.logging import logger

class HybridRetriever:
    """Combines dense semantic vector retrieval with deterministic parameter extraction."""

    def __init__(self, top_k: int = settings.TOP_K_RESULTS):
        self.top_k = top_k

    def _extract_filter_intent(self, query: str) -> PropertyFilter:
        """Parses natural language query for numeric and categorical constraints."""
        f = PropertyFilter(limit=self.top_k)
        q_lower = query.lower()

        # Source detection
        if "darglobal" in q_lower or "dar global" in q_lower:
            f.source = "DarGlobal"
        elif "wasalt" in q_lower:
            f.source = "Wasalt"

        # City / Region detection
        for city in ["riyadh", "jeddah", "dubai", "london", "muscat", "marbella", "doha", "ras al khaimah", "dammam", "khobar"]:
            if city in q_lower:
                f.city = city
                break

        # Property Type
        for ptype in ["villa", "apartment", "mansion", "penthouse", "tower"]:
            if ptype in q_lower:
                f.property_type = ptype
                break

        # Price constraints (e.g., 'under 2,000,000', 'under 1 million', 'less than 3m')
        under_match = re.search(r"(?:under|below|less than|max(?:imum)?)\s*(?:sar|aed|gbp|usd|\$)?\s*([\d,\.]+)\s*(m|million|k)?", q_lower)
        if under_match:
            try:
                num_str = under_match.group(1).replace(",", "")
                val = float(num_str)
                mult = (under_match.group(2) or "").lower()
                if mult in ("m", "million"):
                    val *= 1_000_000
                elif mult == "k":
                    val *= 1_000
                f.max_price = val
            except Exception:
                pass

        # Bedrooms constraint (e.g. '3 bedroom', '4 beds')
        bed_match = re.search(r"(\d+)\s*(?:bed|bedroom|br)", q_lower)
        if bed_match:
            try:
                f.min_bedrooms = int(bed_match.group(1))
            except Exception:
                pass

        return f

    def retrieve(
        self, 
        query: str, 
        top_k: Optional[int] = None, 
        explicit_filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[PropertyItem], List[SourceCitation], str]:
        """Performs hybrid retrieval returning properties, citations, and assembled context."""
        k = top_k or self.top_k
        extracted_filter = self._extract_filter_intent(query)
        
        # Override with explicit filters if provided
        if explicit_filters:
            if "source" in explicit_filters:
                extracted_filter.source = explicit_filters["source"]
            if "city" in explicit_filters:
                extracted_filter.city = explicit_filters["city"]
            if "max_price" in explicit_filters:
                extracted_filter.max_price = float(explicit_filters["max_price"])

        # 1. Semantic Vector Search
        source_filter = extracted_filter.source if extracted_filter.source else None
        vector_results = vector_store.similarity_search(query, top_k=k, source_filter=source_filter)
        
        # 2. Deterministic Structured Search if price/city/bedroom filter is active
        deterministic_results: List[PropertyItem] = []
        if extracted_filter.max_price or extracted_filter.min_bedrooms or extracted_filter.city:
            deterministic_results = property_service.filter_properties(extracted_filter)

        # Merge results, prioritizing structured matches while preserving semantic scores
        merged_properties: List[PropertyItem] = []
        seen_ids = set()
        citations: List[SourceCitation] = []

        # Add deterministic matches first if specific numeric query was asked
        for p in deterministic_results[:k]:
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                merged_properties.append(p)
                citations.append(SourceCitation(
                    id=p.id,
                    title=p.title,
                    source=p.source,
                    source_url=p.source_url,
                    location=p.location,
                    price=p.price,
                    currency=p.currency,
                    relevance_score=0.98
                ))

        # Fill remaining with vector results
        for p, score in vector_results:
            if p.id not in seen_ids and len(merged_properties) < k:
                seen_ids.add(p.id)
                merged_properties.append(p)
                citations.append(SourceCitation(
                    id=p.id,
                    title=p.title,
                    source=p.source,
                    source_url=p.source_url,
                    location=p.location,
                    price=p.price,
                    currency=p.currency,
                    relevance_score=round(score, 3)
                ))

        # Format context for LLM prompt
        if not merged_properties:
            context_text = "No matching real estate developments or listings were found matching the criteria."
        else:
            context_blocks = []
            for i, p in enumerate(merged_properties, 1):
                block = [
                    f"--- PROPERTY {i} ---",
                    f"Title: {p.title}",
                    f"Source: {p.source}",
                    f"Type: {p.property_type or 'Unknown'}",
                    f"Location: {p.location or 'Unknown'}",
                    f"Price: {p.price:,.0f} {p.currency}" if p.price else "Price: Price on Application / Disclosed in Filings",
                ]
                if p.bedrooms:
                    block.append(f"Bedrooms: {p.bedrooms}")
                if p.area:
                    block.append(f"Area: {p.area}")
                if p.amenities:
                    block.append(f"Amenities: {', '.join(p.amenities)}")
                if p.description:
                    block.append(f"Description: {p.description}")
                if p.source_url:
                    block.append(f"Verified URL: {p.source_url}")
                context_blocks.append("\n".join(block))
            context_text = "\n\n".join(context_blocks)

        return merged_properties, citations, context_text

retriever = HybridRetriever()
