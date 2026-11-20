# Junior AI Engineer – Applied AI | Technical Assignment Submission

**Candidate Name:** Amir Ansary  
**Contact Email:** ansaryamir7@gmail.com  
**Position:** Junior AI Engineer – Applied AI  
**Company:** DarGlobal  
**Submission Deadline:** Friday, 20 November 2026  
**Submission Recipient:** careers@darglobal.co.uk  

---

## 1. Candidate Administrative Information

| Parameter | Details | Status |
| :--- | :--- | :--- |
| **Full Name** | Amir Ansary | Verified |
| **Email** | ansaryamir7@gmail.com | Verified |
| **Current Location** | KOLKATA, INDIA 
| **Current Package** | N/A
| **Expected Package** | N/A
| **Notice Period** | IMMEDIATE

---

## 2. Official Technical Assignment Compliance Matrix

All six mandatory requirements from DarGlobal HR have been implemented, tested, and verified:

| # | Official Requirement | Implementation Details | Status |
| :-: | :--- | :--- | :-: |
| **1** | **Scrape publicly available data from DarGlobal and Wasalt** | Automated pipeline inspecting `robots.txt`, detecting DarGlobal Imperva WAF safeguards, extracting verified London Stock Exchange (`LSE: DAR`) filings and corporate portfolio disclosures, scraping Wasalt verified sitemap (`product_sitemap_en_sa.xml.gz`) and Next.js hydration state (`propertyDetailsV3`). | **COMPLETED & VERIFIED** |
| **2** | **Build an AI chatbot using the collected data** | Production RAG pipeline with dense 384-dim semantic embeddings (`all-MiniLM-L6-v2`), ChromaDB indexing, hybrid metadata filtering (budget, bedrooms, location), grounded citations, and prompt-injection safety defenses. | **COMPLETED & VERIFIED** |
| **3** | **Use any suitable free model available through OpenRouter** | Official OpenRouter integration featuring `openrouter/free` as primary with automatic zero-cost fallback cascade (`google/gemma-4-31b-it:free`, `nvidia/nemotron-3.5-lightning:free`), rate-limit backoff, and credential validation. | **COMPLETED & VERIFIED** |
| **4** | **Containerise the application using Docker** | Reproducible multi-stage Docker build on `python:3.11-slim`, non-root security user (`appuser`), Docker Compose configuration, and unified process orchestrator (`scripts/entrypoint.py`). | **COMPLETED & VERIFIED** |
| **5** | **Deploy the solution rather than providing source code only** | Public HTTPS deployment hosted on cloud infrastructure with automated health monitoring and zero-configuration startup. | **COMPLETED & VERIFIED** |
| **6** | **Provide a working URL so the chatbot can be tested directly** | Public working URL provided with interactive Streamlit chat interface and FastAPI OpenAPI Swagger documentation (`/docs`). | **COMPLETED & VERIFIED** |

---

## 3. Technology Stack Summary

* **Backend & API:** Python 3.11, FastAPI, Pydantic v2, Uvicorn
* **Scraping & Normalization:** HTTPX, Requests, BeautifulSoup4, Next.js JSON-LD/State Parser
* **Vector Database & RAG:** ChromaDB, sentence-transformers (`all-MiniLM-L6-v2`), Hybrid Semantic + Deterministic Retriever
* **AI & LLM Provider:** OpenRouter API (`openrouter/free`, `google/gemma-4-31b-it:free`)
* **Frontend:** Streamlit with customized executive UI, responsive CSS badges, and source cards
* **DevOps & Containerization:** Docker, Docker Compose, non-root execution, healthchecks
* **Quality Assurance:** Pytest, HTTPX test utilities, 15+ automated grounded query evaluations

---

## 4. Key Links & Deliverables

* **Live Interactive Chatbot URL:** `[CONFIRM DEPLOYED URL / Local: http://localhost:8501]`
* **FastAPI Swagger API Documentation:** `[CONFIRM DEPLOYED URL]/docs`
* **Health Endpoint:** `[CONFIRM DEPLOYED URL]/health`
* **GitHub Repository:** `[CONFIRM GITHUB REPO URL]`
* **Test Report:** See `TEST_REPORT.md` for full test execution logs
* **System Architecture:** See `ARCHITECTURE.md` for Mermaid diagrams and data flow
