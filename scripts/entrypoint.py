"""Container unified entrypoint for EstateIntel AI.

Coordinates:
1. Pre-flight data index verification
2. FastAPI backend startup on port 8000
3. Streamlit frontend startup on configured public PORT (default 8501)
4. Process health monitoring and signal handling
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.rag.vector_store import vector_store
from app.services.property_service import property_service
from app.scraping.darglobal import DarGlobalScraper
from app.utils.logging import logger

def ensure_data_ready():
    """Ensures property records and vector index are populated prior to serving."""
    logger.info("Verifying data index readiness...")
    count = vector_store.count()
    if count == 0:
        logger.info("Vector index empty. Loading and indexing verified properties...")
        props = property_service.get_all_properties()
        if not props:
            logger.info("Harvesting DarGlobal verified developments...")
            props = DarGlobalScraper().scrape_all()
        indexed = vector_store.index_properties(props)
        logger.info(f"Successfully initialized vector index with {indexed} documents.")
    else:
        logger.info(f"Vector store already contains {count} indexed properties.")

def main():
    logger.info("==================================================")
    logger.info("   EstateIntel AI — Unified Production Runner")
    logger.info("==================================================")
    
    ensure_data_ready()

    # Determine ports
    backend_port = int(os.getenv("BACKEND_PORT", "8000"))
    # In cloud environments like Render/Railway/HF, PORT is the public port
    public_port = int(os.getenv("STREAMLIT_PORT", os.getenv("PORT", "8501")))

    # Safeguard against port collision: ensure FastAPI and Streamlit don't collide
    if backend_port == public_port:
        if backend_port == 8000:
            public_port = 8501
            logger.info(f"Port collision detected (both 8000). Automatically assigned Streamlit to port {public_port}.")
        else:
            backend_port = 8000 if public_port != 8000 else 8001
            logger.info(f"Port collision detected. Automatically assigned FastAPI backend to port {backend_port}.")

    # Start FastAPI backend in background
    logger.info(f"Starting FastAPI backend on 0.0.0.0:{backend_port}...")
    backend_cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", str(backend_port),
        "--log-level", "info"
    ]
    backend_proc = subprocess.Popen(backend_cmd)

    # Allow backend 2 seconds to initialize
    time.sleep(2)

    # Start Streamlit frontend on public port
    logger.info(f"Starting Streamlit frontend on 0.0.0.0:{public_port}...")
    streamlit_cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(ROOT_DIR / "frontend" / "streamlit_app.py"),
        "--server.port", str(public_port),
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
        "--theme.base", "light"
    ]
    frontend_proc = subprocess.Popen(streamlit_cmd)

    def shutdown(sig, frame):
        logger.info("Shutting down processes...")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Monitor processes
    while True:
        b_ret = backend_proc.poll()
        f_ret = frontend_proc.poll()
        if b_ret is not None:
            logger.error(f"Backend process exited with code {b_ret}")
            frontend_proc.terminate()
            sys.exit(b_ret)
        if f_ret is not None:
            logger.error(f"Frontend process exited with code {f_ret}")
            backend_proc.terminate()
            sys.exit(f_ret)
        time.sleep(1)

if __name__ == "__main__":
    main()
