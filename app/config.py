"""Configuration settings for EstateIntel AI."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # App Information
    PROJECT_NAME: str = "EstateIntel AI"
    PROJECT_DESCRIPTION: str = "DarGlobal & Wasalt Intelligent Real Estate Assistant"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    
    # OpenRouter LLM Settings
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    # Default to openrouter/free or verified free model
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openrouter/free")
    FALLBACK_MODELS: list = [
        "nvidia/nemotron-3.5-lightning:free",
        "recursive/flint-v1.0:free",
        "google/gemma-4-31b-it:free",
        "liquid/lfm-3-1.7b:free",
    ]
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.2"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1024"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "12"))
    
    # RAG & ChromaDB Settings
    CHROMA_DIR: Path = BASE_DIR / "data" / "chroma_db"
    RAW_DATA_DIR: Path = BASE_DIR / "data" / "raw"
    PROCESSED_DATA_DIR: Path = BASE_DIR / "data" / "processed"
    COLLECTION_NAME: str = "estateintel_properties"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
    
    # Server Settings
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8000")))
    API_PREFIX: str = "/api"
    
    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }

settings = Settings()
