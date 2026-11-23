import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    # Either HTML SPA or JSON is valid
    assert "PromptWars" in response.text


def test_healthz_endpoint():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "gemini_configured" in data

def test_generate_endpoint_demo_or_live():
    payload = {
        "prompt": "Hello hackathon!",
        "temperature": 0.5
    }
    response = client.post("/api/v1/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "model" in data

def test_structured_endpoint():
    payload = {
        "prompt": "Extract person: Alice is 25 years old",
        "instruction": "Return JSON with name and age",
        "json_schema": {"name": "string", "age": "number"}
    }
    response = client.post("/api/v1/structured", json=payload)
    assert response.status_code == 200
    assert "data" in response.json() or "raw" in response.json()
