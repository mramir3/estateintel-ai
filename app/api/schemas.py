"""Pydantic data models and schemas for EstateIntel AI API."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PropertyItem(BaseModel):
    """Normalized real estate property schema across all sources."""
    id: str
    source: str = Field(..., description="Source platform: 'DarGlobal' or 'Wasalt'")
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    property_type: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area: Optional[str] = None
    amenities: List[str] = Field(default_factory=list)
    source_url: str
    scraped_at: str
    content_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PropertyFilter(BaseModel):
    """Filter parameters for property searches."""
    source: Optional[str] = None
    city: Optional[str] = None
    property_type: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_bedrooms: Optional[int] = None
    search_query: Optional[str] = None
    limit: int = 50

class SourceCitation(BaseModel):
    """Grounded reference citation for generated responses."""
    id: str
    title: str
    source: str
    source_url: str
    location: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    relevance_score: Optional[float] = None

class ChatRequest(BaseModel):
    """Incoming user chat query."""
    message: str = Field(..., min_length=1, max_length=1500, description="User question")
    conversation_id: Optional[str] = Field(None, description="Client conversation tracking ID")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional structured metadata filters")

class ChatResponse(BaseModel):
    """Standardized AI assistant response."""
    answer: str
    conversation_id: str
    model: str
    sources: List[SourceCitation] = Field(default_factory=list)
    retrieved_count: int = 0
    status: str = "success"
    error: Optional[str] = None

class IngestionStats(BaseModel):
    """Verified data collection and indexing metrics."""
    pages_attempted: int
    pages_succeeded: int
    pages_blocked: int
    records_darglobal: int
    records_wasalt: int
    total_documents_indexed: int
    duplicates_detected: int
    last_ingestion_time: str
    vector_store_status: str

class HealthResponse(BaseModel):
    """System health and readiness verification."""
    status: str
    version: str
    environment: str
    openrouter_configured: bool
    vector_store_ready: bool
    total_documents: int
