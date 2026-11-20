"""Security, URL allowlisting, SSRF prevention, and input validation."""
import re
from urllib.parse import urlparse
import ipaddress
from app.utils.logging import logger

# Allowed domains for scraping/crawling
ALLOWED_DOMAINS = {
    "darglobal.co.uk",
    "www.darglobal.co.uk",
    "wasalt.sa",
    "www.wasalt.sa",
    "cdn.wasalt.sa",
    "londonstockexchange.com",
    "www.londonstockexchange.com",
    "openrouter.ai",
}

# Prompt injection signatures to neutralize
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions",
    r"you\s+are\s+now\s+(an?|a\s+new)\s+",
    r"system\s*prompt\s*override",
    r"reveal\s+(your|the)\s+(system\s+prompt|secret|api\s*key)",
    r"drop\s+database",
    r"<script.*?>.*?</script>",
]

def is_safe_url(url: str) -> bool:
    """Validates URL against allowlist and blocks SSRF/internal addresses."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            logger.warning(f"Blocked unsafe URL scheme: {parsed.scheme}")
            return False
            
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return False
            
        # Check against SSRF / private IP
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                logger.warning(f"Blocked SSRF attempt to IP: {hostname}")
                return False
        except ValueError:
            # Not an IP literal, standard hostname
            if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "internal", "local"):
                logger.warning(f"Blocked localhost attempt: {hostname}")
                return False

        # Match against allowlist
        for domain in ALLOWED_DOMAINS:
            if hostname == domain or hostname.endswith("." + domain):
                return True
                
        logger.warning(f"URL domain not in allowlist: {hostname}")
        return False
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return False

def sanitize_user_input(text: str, max_length: int = 1500) -> str:
    """Cleans, validates, and truncates user queries."""
    if not text:
        return ""
    # Strip dangerous HTML/scripts
    cleaned = re.sub(r"<[^>]*>", "", text)
    cleaned = cleaned.strip()
    return cleaned[:max_length]

def check_prompt_injection(text: str) -> bool:
    """Detects potential prompt injection attempts in input queries."""
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False

def mask_secret(secret: str, visible_chars: int = 4) -> str:
    """Masks secret keys for safe logging and status reporting."""
    if not secret:
        return "<not-set>"
    if len(secret) <= visible_chars * 2:
        return "***"
    return f"{secret[:visible_chars]}...{secret[-visible_chars:]}"
