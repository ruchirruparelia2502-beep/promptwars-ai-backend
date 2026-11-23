#!/usr/bin/env bash
set -e

echo "🚀 Starting PromptWars AI Backend in development mode..."

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo "✨ Server starting at http://localhost:8000 (Docs: http://localhost:8000/docs)"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
