"""HTML parsing and text normalization utilities."""
import re
import html
import hashlib
from typing import Optional, Tuple

def clean_text(raw_text: Optional[str]) -> str:
    """Strips HTML tags, decodes entities, and normalizes whitespace."""
    if not raw_text:
        return ""
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", raw_text)
    # Unescape HTML entities (&amp;, &nbsp;, etc.)
    text = html.unescape(text)
    # Normalize multiple whitespaces and newlines
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def compute_content_hash(text: str) -> str:
    """Generates deterministic SHA-256 hash for deduplication."""
    normalized = re.sub(r"\s+", "", (text or "").lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def normalize_price(val: Optional[any], default_currency: str = "SAR") -> Tuple[Optional[float], Optional[str]]:
    """Converts price strings/numbers to a clean float and standard currency."""
    if val is None or val == "":
        return None, None
    try:
        if isinstance(val, (int, float)):
            return float(val), default_currency
        # String cleanup (e.g., '1,600,000 SAR' -> 1600000.0, 'SAR')
        val_str = str(val).replace(",", "").strip()
        # Find currency if embedded
        cur_match = re.search(r"(SAR|AED|GBP|USD|EUR|OMR|QAR)", val_str, re.IGNORECASE)
        cur = cur_match.group(1).upper() if cur_match else default_currency
        
        num_match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
        if num_match:
            return float(num_match.group(0)), cur
        return None, cur
    except Exception:
        return None, None

def normalize_number(val: Optional[any]) -> Optional[int]:
    """Extracts integer value from count fields (bedrooms, bathrooms)."""
    if val is None or val == "":
        return None
    try:
        if isinstance(val, int):
            return val
        if isinstance(val, float):
            return int(val)
        match = re.search(r"\d+", str(val))
        return int(match.group(0)) if match else None
    except Exception:
        return None
