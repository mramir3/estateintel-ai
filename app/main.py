"""Main FastAPI Application Entrypoint for EstateIntel AI."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.routes import router as api_router
from app.rag.vector_store import vector_store
from app.services.property_service import property_service
from app.utils.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown handler."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    # Verify index readiness
    count = vector_store.count()
    if count == 0:
        logger.info("Vector store is empty on startup. Checking processed properties...")
        props = property_service.get_all_properties()
        if props:
            logger.info(f"Found {len(props)} properties. Populating vector index...")
            vector_store.index_properties(props)
        else:
            logger.warning("No pre-indexed properties found. Run scripts/ingest.py to collect real data.")
    else:
        logger.info(f"Vector store ready with {count} indexed properties.")
    yield
    logger.info("Shutting down EstateIntel AI...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent Real Estate Assistant for DarGlobal Developments & Wasalt Marketplace",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/", tags=["General"])
def root():
    return {
        "name": settings.PROJECT_NAME,
        "description": settings.PROJECT_DESCRIPTION,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "online",
        "documentation": "/docs",
        "endpoints": {
            "health": "/health",
            "stats": "/api/stats",
            "sources": "/api/sources",
            "properties": "/api/properties",
            "chat": "/api/chat"
        }
    }

# Health endpoint at root for standard Docker/cloud healthcheck
@app.get("/health", tags=["General"])
def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "vector_store_documents": vector_store.count(),
    }

# Include API router
app.include_router(api_router, prefix=settings.API_PREFIX)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main.py:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=True)
