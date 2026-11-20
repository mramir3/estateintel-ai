# EstateIntel AI — DarGlobal & Wasalt Intelligent Real Estate Assistant

> **Submission for Junior AI Engineer – Applied AI Technical Assessment**  
> **Candidate:** Amir Ansary (`ansaryamir7@gmail.com`)  
> **Company:** DarGlobal PLC   
> **Live Deployed URL:** [https://estateintel-ai.onrender.com](https://estateintel-ai.onrender.com)  
> **GitHub Repository:** [https://github.com/mramir3/estateintel-ai](https://github.com/mramir3/estateintel-ai)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-estateintel--ai.onrender.com-success?style=for-the-badge&logo=render)](https://estateintel-ai.onrender.com)
[![GitHub](https://img.shields.io/badge/GitHub-mramir3%2Festateintel--ai-181717?style=for-the-badge&logo=github)](https://github.com/mramir3/estateintel-ai)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-38%2F38%20Passing-brightgreen?style=for-the-badge)](TEST_REPORT.md)

---

## 🌟 Quick Links for Recruiters & Evaluators

| Resource | Direct Link | Purpose |
| :--- | :--- | :--- |
| **Live Interactive Chatbot** | 🔗 [https://estateintel-ai.onrender.com](https://estateintel-ai.onrender.com) | Direct web interface to test natural language queries |
| **FastAPI Swagger Docs** | 📖 [https://estateintel-ai.onrender.com/docs](https://estateintel-ai.onrender.com/docs) | Interactive API exploration and OpenAPI schemas |
| **Healthcheck Endpoint** | 🩺 [https://estateintel-ai.onrender.com/health](https://estateintel-ai.onrender.com/health) | Live container health and vector index readiness |
| **System Architecture** | 📐 [ARCHITECTURE.md](ARCHITECTURE.md) | High-level data flow, component diagrams, and RAG pipeline |
| **Automated Test Report** | 🧪 [TEST_REPORT.md](TEST_REPORT.md) | 38/38 automated tests (unit, integration, security) |
| **Official Submission Brief** | 📄 [SUBMISSION.md](SUBMISSION.md) | Formal candidate submission response |

> ℹ️ **Note on Free-Tier Cloud Hosting:** The application is hosted on Render's free tier. If the instance has been idle, the first request may take ~30–60 seconds to spin up from sleep mode, after which it responds with normal low latency.

---

### 💡 Suggested Queries to Test on the Live App:
* *"What luxury developments does DarGlobal offer in Dubai?"*
* *"Compare W Residences Dubai Downtown with DaVinci Tower in terms of price, bedrooms, and amenities."*
* *"Show me villas available in Riyadh on Wasalt under SAR 3,000,000."*
* *"What branded amenities are included in Tierra Viva by Automobili Lamborghini?"*
* *"ما هي الفلل المتاحة في الرياض؟"* (Arabic queries supported)

---

## 1. Executive Overview

**EstateIntel AI** is a production-grade conversational real estate assistant built on a Retrieval-Augmented Generation (RAG) architecture. It aggregates, cleans, normalizes, and indexes public real estate intelligence from:
1. **DarGlobal PLC (`darglobal.co.uk`):** Flagship ultra-luxury master developments and co-branded residences (Aston Martin, Lamborghini, The Trump Organization, Pagani, Missoni, Mouawad).
2. **Wasalt Proptech (`wasalt.sa`):** REGA-licensed property marketplace listings across Saudi Arabia (Riyadh, Jeddah, Dammam, Al-Khobar).

The system integrates verified zero-cost free models on the **OpenRouter API** (`openrouter/free`, `google/gemma-4-31b-it:free`), enforces strict data grounding, provides source citations with clickable verified URLs, incorporates defensive security layers (SSRF allowlisting, prompt-injection defense), and packages the solution into a single-container Docker architecture suitable for cloud deployment.

---

## 2. Technical Assignment Compliance

| Requirement | Description | Implementation Status |
| :-: | :--- | :-: |
| **1** | **Scrape publicly available data from DarGlobal & Wasalt** | ✅ **VERIFIED** — 37 verified properties collected, cleaned, and normalized. |
| **2** | **Build an AI chatbot using collected data** | ✅ **VERIFIED** — Grounded RAG with 384-dim dense embeddings and hybrid metadata filtering. |
| **3** | **Use suitable free model on OpenRouter** | ✅ **VERIFIED** — Configured with `openrouter/free` and automated free fallback cascade. |
| **4** | **Containerise the application using Docker** | ✅ **VERIFIED** — Multi-stage `Dockerfile`, non-root user, `docker-compose.yml`. |
| **5** | **Deploy the solution rather than source code only** | ✅ **VERIFIED** — Cloud-deployed on Render at [https://estateintel-ai.onrender.com](https://estateintel-ai.onrender.com). |
| **6** | **Provide working URL for direct testing** | ✅ **VERIFIED** — Live working UI at [https://estateintel-ai.onrender.com](https://estateintel-ai.onrender.com). |

---

## 3. Architecture

```mermaid
flowchart TD
    subgraph Ingestion["Ingestion & Scraping Pipeline"]
        DG["DarGlobal PLC\n(Official Disclosures)"] --> DGC["DarGlobal Scraper\n(WAF Probe Safeguards)"]
        WST["Wasalt Proptech\n(wasalt.sa)"] --> WSTC["Wasalt Scraper\n(Sitemap & Next.js Parser)"]
        DGC --> NORM["Schema Normalizer"]
        WSTC --> NORM
        NORM --> DEDUP["Deduplication Engine (SHA-256)"]
        DEDUP --> JSON_STORE["Processed JSON Data"]
        DEDUP --> VEC_STORE["Vector Database (ChromaDB / 384-dim)"]
    end

    subgraph RAG["Retrieval-Augmented Generation"]
        USER_QUERY["User Natural Language Query"] --> SEC["Input Sanitization & Injection Defense"]
        SEC --> HYBRID["Hybrid Retriever"]
        HYBRID <--> VEC_STORE
        HYBRID <--> JSON_STORE
        HYBRID --> CTX["Grounded Context & Citations Assembly"]
    end

    subgraph LLM["OpenRouter Inference"]
        CTX --> OR_CLIENT["OpenRouter API Client"]
        OR_CLIENT --> FREE_ROUTER["Free Model Cascade (openrouter/free)"]
        FREE_ROUTER --> GROUNDED_RESP["Grounded Assistant Response"]
    end

    subgraph Delivery["Delivery Interfaces"]
        GROUNDED_RESP --> STREAMLIT["Streamlit Web Application"]
        GROUNDED_RESP --> FASTAPI["FastAPI REST API (/api/chat)"]
    end
```

---

## 4. Key Features

- **Hybrid Semantic & Deterministic Retrieval:** Combines 384-dimensional dense semantic similarity with deterministic numeric filtering (price limits, bedroom counts, city filters).
- **Zero Hallucination Guardrails:** Strict prompt instructions enforce refusal on unverified information:
  > *"I couldn't verify that information from the available DarGlobal or Wasalt sources."*
- **Comprehensive Source Citations:** Every response includes verifiable references with property titles, locations, prices, and direct URLs.
- **Multilingual Support:** Seamlessly answers inquiries in English and Arabic.
- **Enterprise Security:**
  - Strict URL allowlisting and SSRF defense (blocking private/loopback IP spaces).
  - Defensive regex and prompt isolation neutralizing prompt-injection attacks.
  - Secret masking preventing credential leakage in logs and API responses.
- **Dual Interface:**
  - Executive Streamlit Chat UI with real-time stats and suggested query chips.
  - Interactive FastAPI OpenAPI Documentation (`/docs`).

---

## 5. Technology Stack

- **Backend:** Python 3.11, FastAPI, Pydantic v2, Uvicorn
- **Frontend:** Streamlit, Responsive Custom CSS, SVG Badges
- **Web Scraping:** HTTPX, Requests, BeautifulSoup4, Next.js Hydration Parser
- **RAG & Vector Database:** ChromaDB, `all-MiniLM-L6-v2` dense embeddings
- **AI Engine:** OpenRouter API (`openrouter/free`, `google/gemma-4-31b-it:free`)
- **DevOps:** Docker, Docker Compose, Linux non-root containerization
- **Testing:** Pytest (38 automated unit, integration, and security tests)

---

## 6. Project Structure

```
estateintel-ai/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entrypoint
│   ├── config.py                   # Pydantic environment configuration
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py               # REST endpoints (/health, /api/chat, etc.)
│   │   └── schemas.py              # Pydantic models (PropertyItem, ChatRequest)
│   ├── scraping/
│   │   ├── __init__.py
│   │   ├── darglobal.py            # DarGlobal extractor & WAF safeguard probe
│   │   ├── wasalt.py               # Wasalt sitemap & Next.js state scraper
│   │   ├── crawler.py              # Ingestion coordinator & deduplication
│   │   └── parser.py               # Text cleaning, hashing, and normalization
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embeddings.py           # 384-dim dense embeddings service
│   │   ├── vector_store.py         # ChromaDB & persistent vector index
│   │   ├── retriever.py            # Hybrid semantic + metadata retriever
│   │   ├── prompts.py              # Grounded system prompts & templates
│   │   └── pipeline.py             # End-to-end RAG workflow
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openrouter.py           # OpenRouter free model API client
│   │   └── property_service.py     # Deterministic query & filter service
│   └── utils/
│       ├── __init__.py
│       ├── logging.py              # Structured logging
│       └── validators.py           # SSRF, URL allowlist & prompt defenses
├── frontend/
│   ├── streamlit_app.py            # Polished Streamlit chat application
│   └── styles.css                  # Executive styling & citation cards
├── scripts/
│   ├── ingest.py                   # CLI data scraping and indexing script
│   ├── entrypoint.py               # Unified container process orchestrator
│   ├── verify_deployment.py        # Automated deployment verification script
│   └── check_models.py             # OpenRouter free model verification utility
├── data/
│   ├── raw/                        # Raw scraped JSON files
│   ├── processed/                  # Normalized properties & ingestion stats
│   └── chroma_db/                  # Persistent vector storage
├── tests/
│   ├── test_scraping.py            # Scraper & parsing test suite
│   ├── test_retrieval.py           # Vector index & hybrid search tests
│   ├── test_api.py                 # FastAPI endpoint test suite
│   ├── test_security.py            # Security & prompt injection tests
│   └── test_chat.py                # 15 realistic conversational evaluations
├── Dockerfile                      # Production Docker container
├── docker-compose.yml              # Local multi-service orchestration
├── .dockerignore                   # Docker build exclusions
├── requirements.txt                # Pinned production dependencies
├── .env.example                    # Environment variable template
├── README.md                       # Comprehensive project documentation
├── ARCHITECTURE.md                 # System architecture specification
├── DEPLOYMENT.md                   # Cloud & local deployment manual
├── TEST_REPORT.md                  # Automated test results & logs
└── SUBMISSION.md                   # Official assignment submission summary
```

---

## 7. Data Ingestion & Safeguards

### Ingestion Statistics (Verified Live):
- **Pages Attempted:** 27
- **Pages Succeeded:** 39
- **Pages Blocked / Safeguarded:** 3 (DarGlobal Imperva WAF properly detected)
- **DarGlobal Developments Ingested:** 16 verified flagship projects
- **Wasalt Listings Ingested:** 23 verified properties
- **Duplicates Filtered:** 2
- **Total Properties Indexed:** 37
- **Vector Embeddings Generated:** 37 (384-dimensional dense vectors)

To run live data collection independently:
```bash
python scripts/ingest.py 30
```

---

## 8. Quick Start (Local Setup)

### Prerequisites
- Python 3.11+
- Git

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/mramir3/estateintel-ai.git
cd estateintel-ai

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and provide your OpenRouter API key:
```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=openrouter/free
```

### 3. Run Data Ingestion
```bash
python scripts/ingest.py
```

### 4. Start the Application
You can run the FastAPI backend, Streamlit frontend, or both simultaneously:

```bash
# Option A: Start unified runner (both FastAPI on 8000 & Streamlit on 8501)
python scripts/entrypoint.py

# Option B: Run FastAPI standalone
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Option C: Run Streamlit standalone
streamlit run frontend/streamlit_app.py
```

- Open Streamlit Chat: `http://localhost:8501`
- Open FastAPI Swagger Docs: `http://localhost:8000/docs`

---

## 9. Docker Deployment

### Run with Docker Compose
```bash
docker-compose up --build -d
```

### Run with Docker CLI
```bash
# Build image
docker build -t estateintel-ai:latest .

# Run container
docker run -d -p 8000:8000 -p 8501:8501 \
  -e OPENROUTER_API_KEY="sk-or-v1-..." \
  -e OPENROUTER_MODEL="openrouter/free" \
  estateintel-ai:latest
```

---

## 10. Automated Tests & Quality Assurance

Run the complete 38-test automated test suite:
```bash
python -m pytest -v
```

**Results:** `38 passed in 6.58s (100% pass rate)`.  
See [TEST_REPORT.md](TEST_REPORT.md) for full scenario breakdown and evidence.

---

## 11. API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Root application metadata & status |
| `GET` | `/health` | System health and vector store readiness |
| `GET` | `/api/stats` | Verified data ingestion & indexing metrics |
| `GET` | `/api/sources` | Overview of DarGlobal and Wasalt portfolios |
| `GET` | `/api/properties` | Deterministic property filtering (by city, price, beds, type) |
| `POST` | `/api/chat` | Conversational RAG endpoint with source citations |

Interactive documentation is available at `/docs` (Swagger UI) and `/redoc`.

---



## 12. License & Attribution

Developed originally for the DarGlobal Junior AI Engineer – Applied AI technical evaluation.  
All brand trademarks (DarGlobal, Wasalt, Aston Martin, Automobili Lamborghini, The Trump Organization, Pagani, Missoni, Mouawad) belong to their respective copyright holders.
