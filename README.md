# ⚡ PromptWars x Cynergy AI Backend Starter

> **Hackathon-Ready, Deploy-in-60-Seconds AI Backend Template**  
> Built for rapid vibe-coding, prompt engineering, and GenAI prototyping for **PromptWars x Cynergy** (Hack2skill).

[![CI & Deployment Check](https://github.com/placeholder/promptwars-ai-backend/actions/workflows/ci.yml/badge.svg)](https://github.com)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Google%20GenAI-Gemini%202.5%20%2F%201.5-4285F4.svg?logo=google)](https://aistudio.google.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Why This Repo for PromptWars?

1. **Instant 1-Click Cloud Deployments**: Pre-configured for **Render**, **Railway**, **Vercel**, **Docker**, and **GCP Cloud Run**.
2. **Pre-wired Google Gemini Integration**: Ready-to-use endpoints for Gemini 2.5 Flash, Gemini 1.5 Pro, multi-modal vision, real-time SSE streaming, and structured JSON output.
3. **Zero CORS Friction**: Pre-configured with universal CORS so your frontend (React, Next.js, Vue, Streamlit, HTML/JS) connects instantly with no browser errors.
4. **Built-in Interactive API Docs**: Live Swagger UI at `/docs` and ReDoc at `/redoc` for live evaluation and hackathon judging.
5. **Zero-Key Demo Mode**: Fully functional mock/echo fallback mode so your endpoints work even before entering an API key.

---

## 🚀 Instant Deployment Options (Ready-to-Deploy)

### Option 1: Render (Recommended for Hackathons)
1. Push this repository to your GitHub account.
2. Go to [Render Dashboard](https://dashboard.render.com/) -> **New** -> **Blueprint**.
3. Select this repo. Render will automatically detect `render.yaml` and configure everything.
4. Add your `GEMINI_API_KEY` under Environment Variables.

### Option 2: Railway
1. Push this repository to your GitHub.
2. Go to [Railway.app](https://railway.app/) -> **New Project** -> **Deploy from GitHub repo**.
3. Railway automatically uses `railway.json` and the `Dockerfile`.
4. Add `GEMINI_API_KEY` in the project settings.

### Option 3: Vercel (Serverless)
1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel` in this folder, or import the GitHub repo on the [Vercel Dashboard](https://vercel.com).
3. The repo includes `vercel.json` and `api/index.py` configured for serverless Python execution.

### Option 4: Docker / Cloud Run
```bash
# Build the container
docker build -t promptwars-backend .

# Run locally
docker run -p 8000:8000 -e GEMINI_API_KEY="your_api_key" promptwars-backend
```

---

## 🛠️ Project Structure

```
promptwars-ai-backend/
├── .github/workflows/ci.yml # Automated CI & build verification
├── api/
│   └── index.py            # Vercel serverless entrypoint
├── app/
│   ├── config.py           # Environment and app configuration
│   ├── main.py             # FastAPI entrypoint & CORS setup
│   ├── routers/
│   │   ├── health.py       # Health checks (/healthz, /)
│   │   └── ai.py           # AI generation, streaming, vision, structured JSON
│   ├── schemas/
│   │   └── models.py       # Pydantic request & response schemas
│   └── services/
│       └── gemini.py       # Google GenAI / Gemini client wrapper
├── tests/
│   └── test_api.py         # Pytest test suite
├── Dockerfile              # Production Dockerfile with dynamic $PORT support
├── Procfile                # Heroku / Railway / Render web process command
├── railway.json            # Railway deployment config
├── render.yaml             # Render Blueprint specification
├── vercel.json             # Vercel serverless deployment config
├── requirements.txt        # Python package dependencies
├── dev.sh                  # One-command local development setup
└── .env.example            # Sample environment variables
```

---

## ⚡ Quickstart (Local Development)

### 1. Clone & Setup
```bash
# Clone your repository
git clone https://github.com/<your-username>/promptwars-ai-backend.git
cd promptwars-ai-backend

# Run the automated dev script
./dev.sh
```

Or manually:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure Your API Key
Get your Gemini API Key for free from [Google AI Studio](https://aistudio.google.com/):
Edit `.env`:
```env
GEMINI_API_KEY=AIzaSy...
DEFAULT_GEMINI_MODEL=gemini-2.5-flash
PORT=8000
```

### 3. Run the Server
```bash
uvicorn app.main:app --reload --port 8000
```
- Interactive API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/healthz](http://localhost:8000/healthz)

---

## 📡 API Endpoints & Cheat Sheet

### 1. Health Check
```bash
curl http://localhost:8000/healthz
```

### 2. AI Content Generation
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a 3-step action plan for winning an AI hackathon.",
    "system_instruction": "You are an elite hackathon mentor.",
    "temperature": 0.7
  }'
```

### 3. Real-time Streaming (SSE)
```bash
curl -N -X POST http://localhost:8000/api/v1/stream \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a punchy elevator pitch for an AI product."
  }'
```

### 4. Structured JSON Output
```bash
curl -X POST http://localhost:8000/api/v1/structured \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Cynergy PromptWars Hackathon on Nov 2026, prize pool 1000 USD",
    "instruction": "Extract event details as JSON with event_name, date, prize_pool"
  }'
```

### 5. Multimodal Vision Analysis
```bash
curl -X POST http://localhost:8000/api/v1/vision \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Describe what is in this image",
    "image_base64": "<base64_string_here>",
    "mime_type": "image/jpeg"
  }'
```

---

## 🔗 How to Push to Your GitHub

1. Create a new repository on [GitHub](https://github.com/new) (e.g. `promptwars-ai-backend`).
2. Run in this directory:
```bash
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/promptwars-ai-backend.git
git branch -M main
git push -u origin main
```
3. Connect your GitHub repo to **Render**, **Railway**, or **Vercel** for automatic instant deployment!
