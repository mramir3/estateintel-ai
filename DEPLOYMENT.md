# EstateIntel AI — Deployment & Operations Guide

This guide provides end-to-end instructions for deploying EstateIntel AI to cloud hosting platforms (**Render**, **Railway**, **Hugging Face Spaces**) and running locally with **Docker** & **Docker Compose**.

---

## 1. Cloud Deployment Architectures

EstateIntel AI supports a unified single-container deployment architecture designed specifically for cloud PaaS providers:

* **Entrypoint:** `scripts/entrypoint.py`
* **FastAPI Backend:** Runs internally on `0.0.0.0:8000` (provides `/health`, `/docs`, `/api/chat`, `/api/properties`, `/api/stats`).
* **Streamlit Frontend:** Automatically binds to the public port assigned by the hosting environment (`$PORT`, defaulting to `8501`).
* **Persistent Vector Store:** Maintains pre-computed vector embeddings in `data/chroma_db/`, eliminating initialization latency on cold starts.

---

## 2. Deploying to Render (Recommended)

Render provides Docker-based web services with automatic HTTPS and free-tier compatibility.

### Step 1: Push Repository to GitHub
```bash
git init
git add .
git commit -m "feat: complete EstateIntel AI production release"
git remote add origin https://github.com/your-username/estateintel-ai.git
git push -u origin main
```

### Step 2: Create Web Service on Render
1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository (`estateintel-ai`).
4. Select **Docker** as the Runtime environment.
5. In **Environment Variables**, configure:
   * `OPENROUTER_API_KEY`: Your OpenRouter API key (`sk-or-v1-...`).
   * `OPENROUTER_MODEL`: `openrouter/free` (or `google/gemma-4-31b-it:free`).
   * `ENVIRONMENT`: `production`
6. Click **Create Web Service**.

### Free-Tier Behavior & Cold Starts
* **Sleep Mode:** Render free instances spin down after 15 minutes of inactivity. The first inbound request may take 30–45 seconds to spin up.
* **Healthcheck:** The container includes a built-in health check targeting `/health`.

---

## 3. Deploying to Railway

1. Install Railway CLI or connect via [Railway Dashboard](https://railway.app/).
2. Select **New Project** → **Deploy from GitHub repo**.
3. Add Environment Variables:
   * `OPENROUTER_API_KEY`: `sk-or-v1-...`
   * `OPENROUTER_MODEL`: `openrouter/free`
   * `PORT`: Railway automatically injects `$PORT`.
4. Railway builds the `Dockerfile` and publishes a live HTTPS URL.

---

## 4. Deploying to Hugging Face Spaces (Docker)

1. Create a new Space at [huggingface.co/spaces](https://huggingface.co/spaces) with SDK set to **Docker**.
2. Add your `OPENROUTER_API_KEY` under **Settings** → **Variables and secrets**.
3. Push the repository to the Space. Hugging Face Spaces exposes port `7860`:
   Set `PORT=7860` in the Space environment variables.

---

## 5. Local Docker Deployment

### Using Docker Compose
```bash
# 1. Clone repository and create .env file
cp .env.example .env
# Edit .env and insert your OPENROUTER_API_KEY

# 2. Build and start containers
docker-compose up --build -d

# 3. Check health and logs
docker-compose logs -f
```

### Using Plain Docker CLI
```bash
# Build Docker image
docker build -t estateintel-ai:latest .

# Run container
docker run -d \
  --name estateintel-ai \
  -p 8000:8000 \
  -p 8501:8501 \
  -e OPENROUTER_API_KEY="sk-or-v1-..." \
  -e OPENROUTER_MODEL="openrouter/free" \
  estateintel-ai:latest
```

* Access Streamlit Interface: `http://localhost:8501`
* Access FastAPI Swagger Docs: `http://localhost:8000/docs`
* Access Health Check: `http://localhost:8000/health`

---

## 6. Post-Deployment Verification

Verify any local or public deployment using the automated smoke-test script:

```bash
# Test local deployment
python scripts/verify_deployment.py http://localhost:8000

# Test public deployment
python scripts/verify_deployment.py https://estateintel-ai.onrender.com
```
