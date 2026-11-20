"""Tests for FastAPI endpoints and input schemas."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "EstateIntel AI"
    assert data["status"] == "online"
    assert "endpoints" in data

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_api_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "openrouter_configured" in data
    assert "vector_store_ready" in data

def test_api_stats_endpoint():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "records_darglobal" in data
    assert "records_wasalt" in data
    assert "total_documents_indexed" in data

def test_api_sources_endpoint():
    response = client.get("/api/sources")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert "DarGlobal" in data["sources"]
    assert "Wasalt" in data["sources"]

def test_api_properties_filter():
    response = client.get("/api/properties?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_api_chat_empty_message():
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"

def test_api_chat_validation_too_long():
    long_msg = "A" * 2000
    response = client.post("/api/chat", json={"message": long_msg})
    # Pydantic validation error for max_length 1500
    assert response.status_code == 422
