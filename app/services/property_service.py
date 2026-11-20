"""Deterministic property search, structured filtering, and data access service."""
import json
from typing import List, Optional, Dict, Any
from app.api.schemas import PropertyItem, PropertyFilter
from app.config import settings
from app.utils.logging import logger

class PropertyService:
    """Provides fast deterministic filtering and retrieval for normalized property data."""

    def __init__(self):
        self._cache: Optional[List[PropertyItem]] = None

    def get_all_properties(self, force_reload: bool = False) -> List[PropertyItem]:
        """Loads and returns all normalized properties from disk."""
        if self._cache is not None and not force_reload:
            return self._cache

        filepath = settings.PROCESSED_DATA_DIR / "properties.json"
        if not filepath.exists():
            logger.warning(f"Properties file not found at {filepath}")
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                items = [PropertyItem(**d) for d in data]
                self._cache = items
                return items
        except Exception as e:
            logger.error(f"Failed to load properties from {filepath}: {e}")
            return []

    def filter_properties(self, f: PropertyFilter) -> List[PropertyItem]:
        """Applies deterministic metadata and numerical filtering (price, bedrooms, location)."""
        properties = self.get_all_properties()
        results = []

        for p in properties:
            # 1. Source filter
            if f.source and f.source.lower() not in p.source.lower():
                continue

            # 2. City / Location filter
            if f.city:
                city_needle = f.city.strip().lower()
                prop_city = (p.city or "").lower()
                prop_loc = (p.location or "").lower()
                if city_needle not in prop_city and city_needle not in prop_loc:
                    continue

            # 3. Property Type filter
            if f.property_type:
                type_needle = f.property_type.strip().lower()
                prop_type = (p.property_type or "").lower()
                if type_needle not in prop_type:
                    continue

            # 4. Numeric Price filters
            if f.min_price is not None:
                if p.price is None or p.price < f.min_price:
                    continue
            if f.max_price is not None:
                if p.price is None or p.price > f.max_price:
                    continue

            # 5. Bedrooms filter
            if f.min_bedrooms is not None:
                if p.bedrooms is None or p.bedrooms < f.min_bedrooms:
                    continue

            # 6. Keyword Search Query
            if f.search_query:
                query = f.search_query.lower()
                searchable_text = f"{p.title} {p.description or ''} {p.location or ''} {' '.join(p.amenities)}".lower()
                if query not in searchable_text:
                    continue

            results.append(p)
            if len(results) >= f.limit:
                break

        return results

    def get_sources_overview(self) -> Dict[str, Any]:
        """Compiles aggregated distribution metrics across sources."""
        items = self.get_all_properties()
        dg_count = sum(1 for p in items if p.source == "DarGlobal")
        wasalt_count = sum(1 for p in items if p.source == "Wasalt")
        
        cities = {}
        for p in items:
            c = p.city or "Unknown"
            cities[c] = cities.get(c, 0) + 1

        types = {}
        for p in items:
            t = p.property_type or "Unknown"
            types[t] = types.get(t, 0) + 1

        return {
            "total_properties": len(items),
            "sources": {
                "DarGlobal": {
                    "count": dg_count,
                    "description": "Luxury global master developments, branded residences, and prime European/Middle Eastern real estate.",
                    "primary_markets": ["Dubai", "Riyadh", "London", "Muscat", "Marbella", "Doha"],
                    "brand_partners": ["Aston Martin", "Lamborghini", "Trump Organization", "Pagani", "Missoni", "Mouawad", "Gensler"]
                },
                "Wasalt": {
                    "count": wasalt_count,
                    "description": "Licensed proptech portal with verified residential & commercial properties across Saudi Arabia.",
                    "primary_markets": ["Riyadh", "Jeddah", "Dammam", "Al-Khobar"],
                    "regulatory_compliance": "REGA (Real Estate General Authority) verified"
                }
            },
            "cities_distribution": cities,
            "property_types_distribution": types,
        }

property_service = PropertyService()
